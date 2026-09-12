"""Unit tests for Phase F: Model Registry and Governance."""

import pytest
from apps.api.app.models.village import Village
from apps.api.app.services.model_registry import (
    model_registry_service,
    ModelGovernanceError,
    ErrorCode,
)
from apps.api.app.services.model_adapter import flood_prediction_adapter


def test_model_registry_location_support():
    """Verify Buxar (Bihar) is explicitly rejected and Mandi (Himachal) is supported."""
    buxar = Village(
        id="bh-07-buxar",
        name="Buxar",
        district="Buxar",
        state="Bihar",
        tehsil="Buxar",
        population=12000,
        elevation=58.0,
        slope=1.2,
        distance_to_river=0.3,
        historical_flood_frequency=0.4,
        vulnerability_index=0.6,
        latitude=25.5647,
        longitude=83.9777,
    )
    is_supp, region, reason = model_registry_service.is_location_supported(buxar)
    assert is_supp is False
    assert region is None
    assert "Bihar Gangetic plains" in reason

    with pytest.raises(ModelGovernanceError) as exc_info:
        model_registry_service.get_model_bundle_for_location(buxar)
    assert exc_info.value.code == ErrorCode.MODEL_NOT_SUPPORTED_FOR_LOCATION

    mandi = Village(
        id="hp-01-mandi",
        name="Mandi",
        district="Mandi",
        state="Himachal Pradesh",
        tehsil="Mandi",
        population=8000,
        elevation=760.0,
        slope=18.5,
        distance_to_river=0.5,
        historical_flood_frequency=0.7,
        vulnerability_index=0.5,
        latitude=31.7087,
        longitude=76.9320,
    )
    is_supp, region, reason = model_registry_service.is_location_supported(mandi)
    assert is_supp is True
    assert region == "himachal_pradesh"
    assert reason is None

    bundle = model_registry_service.get_model_bundle_for_location(mandi)
    assert bundle is not None
    assert bundle.threshold > 0.0


def test_model_adapter_buxar_isolation():
    """Verify flood_prediction_adapter rejects Buxar without running Himachal model."""
    buxar_features = {
        "village_id": "bh-07-buxar",
        "state": "Bihar",
        "location": {"elevation_m": 58.0, "catchment_slope_deg": 1.2, "dist_to_river_m": 300.0},
        "rainfall": {"current_mm_hr": 20.0, "accumulated_1h_mm": 20.0, "accumulated_24h_mm": 50.0},
        "forecast": {"rainfall_1h_mm": 10.0, "rainfall_3h_mm": 25.0},
        "soil": {"saturation_percent": 65.0},
    }

    result = flood_prediction_adapter.predict(buxar_features)

    # Core architectural assertion: Buxar must NOT return an ML probability from Himachal model
    assert result["status"] == "MODEL_NOT_SUPPORTED_FOR_LOCATION"
    assert result["overallRisk"] == "UNSUPPORTED"
    assert result["score"] is None
    assert "Cross-regional proxying is strictly prohibited" in result["reason"]
    assert result["horizons"]["1h"]["probability"] is None


def test_model_registry_overview_status():
    """Verify get_status_overview returns active operational model regions."""
    overview = model_registry_service.get_status_overview()
    assert overview["registry_version"] == "2.5.0-governed"
    assert overview["active_regions_count"] >= 1
    assert "himachal_pradesh" in overview["supported_regions"]
    assert overview["supported_regions"]["himachal_pradesh"]["status"] == "OPERATIONAL"
