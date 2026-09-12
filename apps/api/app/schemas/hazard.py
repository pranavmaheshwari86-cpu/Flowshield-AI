"""
apps/api/app/schemas/hazard.py
Flowshield — Multi-Hazard & Forecasting Pydantic Schemas (v2.4)
Enforces prototype labeling, non-ML empirical thresholds, and honest uncertainty semantics.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class LandslideAssessmentResponse(BaseModel):
    village_id: str
    village_name: str
    trigger_index: float = Field(..., ge=0.0, le=1.0)
    susceptibility_level: str  # LOW, MODERATE, HIGH, CRITICAL, SUSCEPTIBILITY_UNAVAILABLE
    slope_deg: float
    rainfall_24h_mm: float
    soil_saturation_pct: float
    methodology: str = "Empirical Rainfall-Slope Threshold (GSI / Caine 1980)"
    status: str = "PROTOTYPE_EMPIRICAL_THRESHOLD"
    is_ml_model: bool = False
    scientific_disclosure: str = (
        "Empirical screening prototype derived from slope incline and antecedent rainfall. "
        "This is NOT a trained machine learning model or certified geotechnical stability assessment."
    )
    advisory_notice: str = (
        "Advisory screening only. In case of slope cracking, debris flow, or torrential rain, "
        "evacuate immediately and contact Geological Survey of India (GSI) and local DDMA."
    )
    timestamp: datetime


class ForecastHorizon(BaseModel):
    lead_time_hours: int
    forecast_timestamp: datetime
    projected_rainfall_mm: Optional[float] = None
    rainfall_intensity_mm_hr: Optional[float] = None
    uncertainty_state: str = "UNCERTAINTY_UNAVAILABLE"  # UNCERTAINTY_UNAVAILABLE or CALIBRATED_INTERVAL
    confidence_interval_p10: Optional[float] = None
    confidence_interval_p90: Optional[float] = None
    forecast_source: str = "ECMWF High-Resolution Forecast via Open-Meteo"


class MultiHorizonForecastResponse(BaseModel):
    village_id: str
    village_name: str
    generated_at: datetime
    horizons: List[ForecastHorizon]
    cumulative_48h_rainfall_mm: Optional[float] = None
    peak_intensity_horizon_hours: Optional[int] = None
    scientific_disclosure: str = (
        "Atmospheric precipitation projections obtained from numerical weather prediction. "
        "Uncertainty intervals are only provided when ensemble variance is published by upstream source."
    )


class SoilMoistureForecastHorizon(BaseModel):
    lead_time_hours: int
    projected_soil_saturation_pct: float
    model_type: str = "1D_WATER_BALANCE_BUCKET"
    status: str = "PROTOTYPE_BASELINE"
    is_ml_model: bool = False


class SoilMoistureForecastResponse(BaseModel):
    village_id: str
    village_name: str
    generated_at: datetime
    horizons: List[SoilMoistureForecastHorizon]
    status: str = "PROTOTYPE_BASELINE"
    is_ml_model: bool = False
    scientific_disclosure: str = (
        "Decoupled 1D water-balance bucket model (dS = P - ET - Drainage). "
        "PROTOTYPE BASELINE ONLY — subterranean soil dynamics are decoupled from atmospheric weather models."
    )


class FutureRiskHorizon(BaseModel):
    horizon_hours: int
    forecast_timestamp: str
    flood_probability: float
    risk_score: float
    risk_level: str
    rainfall_intensity_mm_hr: float
    cumulative_rainfall_mm: float
    soil_saturation_pct: float
    confidence: float
    uncertainty_band: Dict[str, float]
    key_drivers: List[str]


class FutureRiskTimelineResponse(BaseModel):
    village_id: str
    village_name: str
    latitude: float
    longitude: float
    generated_at: str
    timeline: List[FutureRiskHorizon]
    peak_risk_score: float
    peak_risk_horizon_hours: Optional[int]
    model_version: str
    calibration_method: str
