"""
apps/api/app/schemas/ai.py
Pydantic schemas for the Flowshield Real-Data AI Risk Inference API (V2).
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AIRiskRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of location (e.g. 31.7087 for Mandi)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of location (e.g. 76.9320 for Mandi)")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp (e.g. 2023-07-09T10:00:00+05:30)")
    
    # Optional direct feature overrides if sensor telemetry is supplied
    rainfall_1h_mm: Optional[float] = Field(None, ge=-100.0, le=1000.0)
    rainfall_3h_mm: Optional[float] = Field(None, ge=-100.0, le=1500.0)
    rainfall_6h_mm: Optional[float] = Field(None, ge=-100.0, le=2000.0)
    rainfall_24h_mm: Optional[float] = Field(None, ge=-100.0, le=3000.0)
    rainfall_72h_mm: Optional[float] = Field(None, ge=-100.0, le=5000.0)
    soil_saturation_pct: Optional[float] = Field(None, ge=-50.0, le=200.0)
    deep_soil_saturation_pct: Optional[float] = Field(None, ge=-50.0, le=200.0)
    elevation_m: Optional[float] = Field(None, ge=-100.0, le=9000.0)
    catchment_slope_deg: Optional[float] = Field(None, ge=-10.0, le=90.0)
    dist_to_river_m: Optional[float] = Field(None, ge=-100.0, le=100000.0)
    upstream_drainage_sqkm: Optional[float] = Field(None, ge=0.0)
    vulnerability_index: Optional[float] = Field(None, ge=0.0, le=1.0)
    preparedness_factor: Optional[float] = Field(None, ge=0.0, le=1.0)
    insufficient_data: Optional[bool] = Field(None, description="Flag to force safety guardrail inspection")


class AIRiskResponse(BaseModel):
    risk_score: float = Field(..., description="Operational risk score from 0.0 to 100.0")
    risk_level: str = Field(..., description="LOW, WATCH, HIGH, CRITICAL, INSUFFICIENT_DATA")
    flood_probability: float = Field(..., description="Calibrated ML flood probability (0.0 to 1.0)")
    confidence: float = Field(..., description="Statistically calibrated confidence metric (0.0 to 1.0)")
    threshold: Optional[float] = Field(None, description="Operational decision threshold (e.g. 0.08)")
    calibration_method: Optional[str] = Field(None, description="Calibration scaling method (isotonic, sigmoid)")
    model_version: str = Field(..., description="Identifier of the trained real baseline model")
    model_type: str = Field(..., description="Algorithm and calibration description")
    explanation: List[str] = Field(..., description="Human-readable physical factor attributions")
    status: str = Field(..., description="operational_v2_validated or insufficient_data")
    topographic_factor: Optional[float] = None
    data_provenance: Optional[Dict[str, Any]] = None


class AIExplanationRequest(BaseModel):
    village_id: Optional[str] = Field(None, description="Village ID (e.g., mandi_sadar)")
    village_name: Optional[str] = Field("Mandi Central Basin", description="Human-readable location name")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Risk score (0-100)")
    risk_level: str = Field(..., description="LOW, WATCH, HIGH, CRITICAL")
    flood_probability: float = Field(..., ge=0.0, le=1.0, description="Calibrated flood probability")
    key_factors: List[str] = Field(default_factory=list, description="Primary physical risk drivers")
    telemetry_summary: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Current hydrology/weather readings")
    language: Optional[str] = Field("en", description="Language code: en or hi")


class AIExplanationResponse(BaseModel):
    summary: str = Field(..., description="Concise, plain-language assessment of risk")
    detailed_analysis: str = Field(..., description="In-depth hydrological and terrain breakdown")
    immediate_actions: List[str] = Field(..., description="Specific recommended actions for emergency teams & citizens")
    confidence_assessment: str = Field(..., description="Contextual explanation of prediction confidence")
    provider: str = Field(..., description="Active AI provider used (gemini, openrouter, or deterministic_fallback)")
    model: str = Field(..., description="Model identifier used")
    timestamp: str = Field(..., description="ISO 8601 generation timestamp")


class WebIntelligenceItem(BaseModel):
    id: str = Field(..., description="Unique article / alert identifier")
    title: str = Field(..., description="Title or headline")
    source: str = Field(..., description="Source agency / outlet (e.g., IMD, CWC, HP SDMA, NDTV)")
    url: Optional[str] = Field(None, description="Direct URL if available")
    published_at: str = Field(..., description="Timestamp of publication")
    summary: str = Field(..., description="Brief synopsis of advisory or event")
    severity: str = Field("INFO", description="INFO, ADVISORY, WARNING, CRITICAL")
    region: str = Field("Himachal Pradesh", description="Geographic area")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")


class WebIntelligenceResponse(BaseModel):
    items: List[WebIntelligenceItem] = Field(..., description="List of recent intelligence bulletins and news")
    total: int = Field(..., description="Total count of items")
    last_updated: str = Field(..., description="Timestamp of latest sync")
    source_status: str = Field("live", description="Status of feed acquisition")
    region_summary: Optional[str] = Field(None, description="Synthesized regional flood status overview")
