"""
apps/api/app/schemas/observation.py
Flowshield — Environmental Observation Schemas & Data Semantics (v2.4)
Defines orthogonal classifications: SourceType, DataState, DataQualityStatus
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    OFFICIAL = "OFFICIAL"
    AUTOMATED_STATION = "AUTOMATED_STATION"
    SATELLITE = "SATELLITE"
    REANALYSIS = "REANALYSIS"
    MODEL_FORECAST = "MODEL_FORECAST"
    BASELINE_MODEL = "BASELINE_MODEL"
    HISTORICAL = "HISTORICAL"
    SIMULATION = "SIMULATION"
    MANUAL_REPORT = "MANUAL_REPORT"


class DataState(str, Enum):
    OBSERVED = "OBSERVED"
    FORECAST = "FORECAST"
    HISTORICAL = "HISTORICAL"
    SIMULATION = "SIMULATION"
    ESTIMATED = "ESTIMATED"
    STALE = "STALE"
    MISSING = "MISSING"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID = "INVALID"


class DataQualityStatus(str, Enum):
    VALID = "VALID"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    MISSING = "MISSING"
    INVALID = "INVALID"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class EnvironmentalObservationBase(BaseModel):
    rainfall_1h: float = Field(..., ge=0.0, le=1000.0, description="Precipitation in last 1 hour (mm)")
    rainfall_3h: float = Field(..., ge=0.0, le=1500.0, description="Precipitation cumulative 3h (mm)")
    rainfall_6h: float = Field(..., ge=0.0, le=2000.0, description="Precipitation cumulative 6h (mm)")
    rainfall_24h: float = Field(..., ge=0.0, le=3000.0, description="Precipitation cumulative 24h (mm)")
    rainfall_intensity: float = Field(..., ge=0.0, le=500.0, description="Instantaneous rain rate (mm/h)")
    soil_moisture: float = Field(..., ge=0.0, le=100.0, description="Topsoil saturation percentage (0-7cm)")
    river_level: float = Field(..., ge=0.0, le=100.0, description="River stage level (m)")
    river_level_change: float = Field(..., ge=-20.0, le=20.0, description="River level change over 3h (m)")

    # Phase 1 Additive Features
    rainfall_12h: Optional[float] = Field(None, ge=0.0, le=2500.0)
    rainfall_72h: Optional[float] = Field(None, ge=0.0, le=5000.0)
    deep_soil_moisture: Optional[float] = Field(None, ge=0.0, le=100.0)
    soil_moisture_change: Optional[float] = Field(None, ge=-50.0, le=50.0)
    river_level_change_1h: Optional[float] = Field(None, ge=-10.0, le=10.0)
    river_level_rate: Optional[float] = Field(None, ge=-10.0, le=10.0)
    temperature: Optional[float] = Field(None, ge=-50.0, le=60.0)
    humidity: Optional[float] = Field(None, ge=0.0, le=100.0)
    surface_pressure: Optional[float] = Field(None, ge=500.0, le=1100.0)
    wind_speed: Optional[float] = Field(None, ge=0.0, le=300.0)

    # Provenance and Semantics
    source: str = "Demonstration Telemetry Network"
    source_type: SourceType = SourceType.AUTOMATED_STATION
    data_state: DataState = DataState.OBSERVED
    data_quality_status: DataQualityStatus = DataQualityStatus.VALID
    data_quality_score: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    source_timestamp: Optional[datetime] = None


class EnvironmentalObservationCreate(EnvironmentalObservationBase):
    village_id: str


class EnvironmentalObservationResponse(EnvironmentalObservationBase):
    id: str
    village_id: str
    timestamp: datetime
    retrieved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NormalizedObservation(BaseModel):
    """Normalized internal DTO exchanged between DataProviders and downstream services."""
    location_id: str
    timestamp: datetime
    rainfall_1h_mm: float
    rainfall_3h_mm: float
    rainfall_6h_mm: float
    rainfall_24h_mm: float
    rainfall_72h_mm: float
    soil_saturation_pct: float
    deep_soil_saturation_pct: float
    temperature_c: float
    relative_humidity_pct: float
    surface_pressure_hpa: float
    wind_speed_kmh: float
    river_level_m: Optional[float] = None
    river_level_change_m: Optional[float] = None
    source_type: SourceType
    data_state: DataState
    data_quality_status: DataQualityStatus
    data_quality_score: float
    provider_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
