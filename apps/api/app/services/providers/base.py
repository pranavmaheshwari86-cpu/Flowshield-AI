"""
apps/api/app/services/providers/base.py
Flowshield — Abstract Data Provider Interface (v2.4)
Defines the base contract for all external and internal data sources.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from ...schemas.observation import NormalizedObservation, SourceType, DataState, DataQualityStatus


class FreshnessPolicy(BaseModel):
    """Encapsulates provider-specific temporal validity bounds."""
    expected_update_interval_sec: int = Field(3600, description="Nominal cadence between updates (seconds)")
    stale_after_sec: int = Field(7200, description="Age after which data transitions to STALE (seconds)")
    hard_expiry_sec: int = Field(21600, description="Age after which data is EXPIRED / INSUFFICIENT (seconds)")


class LocationTarget(BaseModel):
    """Target geographic location for telemetry acquisition."""
    id: str
    name: str
    latitude: float
    longitude: float
    state: str = "National"
    district: str = ""
    elevation_m: float = 1000.0
    slope_deg: float = 20.0
    distance_to_river_m: float = 100.0
    upstream_drainage_sqkm: float = 2500.0


class DataProvider(ABC):
    """Abstract Base Class for all Flowshield Telemetry Providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider identifier."""
        pass

    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        """Canonical classification of the source."""
        pass

    @abstractmethod
    def fetch(self, targets: List[LocationTarget]) -> Dict[str, Any]:
        """Fetch raw payload from upstream provider or data source."""
        pass

    @abstractmethod
    def validate(self, raw_payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validates schema, completeness, and physical bounds of raw payload."""
        pass

    @abstractmethod
    def normalize(self, raw_payload: Dict[str, Any], targets: List[LocationTarget]) -> List[NormalizedObservation]:
        """Converts raw validated payload into canonical NormalizedObservation objects."""
        pass

    @abstractmethod
    def provenance(self) -> Dict[str, Any]:
        """Returns provenance dictionary with provider, citation, spatial/temporal resolution, license."""
        pass

    @abstractmethod
    def freshness_policy(self) -> FreshnessPolicy:
        """Returns provider-specific freshness intervals."""
        pass

    @abstractmethod
    def health(self) -> bool:
        """Checks upstream availability and connectivity."""
        pass
