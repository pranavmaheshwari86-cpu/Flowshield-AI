"""
apps/api/app/services/future_risk_service.py
Flowshield — Future Flood Risk Prediction Timeline Service (v3.0)
Smart India Hackathon 2026 (PS ID: 26192)

Projects future multi-horizon hydro-meteorological features (+1h to +48h)
and evaluates them through the calibrated V2 ML inference engine to generate
actionable predictive flood-risk timelines with uncertainty envelopes.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from .forecast_service import forecast_service
from ..models.village import Village
from ..models.observation import EnvironmentalObservation
from ml.inference.predict import predict_flood_risk

logger = logging.getLogger("flowshield.future_risk")


class FutureRiskService:
    """Computes multi-horizon ML flood risk projections based on precipitation forecasts."""

    DEFAULT_HORIZONS = [1, 3, 6, 12, 24, 48]

    def predict_future_risk_timeline(
        self,
        village: Village,
        db: Optional[Session] = None,
        horizons_hours: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Generates ML flood risk projections across future time horizons.
        """
        if horizons_hours is None:
            horizons_hours = self.DEFAULT_HORIZONS

        now = datetime.now(timezone.utc)
        precip_series = forecast_service._fetch_precipitation_projections(village, db)
        base_features = self._get_base_village_features(village, db)

        timeline = []
        highest_risk_horizon = None
        peak_risk_score = -1.0

        for h in horizons_hours:
            # 1. Project hydrological features at horizon h
            proj_features = self._project_features_at_horizon(base_features, precip_series, h)

            # 2. Run calibrated ML inference
            inference = predict_flood_risk(proj_features)
            
            risk_score = float(inference.get("risk_score", 0.0))
            flood_prob = float(inference.get("flood_probability", 0.0))
            risk_level = str(inference.get("risk_level", "LOW"))

            # Calculate uncertainty bounds based on forecast lead time
            # Uncertainty expands slightly with forecast horizon
            dispersion = min(0.18, 0.025 + (h * 0.003))
            p10 = max(0.0, round(flood_prob - dispersion, 4))
            p90 = min(1.0, round(flood_prob + dispersion, 4))

            # Cumulative rainfall up to this hour
            accum_rain = sum(precip_series[:h]) if precip_series else round(proj_features["rainfall_1h_mm"] * h, 1)
            intensity = precip_series[min(len(precip_series) - 1, h - 1)] if precip_series else proj_features["rainfall_1h_mm"]

            horizon_entry = {
                "horizon_hours": h,
                "forecast_timestamp": (now + timedelta(hours=h)).isoformat(),
                "flood_probability": round(flood_prob, 4),
                "risk_score": round(risk_score, 1),
                "risk_level": risk_level,
                "rainfall_intensity_mm_hr": round(intensity, 2),
                "cumulative_rainfall_mm": round(accum_rain, 1),
                "soil_saturation_pct": round(proj_features["soil_saturation_pct"], 1),
                "confidence": round(float(inference.get("confidence", 0.85)), 3),
                "uncertainty_band": {
                    "p10": p10,
                    "p90": p90,
                },
                "key_drivers": inference.get("explanation", [])[:3],
            }

            if risk_score > peak_risk_score:
                peak_risk_score = risk_score
                highest_risk_horizon = h

            timeline.append(horizon_entry)

        return {
            "village_id": village.id,
            "village_name": village.name,
            "latitude": village.latitude,
            "longitude": village.longitude,
            "generated_at": now.isoformat(),
            "timeline": timeline,
            "peak_risk_score": round(peak_risk_score, 1),
            "peak_risk_horizon_hours": highest_risk_horizon,
            "model_version": "flowshield-flood-risk-v2",
            "calibration_method": "isotonic (τ=0.08)"
        }

    def _get_base_village_features(self, village: Village, db: Optional[Session]) -> Dict[str, float]:
        """Extracts current real or observed baseline features for a village."""
        # Static physical terrain features
        elevation = getattr(village, "elevation_m", 850.0) or 850.0
        slope = getattr(village, "slope_deg", 22.0) or 22.0
        dist_river = getattr(village, "distance_to_river_m", 120.0) or 120.0
        drainage = getattr(village, "upstream_drainage_sqkm", 3200.0) or 3200.0

        # Latest dynamic telemetry from DB if available
        rain_1h = 2.0
        rain_3h = 8.0
        rain_6h = 16.0
        rain_24h = 35.0
        rain_72h = 55.0
        soil_sat = 62.0
        deep_soil = 58.0
        temp_c = 21.0
        rel_hum = 78.0
        pressure = 918.0
        wind = 12.0

        if db:
            latest = (
                db.query(EnvironmentalObservation)
                .filter(EnvironmentalObservation.village_id == village.id)
                .order_by(EnvironmentalObservation.timestamp.desc())
                .first()
            )
            if latest:
                rain_1h = float(latest.rainfall_1h or rain_1h)
                rain_3h = float(latest.rainfall_3h or rain_3h)
                rain_6h = float(latest.rainfall_6h or rain_6h)
                rain_24h = float(latest.rainfall_24h or rain_24h)
                rain_72h = float(latest.rainfall_72h or rain_72h)
                soil_sat = float(latest.soil_moisture or soil_sat)
                deep_soil = float(latest.deep_soil_moisture or deep_soil)
                temp_c = float(latest.temperature or temp_c)
                rel_hum = float(latest.humidity or rel_hum)
                pressure = float(latest.surface_pressure or pressure)
                wind = float(latest.wind_speed or wind)

        return {
            "rainfall_1h_mm": rain_1h,
            "rainfall_3h_mm": rain_3h,
            "rainfall_6h_mm": rain_6h,
            "rainfall_24h_mm": rain_24h,
            "rainfall_72h_mm": rain_72h,
            "soil_saturation_pct": soil_sat,
            "deep_soil_saturation_pct": deep_soil,
            "temperature_c": temp_c,
            "relative_humidity_pct": rel_hum,
            "surface_pressure_hpa": pressure,
            "wind_speed_kmh": wind,
            "elevation_m": float(elevation),
            "catchment_slope_deg": float(slope),
            "dist_to_river_m": float(dist_river),
            "upstream_drainage_sqkm": float(drainage),
        }

    def _project_features_at_horizon(
        self,
        base_features: Dict[str, float],
        precip_series: List[float],
        horizon: int
    ) -> Dict[str, float]:
        """
        Synthesizes realistic feature projections at horizon H using
        hydrological conservation principles and precipitation forecasts.
        """
        feats = base_features.copy()

        if precip_series and len(precip_series) >= horizon:
            idx = horizon - 1
            rain_rate = precip_series[idx]
            
            # Multi-hour sums from forecast
            start_3h = max(0, horizon - 3)
            rain_3h = sum(precip_series[start_3h:horizon])
            
            start_6h = max(0, horizon - 6)
            rain_6h = sum(precip_series[start_6h:horizon])

            start_24h = max(0, horizon - 24)
            rain_24h = sum(precip_series[start_24h:horizon]) + max(0.0, base_features["rainfall_24h_mm"] * (1.0 - horizon / 24.0))
            
            accum_to_h = sum(precip_series[:horizon])
            rain_72h = base_features["rainfall_72h_mm"] + accum_to_h

            feats["rainfall_1h_mm"] = rain_rate
            feats["rainfall_3h_mm"] = rain_3h
            feats["rainfall_6h_mm"] = rain_6h
            feats["rainfall_24h_mm"] = rain_24h
            feats["rainfall_72h_mm"] = rain_72h

            # Dynamic Soil Saturation Model:
            # S(t) = S(0) + (cumulative_rain * 0.45) - (t * 0.3 drainage)
            delta_soil = (accum_to_h * 0.45) - (horizon * 0.25)
            new_soil = min(98.5, max(15.0, base_features["soil_saturation_pct"] + delta_soil))
            feats["soil_saturation_pct"] = new_soil
            feats["deep_soil_saturation_pct"] = min(96.0, max(15.0, base_features["deep_soil_saturation_pct"] + (delta_soil * 0.6)))
        else:
            # Zero-fabrication policy: if no precip series available, do not fabricate synthetic decay curves
            feats["rainfall_1h_mm"] = 0.0
            feats["rainfall_3h_mm"] = 0.0
            feats["rainfall_6h_mm"] = 0.0

        return feats


future_risk_service = FutureRiskService()
