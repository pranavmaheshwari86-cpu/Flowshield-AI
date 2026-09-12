"""Unit tests for Phase D: Location Capability Engine."""

import pytest
from apps.api.app.models.village import Village
from apps.api.app.services.location_capability_service import location_capability_service
from apps.api.app.schemas.data_types import ModelSupport, FreshnessStatus


def test_buxar_bihar_capabilities():
    """Verify Buxar retains weather, forecast, and CWC river, but rejects ML flood model."""
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

    cap = location_capability_service.evaluate_capabilities(buxar)

    # Core Architectural Assertion #5 & #10
    assert cap.weather_observation is True, "Weather must remain AVAILABLE for Buxar"
    assert cap.precipitation_forecast is True, "Precipitation forecast must remain AVAILABLE for Buxar"
    assert cap.river_monitoring == FreshnessStatus.VERIFIED_CACHE, "Buxar has verified CWC Ganga gauge"
    assert cap.river_station_name is not None
    assert "Buxar" in cap.river_station_name

    assert cap.flood_risk_model == ModelSupport.UNSUPPORTED, "Buxar must NEVER proxy Himachal Pradesh ML model"
    assert cap.model_id is None
    assert "unavailable for Bihar" in cap.unsupported_reason


def test_mandi_himachal_capabilities():
    """Verify Mandi (Himachal Pradesh) resolves to SUPPORTED with the trained model."""
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

    cap = location_capability_service.evaluate_capabilities(mandi)

    assert cap.weather_observation is True
    assert cap.precipitation_forecast is True
    assert cap.flood_risk_model == ModelSupport.SUPPORTED
    assert cap.model_id == "flood-risk-hp-lr-v2"
    assert cap.model_region == "himachal_pradesh"
    assert cap.unsupported_reason is None
