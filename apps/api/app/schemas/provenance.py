"""Data provenance and audit tracking schemas for FlowShield.

Every displayed value or telemetry vector carries cryptographic or auditable provenance
documenting source, ingestion time, freshness status, and calculation formulas.
"""

from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from .data_types import DataType, FreshnessStatus


class DataProvenance(BaseModel):
    """Full pedigree of a data point or telemetry vector."""
    source: str = Field(..., description="Authoritative upstream source (e.g., OpenWeather, Open-Meteo ECMWF, CWC)")
    source_id: Optional[str] = Field(None, description="Station ID or upstream run ID")
    source_timestamp_utc: Optional[datetime] = Field(None, description="Timestamp asserted by the data provider")
    ingestion_timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Time ingested by FlowShield")
    freshness_status: FreshnessStatus = Field(..., description="LIVE, RECENT, VERIFIED_CACHE, STALE, UNAVAILABLE")
    data_type: DataType = Field(..., description="OBSERVED, FORECAST_NWP, ML_PREDICTION, DERIVED_ESTIMATE, STATIC, CACHED, UNAVAILABLE")
    is_live: bool = Field(False, description="True ONLY for automated real-time sensor streams (< 60m old)")
    derivation_formula: Optional[str] = Field(None, description="Explicit mathematical formula if DERIVED_ESTIMATE")
    quality_notes: Optional[str] = Field(None, description="Any anomaly or sensor note")


class FreshnessMetadata(BaseModel):
    """Convenience model for telemetry freshness display in UI cards and headers."""
    status: FreshnessStatus
    is_live: bool
    age_seconds: Optional[float] = None
    last_updated_ist: Optional[str] = None
    bulletin_reference: Optional[str] = None
