"""
apps/api/app/schemas/prediction.py
Flowshield — Prediction & Inference Schemas (v2.4)
Supports both canonical 15 features and legacy schema aliases.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    village_id: Optional[str] = None
    region: Optional[str] = Field(None, description="Regional slug for localized inference")

    # Canonical 15 features (ERA5-Land / DEM)
    rainfall_1h_mm: Optional[float] = Field(None, ge=0.0, le=1000.0)
    rainfall_3h_mm: Optional[float] = Field(None, ge=0.0, le=1500.0)
    rainfall_6h_mm: Optional[float] = Field(None, ge=0.0, le=2000.0)
    rainfall_24h_mm: Optional[float] = Field(None, ge=0.0, le=3000.0)
    rainfall_72h_mm: Optional[float] = Field(None, ge=0.0, le=5000.0)
    soil_saturation_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    deep_soil_saturation_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    temperature_c: Optional[float] = Field(None, ge=-50.0, le=60.0)
    relative_humidity_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    surface_pressure_hpa: Optional[float] = Field(None, ge=500.0, le=1100.0)
    wind_speed_kmh: Optional[float] = Field(None, ge=0.0, le=300.0)
    elevation_m: Optional[float] = Field(None, ge=0.0, le=9000.0)
    catchment_slope_deg: Optional[float] = Field(None, ge=0.0, le=90.0)
    dist_to_river_m: Optional[float] = Field(None, ge=0.0, le=100000.0)
    upstream_drainage_sqkm: Optional[float] = Field(None, ge=0.0, le=100000.0)

    # Optional vulnerability & operational adjustments
    vulnerability_index: Optional[float] = Field(None, ge=0.0, le=1.0)
    preparedness_factor: Optional[float] = Field(None, ge=0.0, le=1.0)
    insufficient_data: Optional[bool] = Field(False, description="Flag indicating sensor blackout or telemetry failure.")

    # Legacy aliases for backwards compatibility
    rainfall_1h: Optional[float] = Field(None, ge=0.0, le=1000.0)
    rainfall_3h: Optional[float] = Field(None, ge=0.0, le=1500.0)
    rainfall_6h: Optional[float] = Field(None, ge=0.0, le=2000.0)
    rainfall_24h: Optional[float] = Field(None, ge=0.0, le=3000.0)
    rainfall_intensity: Optional[float] = Field(None, ge=0.0, le=500.0)
    soil_moisture: Optional[float] = Field(None, ge=0.0, le=100.0)
    river_level: Optional[float] = Field(None, ge=0.0, le=100.0)
    river_level_change: Optional[float] = Field(None, ge=-50.0, le=50.0)
    elevation: Optional[float] = Field(None, ge=0.0, le=9000.0)
    slope: Optional[float] = Field(None, ge=0.0, le=90.0)
    distance_to_river: Optional[float] = Field(None, ge=0.0, le=100.0)  # km in legacy
    historical_flood_frequency: Optional[float] = Field(None, ge=0.0, le=1.0)


class FeatureContribution(BaseModel):
    feature: str
    feature_name: Optional[str] = None
    display_name: Optional[str] = None
    value: float
    unit: Optional[str] = None
    contribution: float
    shap_value: Optional[float] = None
    direction: str  # "increases_risk" or "decreases_risk"
    contribution_direction: Optional[str] = None
    percentage_impact: Optional[float] = None


class PredictionResponse(BaseModel):
    prediction_id: str
    village_id: Optional[str] = None
    flood_probability: float = Field(..., ge=0.0, le=1.0)
    calibrated_probability: float = Field(..., ge=0.0, le=1.0)
    raw_probability: Optional[float] = None
    decision_threshold: float = Field(0.08, ge=0.0, le=1.0)
    threshold_exceeded: bool = False
    risk_score: int = Field(..., ge=0, le=100)
    operational_risk_score: Optional[int] = Field(None, ge=0, le=100)
    policy_score: int = Field(..., ge=0, le=100)
    risk_level: str  # LOW, WATCH, HIGH, CRITICAL, INSUFFICIENT_DATA
    operational_risk_level: str  # LOW, WATCH, HIGH, CRITICAL, INSUFFICIENT_DATA
    prediction_quality: float = Field(..., ge=0.0, le=1.0)
    model_version: str
    model_integrity_status: str = "MODEL_READY"
    top_contributing_factors: List[FeatureContribution] = []
    top_shap_factors: List[FeatureContribution] = []
    physical_explanations: List[str] = []
    data_provenance: Optional[Dict[str, Any]] = None
    timestamp: datetime
