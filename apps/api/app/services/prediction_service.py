"""
apps/api/app/services/prediction_service.py
Flowshield — Unified V2 ML Prediction & Risk Service (v2.4)
Wraps ModelIntegrityChecker and ml.inference.predict:predict_flood_risk.
Replaces legacy 12-feature XGBoost with canonical 15-feature Calibrated V2 Pipeline.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("flowshield.prediction_service")

# Ensure repository root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from ml.inference.predict import predict_flood_risk, get_explainer
from .model_integrity import model_integrity_checker, ModelIntegrityState
from .risk_engine import risk_engine


class PredictionService:
    """
    Production ML prediction service utilizing the frozen Flowshield V2 pipeline
    (Calibrated Logistic Regression with Isotonic scaling, tau=0.08, 15 features).
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PredictionService, cls).__new__(cls)
            cls._instance._is_loaded = False
            cls._instance.metadata = {
                "model_version": "flowshield-flood-risk-v2",
                "model_type": "Calibrated Logistic Regression (Isotonic scaling on ERA5-Land)",
                "pipeline_version": "v2.5",
                "features_count": 15,
                "decision_threshold": 0.08,
            }
        return cls._instance

    def __init__(self):
        if not self._is_loaded:
            self.load_artifacts()

    def load_artifacts(self) -> bool:
        """Verifies model integrity against frozen hashes and prepares inference."""
        state, details = model_integrity_checker.verify_integrity(enforce_checksums=True)
        if state == ModelIntegrityState.MODEL_READY:
            self._is_loaded = True
            logger.info("PredictionService: Flowshield V2 pipeline loaded and verified.")
            return True
        else:
            logger.error(f"PredictionService: Model integrity verification failed with state {state}: {details.get('errors')}")
            self._is_loaded = False
            return False

    @property
    def is_ready(self) -> bool:
        return self._is_loaded and model_integrity_checker.state == ModelIntegrityState.MODEL_READY

    @staticmethod
    def normalize_feature_vector(feature_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps inputs (including legacy parameter aliases) to canonical 15 features.
        Zero arbitrary heuristic multipliers: genuinely missing features remain None/NaN
        for legitimate training-median imputation by SimpleImputer in the pipeline.
        """
        norm = {}

        # 1. rainfall_1h_mm
        r1 = feature_dict.get("rainfall_1h_mm", feature_dict.get("rainfall_1h", feature_dict.get("rainfall_intensity")))
        norm["rainfall_1h_mm"] = float(r1) if r1 is not None else None

        # 2. rainfall_3h_mm
        r3 = feature_dict.get("rainfall_3h_mm", feature_dict.get("rainfall_3h"))
        norm["rainfall_3h_mm"] = float(r3) if r3 is not None else None

        # 3. rainfall_6h_mm
        r6 = feature_dict.get("rainfall_6h_mm", feature_dict.get("rainfall_6h"))
        norm["rainfall_6h_mm"] = float(r6) if r6 is not None else None

        # 4. rainfall_24h_mm
        r24 = feature_dict.get("rainfall_24h_mm", feature_dict.get("rainfall_24h"))
        norm["rainfall_24h_mm"] = float(r24) if r24 is not None else None

        # 5. rainfall_72h_mm
        r72 = feature_dict.get("rainfall_72h_mm", feature_dict.get("rainfall_72h"))
        norm["rainfall_72h_mm"] = float(r72) if r72 is not None else None

        # 6. soil_saturation_pct
        soil = feature_dict.get("soil_saturation_pct", feature_dict.get("soil_moisture"))
        norm["soil_saturation_pct"] = float(soil) if soil is not None else None

        # 7. deep_soil_saturation_pct
        deep_soil = feature_dict.get("deep_soil_saturation_pct", feature_dict.get("deep_soil_moisture"))
        norm["deep_soil_saturation_pct"] = float(deep_soil) if deep_soil is not None else None

        # 8. temperature_c
        temp = feature_dict.get("temperature_c", feature_dict.get("temp_c"))
        norm["temperature_c"] = float(temp) if temp is not None else None

        # 9. relative_humidity_pct
        hum = feature_dict.get("relative_humidity_pct", feature_dict.get("humidity"))
        norm["relative_humidity_pct"] = float(hum) if hum is not None else None

        # 10. surface_pressure_hpa
        press = feature_dict.get("surface_pressure_hpa", feature_dict.get("pressure_hpa"))
        norm["surface_pressure_hpa"] = float(press) if press is not None else None

        # 11. wind_speed_kmh
        wind = feature_dict.get("wind_speed_kmh", feature_dict.get("wind_kmh"))
        norm["wind_speed_kmh"] = float(wind) if wind is not None else None

        # 12. elevation_m
        elev = feature_dict.get("elevation_m", feature_dict.get("elevation"))
        norm["elevation_m"] = float(elev) if elev is not None else None

        # 13. catchment_slope_deg
        slope = feature_dict.get("catchment_slope_deg", feature_dict.get("slope"))
        norm["catchment_slope_deg"] = float(slope) if slope is not None else None

        # 14. dist_to_river_m
        d_raw = feature_dict.get("dist_to_river_m", feature_dict.get("distance_to_river"))
        if d_raw is not None:
            d_val = float(d_raw)
            # Legacy distance_to_river was sometimes given in kilometers (<= 20.0)
            norm["dist_to_river_m"] = d_val * 1000.0 if d_val <= 20.0 else d_val
        else:
            norm["dist_to_river_m"] = None

        # 15. upstream_drainage_sqkm
        drain = feature_dict.get("upstream_drainage_sqkm", feature_dict.get("upstream_drainage", feature_dict.get("drainage_area")))
        norm["upstream_drainage_sqkm"] = float(drain) if drain is not None else None

        return norm

    def predict(
        self,
        feature_dict: Dict[str, Any],
        data_quality_score: float = 1.0,
        freshness_seconds: int = 0,
        region: Optional[str] = None,
    ) -> Tuple[float, float, List[Dict[str, Any]]]:
        """
        Runs ML prediction and returns backwards-compatible 3-tuple:
        (flood_probability, prediction_quality, top_contributing_factors)
        """
        res = self.predict_full(feature_dict, data_quality_score, freshness_seconds, region=region)
        return res["flood_probability"], res["prediction_quality"], res["top_contributing_factors"]

    def predict_full(
        self,
        feature_dict: Dict[str, Any],
        data_quality_score: float = 1.0,
        freshness_seconds: int = 0,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Runs comprehensive V2 inference and returns all operational & diagnostic fields.
        Delegates administrative risk scoring strictly to RiskEngine.
        """
        if not self.is_ready:
            self.load_artifacts()

        # Check for model unreadiness
        if not self.is_ready:
            logger.warning("PredictionService: V2 model not ready; returning safe degraded payload.")
            return {
                "flood_probability": 0.0,
                "calibrated_probability": 0.0,
                "raw_probability": 0.0,
                "decision_threshold": 0.08,
                "threshold_exceeded": False,
                "prediction_quality": 0.0,
                "model_version": self.metadata["model_version"],
                "model_integrity_status": model_integrity_checker.state.value,
                "risk_score": 0,
                "operational_risk_score": 0,
                "policy_score": 0,
                "risk_level": "INSUFFICIENT_DATA",
                "operational_risk_level": "INSUFFICIENT_DATA",
                "top_contributing_factors": [],
                "top_shap_factors": [],
                "physical_explanations": ["Model integrity check failed or artifacts unavailable."],
                "status": "model_unavailable",
                "topographic_factor": 0.0,
            }

        # Normalize features to canonical 15
        canonical_inputs = self.normalize_feature_vector(feature_dict)

        # Pass through insufficient_data flag if present
        if feature_dict.get("insufficient_data") is not None:
            canonical_inputs["insufficient_data"] = feature_dict.get("insufficient_data")

        # Pass through vulnerability index if present
        if feature_dict.get("vulnerability_index") is not None:
            try:
                canonical_inputs["vulnerability_index"] = float(feature_dict["vulnerability_index"])
            except (ValueError, TypeError):
                pass
        if feature_dict.get("preparedness_factor") is not None:
            try:
                canonical_inputs["preparedness_factor"] = float(feature_dict["preparedness_factor"])
            except (ValueError, TypeError):
                pass

        # Pass through region if present
        selected_region = region or feature_dict.get("region")
        if selected_region:
            canonical_inputs["region"] = selected_region

        # Execute V2 / regional inference pipeline
        raw_res = predict_flood_risk(canonical_inputs)

        if raw_res.get("status") == "insufficient_data" or raw_res.get("risk_level") == "INSUFFICIENT_DATA":
            return {
                "flood_probability": 0.0,
                "calibrated_probability": 0.0,
                "raw_probability": 0.0,
                "decision_threshold": float(raw_res.get("threshold", 0.08)),
                "threshold_exceeded": False,
                "prediction_quality": 0.0,
                "model_version": self.metadata["model_version"],
                "model_integrity_status": model_integrity_checker.state.value,
                "risk_score": 0,
                "operational_risk_score": 0,
                "policy_score": 0,
                "risk_level": "INSUFFICIENT_DATA",
                "operational_risk_level": "INSUFFICIENT_DATA",
                "top_contributing_factors": [],
                "top_shap_factors": [],
                "physical_explanations": raw_res.get("explanation", raw_res.get("physical_explanations", ["Data quality safety guardrail tripped."])),
                "status": "insufficient_data",
                "topographic_factor": 0.0,
            }

        calibrated_prob = float(raw_res.get("flood_probability", 0.0))
        raw_prob = float(raw_res.get("raw_probability", calibrated_prob))
        threshold = float(raw_res.get("threshold", 0.08))
        threshold_exceeded = bool(calibrated_prob >= threshold)

        # Authentic feature attributions from ModelExplainer
        top_factors = raw_res.get("top_contributing_factors", [])

        # Operational risk scoring delegated strictly to RiskEngine
        v_val = feature_dict.get("vulnerability_index")
        v_idx = float(v_val) if v_val is not None else 0.50

        infra_val = feature_dict.get("critical_infrastructure_index")
        infra_idx = float(infra_val) if infra_val is not None else 0.50

        pop_val = feature_dict.get("population_density_index")
        pop_idx = float(pop_val) if pop_val is not None else 0.50

        topo_factor = float(raw_res.get("topographic_factor", 0.50))

        tr_val = feature_dict.get("trend_factor")
        trend_factor = float(tr_val) if tr_val is not None else 1.0

        risk_score, risk_lvl, color_hex, is_capped = risk_engine.compute_operational_risk(
            flood_probability=calibrated_prob,
            trend_factor=trend_factor,
            vulnerability_index=v_idx,
            data_quality_score=data_quality_score,
            freshness_seconds=freshness_seconds,
            critical_infrastructure_index=infra_idx,
            population_density_index=pop_idx,
            topographic_factor=topo_factor,
        )

        # Composite prediction quality
        margin = abs(calibrated_prob - threshold) * 2.0
        freshness_factor = max(0.0, 1.0 - (freshness_seconds / 3600.0))
        quality = round(0.4 * margin + 0.3 * data_quality_score + 0.3 * freshness_factor, 3)
        quality = max(0.1, min(1.0, quality))

        return {
            "flood_probability": round(calibrated_prob, 4),
            "calibrated_probability": round(calibrated_prob, 4),
            "raw_probability": round(raw_prob, 4),
            "decision_threshold": round(threshold, 4),
            "threshold_exceeded": threshold_exceeded,
            "prediction_quality": quality,
            "model_version": raw_res.get("model_version") or self.metadata["model_version"],
            "region": raw_res.get("region") or selected_region or "himachal_pradesh",
            "region_display_name": raw_res.get("region_display_name", "Himachal Pradesh"),
            "model_integrity_status": ModelIntegrityState.MODEL_READY.value,
            "risk_score": risk_score,
            "operational_risk_score": risk_score,
            "policy_score": risk_score,
            "risk_level": risk_lvl,
            "operational_risk_level": risk_lvl,
            "color_hex": color_hex,
            "is_capped_by_quality": is_capped,
            "top_contributing_factors": top_factors,
            "top_shap_factors": top_factors,
            "physical_explanations": raw_res.get("explanation", []),
            "status": raw_res.get("status", "operational_v2_validated"),
            "topographic_factor": round(topo_factor, 3),
        }

    def _compute_feature_attributions(
        self, canonical_inputs: Dict[str, float], calibrated_prob: float
    ) -> List[Dict[str, Any]]:
        """
        @deprecated: Uses authentic ModelExplainer attributions from ml.inference.explain.
        """
        explainer = get_explainer()
        return explainer.explain_prediction(canonical_inputs, calibrated_prob, top_k=4)


prediction_service = PredictionService()
