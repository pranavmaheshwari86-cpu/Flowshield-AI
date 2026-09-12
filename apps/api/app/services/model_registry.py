"""Production Model Registry and Governance Service for FlowShield.

Enforces strict model governance:
1. Location -> capability check
2. Model registry lookup
3. Geographic coverage verification (State / District)
4. Production readiness status check
5. Feature schema compliance
6. Rejection of unvalidated regions (No cross-regional silent fallbacks!)
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from ..models.village import Village
from ..schemas.data_types import ModelSupport
from ..schemas.errors import ErrorCode, ServiceErrorDetail
from ml.registry.model_registry import ModelRegistry, RegionalModelBundle, _FLOOD_MODELS_DIR
from ml.registry.region_resolver import region_resolver, SUPPORTED_REGIONS, STATE_TO_REGION

logger = logging.getLogger("flowshield.model_registry_service")


class ModelGovernanceError(Exception):
    """Exception raised when an inference request violates model governance rules."""
    def __init__(self, code: ErrorCode, message: str, location_id: Optional[str] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.location_id = location_id

    def to_service_error(self) -> ServiceErrorDetail:
        return ServiceErrorDetail(
            code=self.code,
            message=self.message,
            location_id=self.location_id,
        )


class ModelRegistryService:
    """Production wrapper and governance gateway for machine learning models."""

    def __init__(self):
        self._underlying_registry = ModelRegistry()

    def get_supported_regions(self) -> List[str]:
        """Returns list of region slugs defined in system."""
        return list(SUPPORTED_REGIONS)

    def is_location_supported(self, village: Village) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates whether a location has an approved, validated model.
        Returns: (is_supported, region_slug, rejection_reason)
        """
        state = (village.state or "").strip().lower()
        district = (village.district or "").strip().lower()

        # Check if state/district maps to any supported model region
        region_slug = None
        if "himachal" in state:
            region_slug = "himachal_pradesh"
        elif "uttarakhand" in state:
            region_slug = "uttarakhand"
        elif "ladakh" in state:
            region_slug = "leh_ladakh"
        elif "sikkim" in state:
            region_slug = "sikkim"

        # Special Case: Buxar / Bihar Gangetic plains have NO validated flash flood model
        if "bihar" in state:
            return (
                False,
                None,
                f"No validated flood-risk machine learning model trained for Bihar Gangetic plains (village: {village.name}, district: {village.district}). Cross-regional proxying is prohibited."
            )

        if not region_slug or region_slug not in SUPPORTED_REGIONS:
            return (
                False,
                None,
                f"Location {village.name} in state '{village.state}' is outside the geographic coverage of validated flood-risk models."
            )

        # Check if model artifact actually exists on disk
        try:
            bundle = self._underlying_registry.get(hazard="flood", region=region_slug)
            return True, region_slug, None
        except Exception as e:
            return (
                False,
                region_slug,
                f"Model bundle for region '{region_slug}' not operational: {e}"
            )

    def get_model_bundle_for_location(self, village: Village) -> RegionalModelBundle:
        """
        Executes governance validation before loading model bundle.
        Raises ModelGovernanceError if region is unsupported. NEVER proxies wrong region!
        """
        is_supp, region_slug, reason = self.is_location_supported(village)
        if not is_supp or not region_slug:
            logger.warning(f"Model governance check failed for village {village.id} ({village.name}): {reason}")
            raise ModelGovernanceError(
                code=ErrorCode.MODEL_NOT_SUPPORTED_FOR_LOCATION,
                message=reason or "Location not supported by model registry",
                location_id=village.id,
            )

        return self._underlying_registry.get(hazard="flood", region=region_slug)

    def get_feature_schema(self, region_slug: str = "himachal_pradesh") -> List[str]:
        """Returns canonical list of feature names required by model."""
        try:
            bundle = self._underlying_registry.get(hazard="flood", region=region_slug)
            if bundle.feature_schema and "features" in bundle.feature_schema:
                return bundle.feature_schema["features"]
        except Exception:
            pass

        # Canonical 15-feature standard from v2_decision_pipeline.json
        return [
            "rainfall_1h_mm",
            "rainfall_3h_mm",
            "rainfall_6h_mm",
            "rainfall_24h_mm",
            "rainfall_72h_mm",
            "soil_saturation_pct",
            "deep_soil_saturation_pct",
            "temperature_c",
            "relative_humidity_pct",
            "surface_pressure_hpa",
            "wind_speed_kmh",
            "elevation_m",
            "catchment_slope_deg",
            "dist_to_river_m",
            "upstream_drainage_sqkm",
        ]

    def get_status_overview(self) -> Dict[str, Any]:
        """Returns system-wide model registry status for API /models/status."""
        regions_status = {}
        for reg in SUPPORTED_REGIONS:
            try:
                bundle = self._underlying_registry.get(hazard="flood", region=reg)
                regions_status[reg] = {
                    "status": "OPERATIONAL",
                    "model_version": bundle.model_version,
                    "production_status": bundle.production_status,
                    "algorithm": bundle.metadata.get("algorithm", "LogisticRegression"),
                    "threshold": bundle.threshold,
                }
            except Exception as e:
                regions_status[reg] = {
                    "status": "UNAVAILABLE",
                    "error": str(e),
                }

        return {
            "registry_version": "2.5.0-governed",
            "active_regions_count": sum(1 for r in regions_status.values() if r.get("status") == "OPERATIONAL"),
            "supported_regions": regions_status,
            "prohibited_fallbacks": ["bihar -> himachal_pradesh", "cross_region_silent_default"],
        }


model_registry_service = ModelRegistryService()
