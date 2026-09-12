"""Location capabilities schema.

Enforces capability-based functionality: a location without a validated ML model
still supports weather, NWP precipitation forecasting, river monitoring, and terrain intelligence.
"""

from typing import Optional
from pydantic import BaseModel, Field
from .data_types import DataType, FreshnessStatus, ModelSupport, DataAvailability


class LocationCapability(BaseModel):
    """Granular feature capabilities supported for a specific geographic settlement."""
    village_id: str = Field(..., description="Unique settlement identifier")
    village_name: str = Field(..., description="Display name of the village/settlement")
    district: str = Field(..., description="Administrative district")
    state: str = Field(..., description="State name")
    latitude: float = Field(..., description="WGS84 latitude")
    longitude: float = Field(..., description="WGS84 longitude")

    # Granular capability flags
    weather_observation: bool = Field(..., description="True if real-time atmospheric observation is available")
    precipitation_forecast: bool = Field(..., description="True if NWP precipitation forecast is available")
    river_monitoring: FreshnessStatus = Field(..., description="River telemetry or bulletin state")
    river_station_name: Optional[str] = Field(None, description="Monitored CWC gauge station name if applicable")
    soil_estimation: DataType = Field(..., description="DERIVED_ESTIMATE or UNAVAILABLE")
    terrain_attributes: bool = Field(..., description="True if elevation, slope, and drainage basin are in DB")
    
    # ML Flood Risk Governance
    flood_risk_model: ModelSupport = Field(..., description="SUPPORTED, UNSUPPORTED, or VALIDATION_ONLY")
    model_id: Optional[str] = Field(None, description="Identifier of the active validated model if supported")
    model_region: Optional[str] = Field(None, description="Geographic model region slug (e.g. himachal_pradesh)")
    target_region: Optional[str] = Field(None, description="Target geographic model region or administrative region")
    unsupported_reason: Optional[str] = Field(
        None, 
        description="Explicit reason if ML model is unsupported (e.g. 'No validated ML model trained for Bihar Gangetic plains')"
    )
