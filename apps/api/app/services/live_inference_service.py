"""
apps/api/app/services/live_inference_service.py
Flowshield — Live Model Inference & Decision Orchestration Service (v2.5)
Connects real-world telemetry and topographical parameters to the frozen V2
ML inference pipeline, persisting predictions, risk snapshots, and alert triggers.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models.village import Village
from ..models.observation import EnvironmentalObservation
from ..models.prediction import Prediction
from ..models.risk_snapshot import RiskSnapshot
from .prediction_service import prediction_service
from .risk_engine import risk_engine
from .alert_engine import alert_engine
from ml.registry.region_resolver import region_resolver

logger = logging.getLogger("flowshield.live_inference")


class LiveInferenceService:
    """
    Coordinates live data gathering, canonical 15-feature extraction,
    calibrated inference, database persistence, and alert generation.
    """

    @staticmethod
    def extract_feature_vector(village: Village, obs: Optional[EnvironmentalObservation]) -> Dict[str, Any]:
        """
        Builds the canonical 15-feature dictionary from village static terrain
        and latest environmental telemetry.
        """
        dist_m = village.distance_to_river * 1000.0 if village.distance_to_river <= 20.0 else village.distance_to_river

        # In-situ / station observations
        r1 = float(obs.rainfall_1h) if obs and obs.rainfall_1h is not None else 0.0
        r3 = float(obs.rainfall_3h) if obs and obs.rainfall_3h is not None else 0.0
        r6 = float(obs.rainfall_6h) if obs and obs.rainfall_6h is not None else 0.0
        r24 = float(obs.rainfall_24h) if obs and obs.rainfall_24h is not None else 0.0
        r72 = float(getattr(obs, "rainfall_72h", None) or (r24 * 1.5)) if obs else 0.0

        soil = float(obs.soil_moisture) if obs and obs.soil_moisture is not None else 40.0
        deep_soil = float(getattr(obs, "deep_soil_moisture", None) or soil) if obs else 40.0

        temp = float(getattr(obs, "temperature", None) or 22.0) if obs else 22.0
        humidity = float(getattr(obs, "humidity", None) or 65.0) if obs else 65.0
        pressure = float(getattr(obs, "surface_pressure", None) or 920.0) if obs else 920.0
        wind = float(getattr(obs, "wind_speed", None) or 8.0) if obs else 8.0

        return {
            "rainfall_1h_mm": r1,
            "rainfall_3h_mm": r3,
            "rainfall_6h_mm": r6,
            "rainfall_24h_mm": r24,
            "rainfall_72h_mm": r72,
            "soil_saturation_pct": soil,
            "deep_soil_saturation_pct": deep_soil,
            "temperature_c": temp,
            "relative_humidity_pct": humidity,
            "surface_pressure_hpa": pressure,
            "wind_speed_kmh": wind,
            "elevation_m": float(village.elevation),
            "catchment_slope_deg": float(village.slope),
            "dist_to_river_m": float(dist_m),
            "upstream_drainage_sqkm": float(getattr(village, "upstream_drainage_sqkm", 3200.0)),
            "vulnerability_index": float(village.vulnerability_index),
        }

    def evaluate_village(
        self,
        db: Session,
        village_id: str,
        persist: bool = True,
    ) -> Dict[str, Any]:
        """
        Runs on-demand real-time prediction for a specific village using its latest
        hydrometeorological telemetry and topographical parameters.
        """
        village = db.query(Village).filter(Village.id == village_id).first()
        if not village:
            raise ValueError(f"Village '{village_id}' not found.")

        latest_obs = (
            db.query(EnvironmentalObservation)
            .filter(EnvironmentalObservation.village_id == village.id)
            .order_by(EnvironmentalObservation.timestamp.desc())
            .first()
        )

        data_quality_score = float(latest_obs.data_quality_score) if latest_obs and latest_obs.data_quality_score is not None else 1.0
        freshness_seconds = int(latest_obs.freshness_seconds) if latest_obs and latest_obs.freshness_seconds is not None else 0

        features = self.extract_feature_vector(village, latest_obs)
        region_slug = region_resolver.resolve_from_state(getattr(village, "state", "")) or "himachal_pradesh"
        features["region"] = region_slug
        pred_res = prediction_service.predict_full(
            feature_dict=features,
            data_quality_score=data_quality_score,
            freshness_seconds=freshness_seconds,
            region=region_slug,
        )

        now = datetime.now(timezone.utc)
        pred_id = str(uuid.uuid4())

        # Trend estimation from past snapshots
        past_snaps = (
            db.query(RiskSnapshot)
            .filter(RiskSnapshot.village_id == village.id)
            .order_by(RiskSnapshot.timestamp.desc())
            .limit(3)
            .all()
        )
        past_scores = [s.risk_score for s in reversed(past_snaps)] if past_snaps else []
        trend_factor, trend_str = risk_engine.calculate_trend_factor(past_scores)

        risk_score, risk_lvl, color_hex, is_capped = risk_engine.compute_operational_risk(
            flood_probability=pred_res["calibrated_probability"],
            trend_factor=trend_factor,
            vulnerability_index=village.vulnerability_index,
            data_quality_score=data_quality_score,
            freshness_seconds=freshness_seconds,
        )

        if persist:
            try:
                db_pred = Prediction(
                    id=pred_id,
                    village_id=village.id,
                    observation_id=latest_obs.id if latest_obs else None,
                    flood_probability=pred_res["flood_probability"],
                    calibrated_probability=pred_res["calibrated_probability"],
                    decision_threshold=pred_res["decision_threshold"],
                    threshold_exceeded=pred_res["threshold_exceeded"],
                    model_integrity_status=pred_res["model_integrity_status"],
                    prediction_quality=pred_res["prediction_quality"],
                    model_version=pred_res["model_version"],
                    feature_contributions=pred_res["top_contributing_factors"],
                    created_at=now,
                )
                db.add(db_pred)
                db.flush()

                snapshot = RiskSnapshot(
                    village_id=village.id,
                    prediction_id=db_pred.id,
                    risk_score=risk_score,
                    risk_level=risk_lvl,
                    trend=trend_str,
                    timestamp=now,
                )
                db.add(snapshot)
                db.flush()

                alert_engine.evaluate_and_create_alert(
                    db=db,
                    village=village,
                    risk_score=risk_score,
                    risk_level=risk_lvl,
                    prediction_id=db_pred.id,
                    top_contributors=pred_res["top_contributing_factors"],
                )
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to persist prediction/snapshot for {village.name}: {e}")

        return {
            "prediction_id": pred_id,
            "village_id": village.id,
            "village_name": village.name,
            "flood_probability": pred_res["flood_probability"],
            "calibrated_probability": pred_res["calibrated_probability"],
            "raw_probability": pred_res.get("raw_probability", pred_res["calibrated_probability"]),
            "decision_threshold": pred_res["decision_threshold"],
            "threshold_exceeded": pred_res["threshold_exceeded"],
            "prediction_quality": pred_res["prediction_quality"],
            "model_version": pred_res["model_version"],
            "model_integrity_status": pred_res["model_integrity_status"],
            "risk_score": risk_score,
            "operational_risk_score": risk_score,
            "risk_level": risk_lvl,
            "operational_risk_level": risk_lvl,
            "trend": trend_str,
            "color_hex": color_hex,
            "is_capped_by_quality": is_capped,
            "top_contributing_factors": pred_res["top_contributing_factors"],
            "physical_explanations": pred_res.get("physical_explanations", []),
            "canonical_features": features,
            "timestamp": now.isoformat(),
        }

    def evaluate_all_villages(self, db: Session, persist: bool = True) -> Dict[str, Any]:
        """
        Executes real-time inference across all monitored settlements in the basin.
        """
        villages = db.query(Village).order_by(Village.name).all()
        results = []
        severity_counts = {"LOW": 0, "WATCH": 0, "HIGH": 0, "CRITICAL": 0, "INSUFFICIENT_DATA": 0}
        total_calibrated_prob = 0.0

        for v in villages:
            res = self.evaluate_village(db, v.id, persist=persist)
            results.append(res)
            lvl = res["risk_level"]
            severity_counts[lvl] = severity_counts.get(lvl, 0) + 1
            total_calibrated_prob += res["calibrated_probability"]

        n = len(results) if results else 1
        return {
            "total_evaluated": len(results),
            "severity_breakdown": severity_counts,
            "average_calibrated_probability": round(total_calibrated_prob / n, 4),
            "decision_threshold": 0.08,
            "high_risk_settlements": [r["village_name"] for r in results if r["risk_level"] in ["HIGH", "CRITICAL"]],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": results,
        }


live_inference_service = LiveInferenceService()
