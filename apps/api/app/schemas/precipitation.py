"""Precipitation domain schemas for FlowShield.

Permanently isolates precipitation forecasts (NWP in mm/h) from flood risk (% probability).
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from .data_types import DataType, FreshnessStatus
from .provenance import DataProvenance


class PrecipitationPoint(BaseModel):
    """A single discrete time-series point for precipitation (observed or forecast)."""
    timestamp_utc: datetime = Field(..., description="UTC ISO timestamp")
    timestamp_ist: str = Field(..., description="Formatted Indian Standard Time e.g. '2026-09-12 15:30 IST'")
    relative_hour: int = Field(..., description="Relative offset in hours from reference NOW (e.g. -6, 0, +1, +24)")
    value_mm_hr: Optional[float] = Field(None, description="Precipitation rate in mm/h. None if missing; 0.0 ONLY if provider reported 0.0")
    type: DataType = Field(..., description="OBSERVED or FORECAST_NWP")
    source: str = Field(..., description="Source attribution e.g. 'Open-Meteo (ECMWF IFS)' or 'OpenWeather'")
    status: str = Field("VALID", description="VALID, ESTIMATED, UNAVAILABLE")
    forecast_lead_hours: Optional[int] = Field(None, description="Forecast lead time in hours (null for observed points)")


class PrecipitationForecastResponse(BaseModel):
    """Complete precipitation package combining observed history and numerical weather forecast."""
    model_name: str = Field("ECMWF IFS via Open-Meteo", description="NWP model name")
    model_run_utc: Optional[datetime] = Field(None, description="Initial cycle time of the NWP model run")
    model_run_ist: Optional[str] = Field(None, description="Model run time in IST")
    current_rate_mm_hr: Optional[float] = Field(None, description="Latest observed precipitation rate in mm/h")
    observed_points: List[PrecipitationPoint] = Field(default_factory=list, description="Historical observed points (typically -6h to 0h)")
    forecast_points: List[PrecipitationPoint] = Field(default_factory=list, description="Future projected points (+1h to +48h)")
    peak_forecast_mm_hr: Optional[float] = Field(None, description="Highest projected precipitation rate in the next 24h/48h")
    peak_forecast_time_ist: Optional[str] = Field(None, description="IST time of peak projected precipitation")
    accumulated_24h_forecast_mm: Optional[float] = Field(None, description="Total projected 24-hour rainfall accumulation in mm")
    provenance: DataProvenance
    freshness: FreshnessStatus
