"""Unit tests for Phase A: Schemas, Data Contracts, and Taxonomy."""

import pytest
from datetime import datetime, timezone
from apps.api.app.schemas.data_types import (
    DataType,
    FreshnessStatus,
    ModelSupport,
    DataAvailability,
)
from apps.api.app.schemas.errors import ErrorCode, ServiceErrorDetail
from apps.api.app.schemas.provenance import DataProvenance, FreshnessMetadata
from apps.api.app.schemas.location_capability import LocationCapability
from apps.api.app.schemas.precipitation import PrecipitationPoint, PrecipitationForecastResponse


def test_data_type_taxonomy():
    """Verify all 7 authoritative data types exist and serialize as string values."""
    expected_types = {
        "OBSERVED",
        "FORECAST_NWP",
        "ML_PREDICTION",
        "DERIVED_ESTIMATE",
        "STATIC",
        "CACHED",
        "UNAVAILABLE",
    }
    actual_types = {dt.value for dt in DataType}
    assert expected_types == actual_types
    assert DataType.OBSERVED == "OBSERVED"
    assert DataType.FORECAST_NWP == "FORECAST_NWP"


def test_freshness_status_lifecycle():
    """Verify freshness status states: LIVE, RECENT, VERIFIED_CACHE, STALE, UNAVAILABLE."""
    expected_statuses = {"LIVE", "RECENT", "VERIFIED_CACHE", "STALE", "UNAVAILABLE"}
    actual_statuses = {fs.value for fs in FreshnessStatus}
    assert expected_statuses == actual_statuses


def test_model_support_enums():
    """Verify model support enums."""
    assert ModelSupport.SUPPORTED == "SUPPORTED"
    assert ModelSupport.UNSUPPORTED == "UNSUPPORTED"
    assert ModelSupport.VALIDATION_ONLY == "VALIDATION_ONLY"


def test_service_error_detail():
    """Verify ServiceErrorDetail validation."""
    err = ServiceErrorDetail(
        code=ErrorCode.MODEL_NOT_SUPPORTED_FOR_LOCATION,
        message="No validated ML model for Bihar Gangetic plains",
        location_id="bh-07-buxar",
    )
    assert err.code == ErrorCode.MODEL_NOT_SUPPORTED_FOR_LOCATION
    assert err.location_id == "bh-07-buxar"
    data = err.model_dump() if hasattr(err, "model_dump") else err.dict()
    assert data["code"] == "MODEL_NOT_SUPPORTED_FOR_LOCATION"


def test_data_provenance_derivation():
    """Verify provenance model with DERIVED_ESTIMATE and formula disclosure."""
    prov = DataProvenance(
        source="FlowShield Soil Saturation Estimator",
        freshness_status=FreshnessStatus.RECENT,
        data_type=DataType.DERIVED_ESTIMATE,
        is_live=False,
        derivation_formula="min(95, max(20, 48 + (rainfall_24h * 0.35)))",
    )
    assert prov.data_type == DataType.DERIVED_ESTIMATE
    assert prov.derivation_formula is not None
    assert "0.35" in prov.derivation_formula


def test_location_capability_buxar_vs_mandi():
    """Verify capability representation for Buxar (unsupported ML) and Mandi (supported ML)."""
    buxar = LocationCapability(
        village_id="bh-07-buxar",
        village_name="Buxar",
        district="Buxar",
        state="Bihar",
        latitude=25.5647,
        longitude=83.9777,
        weather_observation=True,
        precipitation_forecast=True,
        river_monitoring=FreshnessStatus.VERIFIED_CACHE,
        river_station_name="Buxar (CWC)",
        soil_estimation=DataType.DERIVED_ESTIMATE,
        terrain_attributes=True,
        flood_risk_model=ModelSupport.UNSUPPORTED,
        unsupported_reason="No validated ML model trained for Bihar Gangetic plains",
    )
    assert buxar.weather_observation is True
    assert buxar.precipitation_forecast is True
    assert buxar.flood_risk_model == ModelSupport.UNSUPPORTED
    assert buxar.model_id is None

    mandi = LocationCapability(
        village_id="hp-01-mandi",
        village_name="Mandi",
        district="Mandi",
        state="Himachal Pradesh",
        latitude=31.7087,
        longitude=76.9320,
        weather_observation=True,
        precipitation_forecast=True,
        river_monitoring=FreshnessStatus.LIVE,
        river_station_name="Mandi Gauge",
        soil_estimation=DataType.DERIVED_ESTIMATE,
        terrain_attributes=True,
        flood_risk_model=ModelSupport.SUPPORTED,
        model_id="flood-risk-hp-lr-v2",
        model_region="himachal_pradesh",
    )
    assert mandi.flood_risk_model == ModelSupport.SUPPORTED
    assert mandi.model_id == "flood-risk-hp-lr-v2"


def test_precipitation_point_and_forecast_response():
    """Verify precipitation forecast schemas with IST timestamps and null-safe rates."""
    now_utc = datetime.now(timezone.utc)
    pt1 = PrecipitationPoint(
        timestamp_utc=now_utc,
        timestamp_ist="2026-09-12 15:30 IST",
        relative_hour=0,
        value_mm_hr=0.0,  # Provider explicitly reported zero
        type=DataType.OBSERVED,
        source="OpenWeather",
        status="VALID",
    )
    pt2 = PrecipitationPoint(
        timestamp_utc=now_utc,
        timestamp_ist="2026-09-12 18:30 IST",
        relative_hour=3,
        value_mm_hr=4.2,
        type=DataType.FORECAST_NWP,
        source="Open-Meteo (ECMWF IFS)",
        status="VALID",
        forecast_lead_hours=3,
    )
    prov = DataProvenance(
        source="Open-Meteo ECMWF IFS",
        freshness_status=FreshnessStatus.LIVE,
        data_type=DataType.FORECAST_NWP,
        is_live=True,
    )
    response = PrecipitationForecastResponse(
        model_name="ECMWF IFS via Open-Meteo",
        model_run_utc=now_utc,
        model_run_ist="2026-09-12 11:30 IST",
        current_rate_mm_hr=0.0,
        observed_points=[pt1],
        forecast_points=[pt2],
        peak_forecast_mm_hr=4.2,
        peak_forecast_time_ist="2026-09-12 18:30 IST",
        accumulated_24h_forecast_mm=18.5,
        provenance=prov,
        freshness=FreshnessStatus.LIVE,
    )
    assert response.peak_forecast_mm_hr == 4.2
    assert len(response.forecast_points) == 1
    assert response.forecast_points[0].type == DataType.FORECAST_NWP
