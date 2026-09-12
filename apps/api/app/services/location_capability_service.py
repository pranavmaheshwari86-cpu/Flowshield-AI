"""Location capability resolution engine for FlowShield.

Determines granular capability support per settlement without binary all-or-nothing exclusion.
Locations lacking a validated regional flood risk model (e.g., Buxar, Bihar) continue to provide
weather observations, ECMWF precipitation forecasting, CWC river telemetry, and terrain metrics.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from ..models.village import Village
from ..schemas.location_capability import LocationCapability
from ..schemas.data_types import FreshnessStatus, ModelSupport, DataType
from .providers.cwc_gauge import VERIFIED_CWC_GAUGES

logger = logging.getLogger("flowshield.location_capability")


class LocationCapabilityService:
    """Evaluates and reports operational capabilities for a given settlement."""

    # Explicit list of states with production-validated ML flood risk models
    SUPPORTED_ML_REGIONS = {
        "himachal pradesh": {
            "model_id": "flood-risk-hp-lr-v2",
            "model_region": "himachal_pradesh",
            "status": ModelSupport.SUPPORTED,
        },
        "uttarakhand": {
            "model_id": "flood-risk-hp-lr-v2",
            "model_region": "uttarakhand",
            "status": ModelSupport.SUPPORTED,
        },
        "arunachal pradesh": {
            "model_id": "flood-risk-arunachal_pradesh-v1",
            "model_region": "arunachal_pradesh",
            "status": ModelSupport.SUPPORTED,
        },
        "jammu & kashmir": {
            "model_id": "flood-risk-jammu_kashmir-v1",
            "model_region": "jammu_kashmir",
            "status": ModelSupport.SUPPORTED,
        },
        "jammu and kashmir": {
            "model_id": "flood-risk-jammu_kashmir-v1",
            "model_region": "jammu_kashmir",
            "status": ModelSupport.SUPPORTED,
        },
        "ladakh": {
            "model_id": "flood-risk-leh_ladakh-v1",
            "model_region": "leh_ladakh",
            "status": ModelSupport.SUPPORTED,
        },
        "leh & ladakh": {
            "model_id": "flood-risk-leh_ladakh-v1",
            "model_region": "leh_ladakh",
            "status": ModelSupport.SUPPORTED,
        },
        "leh and ladakh": {
            "model_id": "flood-risk-leh_ladakh-v1",
            "model_region": "leh_ladakh",
            "status": ModelSupport.SUPPORTED,
        },
        "manipur": {
            "model_id": "flood-risk-manipur-v1",
            "model_region": "manipur",
            "status": ModelSupport.SUPPORTED,
        },
        "meghalaya": {
            "model_id": "flood-risk-meghalaya-v1",
            "model_region": "meghalaya",
            "status": ModelSupport.SUPPORTED,
        },
        "mizoram": {
            "model_id": "flood-risk-mizoram-v1",
            "model_region": "mizoram",
            "status": ModelSupport.SUPPORTED,
        },
        "nagaland": {
            "model_id": "flood-risk-nagaland-v1",
            "model_region": "nagaland",
            "status": ModelSupport.SUPPORTED,
        },
        "sikkim": {
            "model_id": "flood-risk-sikkim-v1",
            "model_region": "sikkim",
            "status": ModelSupport.SUPPORTED,
        },
        "tripura": {
            "model_id": "flood-risk-tripura-v1",
            "model_region": "tripura",
            "status": ModelSupport.SUPPORTED,
        },
    }

    def evaluate_capabilities(self, village: Village, db: Optional[Session] = None) -> LocationCapability:
        """Computes granular capability vector for a village."""
        # 1. Weather observation capability: requires valid coordinates
        has_coords = (
            village.latitude is not None
            and village.longitude is not None
            and -90.0 <= float(village.latitude) <= 90.0
            and -180.0 <= float(village.longitude) <= 180.0
        )
        weather_avail = bool(has_coords)
        precip_forecast_avail = bool(has_coords)

        # 2. River monitoring capability: check proximity to known CWC gauges
        river_status = FreshnessStatus.UNAVAILABLE
        river_station = None

        if has_coords:
            v_lat = float(village.latitude)
            v_lon = float(village.longitude)
            for gid, ginfo in VERIFIED_CWC_GAUGES.items():
                d2 = (v_lat - ginfo["latitude"]) ** 2 + (v_lon - ginfo["longitude"]) ** 2
                if d2 < 0.25:  # Within ~50km
                    river_status = FreshnessStatus.VERIFIED_CACHE
                    river_station = ginfo["station_name"]
                    break

        # 3. Soil estimation: formula-based estimate from rainfall
        soil_type = DataType.DERIVED_ESTIMATE

        # 4. Terrain attributes: elevation and slope exist in DB record
        terrain_avail = (
            village.elevation is not None
            and village.slope is not None
        )

        # 5. Flood Risk ML Governance
        # Buxar (Bihar) or Gangetic plains locations MUST NOT proxy Himachal Pradesh model!
        state_norm = (village.state or "").strip().lower()
        district_norm = (village.district or "").strip().lower()

        ml_support = ModelSupport.UNSUPPORTED
        model_id = None
        model_region = None
        unsupported_reason = None

        if state_norm in self.SUPPORTED_ML_REGIONS:
            reg_info = self.SUPPORTED_ML_REGIONS[state_norm]
            ml_support = reg_info["status"]
            model_id = reg_info["model_id"]
            model_region = reg_info["model_region"]
        else:
            ml_support = ModelSupport.UNSUPPORTED
            model_id = None
            model_region = None
            unsupported_reason = (
                f"Validated flood-risk machine learning model unavailable for {village.state} "
                f"(district: {village.district}). Cross-regional model fallback is strictly prohibited."
            )

        return LocationCapability(
            village_id=village.id,
            village_name=village.name,
            district=village.district,
            state=village.state,
            latitude=float(village.latitude),
            longitude=float(village.longitude),
            weather_observation=weather_avail,
            precipitation_forecast=precip_forecast_avail,
            river_monitoring=river_status,
            river_station_name=river_station,
            soil_estimation=soil_type,
            terrain_attributes=terrain_avail,
            flood_risk_model=ml_support,
            model_id=model_id,
            model_region=model_region,
            target_region=model_region or state_norm,
            unsupported_reason=unsupported_reason,
        )


location_capability_service = LocationCapabilityService()
