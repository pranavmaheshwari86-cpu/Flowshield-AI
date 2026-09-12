"""Structured domain error codes and error response models for FlowShield."""

from enum import Enum
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """Standardized error codes preventing silent fallbacks or ambiguous failures."""
    MODEL_NOT_SUPPORTED_FOR_LOCATION = "MODEL_NOT_SUPPORTED_FOR_LOCATION"
    MODEL_INPUT_UNAVAILABLE = "MODEL_INPUT_UNAVAILABLE"
    WEATHER_PROVIDER_UNAVAILABLE = "WEATHER_PROVIDER_UNAVAILABLE"
    PRECIPITATION_FORECAST_UNAVAILABLE = "PRECIPITATION_FORECAST_UNAVAILABLE"
    RIVER_DATA_UNAVAILABLE = "RIVER_DATA_UNAVAILABLE"
    RIVER_DATA_STALE = "RIVER_DATA_STALE"
    INVALID_PROVIDER_DATA = "INVALID_PROVIDER_DATA"
    LOCATION_NOT_FOUND = "LOCATION_NOT_FOUND"
    DATA_QUALITY_DEGRADED = "DATA_QUALITY_DEGRADED"


class ServiceErrorDetail(BaseModel):
    """Standardized machine-readable error detail embedded in API responses."""
    code: ErrorCode = Field(..., description="Machine-readable error identifier")
    message: str = Field(..., description="Human-readable explanation")
    provider: Optional[str] = Field(None, description="Affected upstream provider, if applicable")
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Time error was recorded")
    location_id: Optional[str] = Field(None, description="Location context of the error")
    retry_after_seconds: Optional[int] = Field(None, description="Recommended retry delay in seconds")
