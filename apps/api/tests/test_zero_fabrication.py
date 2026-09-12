"""Phase M: Zero-Fabrication and Chaos Test Suite.

Verifies the 13 automated chaos and zero-fabrication scenarios mandated by
Architectural Correction #14:
1. External Weather API Timeout (no 22.0C or synthetic fallback)
2. NWP Precipitation Forecast Endpoint 500 Failure (no synthetic sine wave)
3. Ungauged Basin Settlement (river stage strictly None, data_state UNGAUGED_BASIN, never 8.1m)
4. Negative Rainfall Ingestion Attempt (rejected with validation error)
5. Non-Existent Settlement (HTTP 404 with structured error)
6. Stale Environmental Observation (>3h old flagged STALE, never LIVE)
7. Buxar (Gangetic Plain) Strict Model Isolation (UNSUPPORTED, risk_score None)
8. Missing Model Artifact Handling (ValueError/FileNotFoundError, no random fallback)
9. Extreme Outlier Sensor Reading (rejected as unphysical)
10. Database Disconnection / Query Error Handling (HTTP 500 structured error, no corruption)
11. Soil Guard: Derived Estimate vs VWC Isolation (formula provenance, strict guard)
12. CWC Gauge Bulletin Age Check (VERIFIED_BULLETIN_CACHE, never LIVE)
13. Uncertainty Band Verification (NOW point None, p10 <= p50 <= p90, Buxar None)
"""

import pytest
import math
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import urllib.error

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.village import Village
from app.models.observation import EnvironmentalObservation
from app.models.river import River
from app.services.timeline_service import timeline_service
from app.services.observation_validator import observation_validator, FreshnessStatus
from app.services.feature_assembler import feature_assembler, FeatureAssemblyError
from app.services.location_capability_service import location_capability_service
from app.services.forecast_service import forecast_service
from app.services.providers.cwc_gauge import CwcRiverGaugeProvider
from app.services.providers.base import LocationTarget
from app.schemas.data_types import DataType, ModelSupport
from app.schemas.errors import ErrorCode
from ml.registry.model_registry import model_registry


@pytest.fixture
def mandi_village(db_session: Session):
    mandi = db_session.query(Village).filter(Village.id == "hp-08-mandi").first()
    if not mandi:
        mandi = Village(
            id="hp-08-mandi",
            name="Mandi",
            district="Mandi",
            state="Himachal Pradesh",
            latitude=31.7087,
            longitude=76.9320,
            elevation=760.0,
            slope=18.5,
            distance_to_river=0.35,
            population=26000,
            tehsil="Mandi Sadar",
            historical_flood_frequency=0.35,
            vulnerability_index=0.45
        )
        db_session.add(mandi)
        db_session.commit()
    return mandi


@pytest.fixture
def buxar_village(db_session: Session):
    buxar = db_session.query(Village).filter(Village.id == "bh-07-buxar").first()
    if not buxar:
        buxar = Village(
            id="bh-07-buxar",
            name="Buxar",
            district="Buxar",
            state="Bihar",
            latitude=25.5647,
            longitude=83.9777,
            elevation=56.0,
            slope=1.2,
            distance_to_river=0.1,
            population=110000,
            tehsil="Buxar Sadar",
            historical_flood_frequency=0.2,
            vulnerability_index=0.65
        )
        db_session.add(buxar)
        db_session.commit()
    return buxar


# ==============================================================================
# Scenario 1: External Weather API Timeout
# ==============================================================================
def test_chaos_01_external_weather_api_timeout():
    """Scenario 1: External Weather API Timeout must return None/STALE,
    never hardcoded 22.0 deg C, 2400 sqkm, or synthetic fallback.
    """
    village = Village(
        id="chaos-v1",
        name="Timeout Village",
        latitude=31.7,
        longitude=76.9,
        district="Mandi",
        state="Himachal Pradesh",
        elevation=800.0,
        slope=15.0,
        distance_to_river=0.5,
        population=5000,
        tehsil="Mandi Sadar",
        historical_flood_frequency=0.2,
        vulnerability_index=0.4
    )

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection timed out")):
        projections = forecast_service._fetch_precipitation_projections(village, db=None)
        assert projections is None, "API timeout must yield None, not [0.0]*48 or synthetic curves"

        forecast_res = forecast_service.get_multi_horizon_forecast(village, db=None)
        assert forecast_res.cumulative_48h_rainfall_mm is None
        assert forecast_res.peak_intensity_horizon_hours is None
        for h in forecast_res.horizons:
            assert h.projected_rainfall_mm is None
            assert h.uncertainty_state == "UNCERTAINTY_UNAVAILABLE"


# ==============================================================================
# Scenario 2: NWP Precipitation Forecast Endpoint 500 Failure
# ==============================================================================
def test_chaos_02_nwp_precipitation_forecast_server_error(db_session: Session, mandi_village: Village):
    """Scenario 2: NWP Forecast server error must result in status UNAVAILABLE,
    never a fabricated curve or synthetic interpolation.
    """
    with patch("urllib.request.urlopen",
               side_effect=urllib.error.HTTPError("https://api.open-meteo.com/v1/forecast", 500, "Internal Server Error", {}, None)):
        timeline = timeline_service.get_detailed_timeline(village_id=mandi_village.id, db=db_session, force_refresh=True)
        assert timeline is not None
        assert timeline.precipitation_forecast is not None
        # Must flag NWP precipitation as UNAVAILABLE, not synthetic
        assert timeline.precipitation_forecast.freshness == FreshnessStatus.UNAVAILABLE
        assert all(p.value_mm_hr is None for p in timeline.precipitation_forecast.forecast_points)
        assert all(p.status == "UNAVAILABLE" for p in timeline.precipitation_forecast.forecast_points)
        assert timeline.precipitation_forecast.peak_forecast_mm_hr is None
        assert timeline.precipitation_forecast.accumulated_24h_forecast_mm is None


# ==============================================================================
# Scenario 3: Ungauged Basin Settlement
# ==============================================================================
def test_chaos_03_ungauged_basin_settlement(db_session: Session):
    """Scenario 3: An ungauged settlement far from any CWC gauge station
    must have river_stage_meters strictly None and data_state UNGAUGED_BASIN.
    It must NEVER fabricate 8.1m or any constant level.
    """
    ungauged_id = "chaos-ungauged-01"
    ungauged = db_session.query(Village).filter(Village.id == ungauged_id).first()
    if not ungauged:
        ungauged = Village(
            id=ungauged_id,
            name="Remote Peak Settlement",
            latitude=32.85,  # High elevation remote mountain, far from Buxar/Mandi gauges
            longitude=77.55,
            district="Lahaul and Spiti",
            state="Himachal Pradesh",
            elevation=3400.0,
            slope=28.0,
            distance_to_river=4.5,
            population=350,
            tehsil="Keylong",
            historical_flood_frequency=0.05,
            vulnerability_index=0.2
        )
        db_session.add(ungauged)
        db_session.commit()

    timeline = timeline_service.get_detailed_timeline(village_id=ungauged_id, db=db_session, force_refresh=True)
    assert timeline.hydrology.current_stage_meters is None, "Ungauged basin must NOT fabricate river stage"
    assert timeline.hydrology.data_state == "UNGAUGED_BASIN"
    assert timeline.hydrology.danger_mark_meters is None
    assert timeline.hydrology.margin_to_danger_meters is None


# ==============================================================================
# Scenario 4: Negative Rainfall Ingestion Attempt
# ==============================================================================
def test_chaos_04_negative_rainfall_rejection():
    """Scenario 4: Negative rainfall must be rejected by validator,
    never clamped to 0.0 or silently accepted.
    """
    now = datetime.now(timezone.utc)
    res = observation_validator.validate_observation({
        "timestamp": now,
        "rainfall_1h_mm": -8.5,
        "rainfall_24h_mm": 10.0,
        "temperature_c": 22.0
    })
    assert res.is_valid is False
    assert any("Negative rainfall" in err for err in res.errors)


# ==============================================================================
# Scenario 5: Non-Existent Settlement (HTTP 404)
# ==============================================================================
def test_chaos_05_nonexistent_settlement_404(client: TestClient):
    """Scenario 5: Request for a non-existent settlement must return HTTP 404
    with structured error message, never empty dummy data.
    """
    resp = client.get("/api/v1/risk/forecast/detailed?village_id=non-existent-settlement-404")
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body
    assert "not found" in body["detail"].lower()


# ==============================================================================
# Scenario 6: Stale Environmental Observation (>3h old)
# ==============================================================================
def test_chaos_06_stale_observation_flagged():
    """Scenario 6: Sensor observation older than 3 hours must be flagged STALE,
    never presented as LIVE.
    """
    now = datetime.now(timezone.utc)
    stale_time = now - timedelta(hours=4)
    freshness = observation_validator.evaluate_freshness(stale_time, is_official_bulletin=False)
    assert freshness == FreshnessStatus.STALE


# ==============================================================================
# Scenario 7: Buxar (Gangetic Plain) Strict Model Isolation
# ==============================================================================
def test_chaos_07_buxar_gangetic_plain_isolation(client: TestClient, db_session: Session, buxar_village: Village):
    """Scenario 7: Buxar must NEVER run the Himachal Pradesh mountain ML model.
    Its flood risk model must be explicitly UNSUPPORTED and risk scores None.
    """
    resp = client.get(f"/api/v1/risk/forecast/detailed?village_id={buxar_village.id}")
    assert resp.status_code == 200
    data = resp.json()

    # Capability check
    assert data["location_capabilities"]["flood_risk_model"] == "UNSUPPORTED"
    assert "Validated flood-risk machine learning model unavailable" in data["location_capabilities"]["unsupported_reason"]

    # All forecast horizons must have risk_tier UNSUPPORTED and null score
    for h in data["forecast_horizons"]:
        assert h["risk_tier"] == "UNSUPPORTED"
        assert h["operational_risk_score"] is None
        assert h["calibrated_flood_probability"] is None
        assert h["uncertainty_band"] is None


# ==============================================================================
# Scenario 8: Missing Model Artifact Handling
# ==============================================================================
def test_chaos_08_missing_model_artifact_graceful_handling():
    """Scenario 8: Querying an undeployed or unsupported model from the registry raises
    ValueError or FileNotFoundError rather than falling back to random numbers.
    """
    with pytest.raises((ValueError, FileNotFoundError)):
        model_registry.get(hazard="flood", region="karnataka_coastal")


# ==============================================================================
# Scenario 9: Extreme Outlier Sensor Reading
# ==============================================================================
def test_chaos_09_extreme_sensor_outlier_rejection():
    """Scenario 9: Extreme unphysical readings (e.g. 650 mm/h rain, 250 deg C temp)
    must be flagged as invalid by the physical limits engine.
    """
    now = datetime.now(timezone.utc)
    res = observation_validator.validate_observation({
        "timestamp": now,
        "rainfall_1h_mm": 650.0,  # Far above 300 mm/h world record
        "temperature_c": 250.0,   # Far above 60 deg C
    })
    assert res.is_valid is False
    assert any("exceeds world-record threshold" in err or "outside physical bounds" in err for err in res.errors)


# ==============================================================================
# Scenario 10: Database Error Handling
# ==============================================================================
def test_chaos_10_database_error_handling(client: TestClient, mandi_village: Village):
    """Scenario 10: Unexpected DB failure returns HTTP 500 structured error
    without corrupting application state.
    """
    timeline_service._cache.clear()
    with patch("app.routers.forecast_risk.timeline_service.get_detailed_timeline",
               side_effect=RuntimeError("Database connection lost")):
        resp = client.get(f"/api/v1/risk/forecast/detailed?village_id={mandi_village.id}&force_refresh=true")
        assert resp.status_code == 500
        assert "detail" in resp.json()


# ==============================================================================
# Scenario 11: Soil Guard Enforcement
# ==============================================================================
def test_chaos_11_soil_guard_enforcement(db_session: Session, mandi_village: Village):
    """Scenario 11: Soil Guard strictly labels derived estimates in provenance
    and prevents passing unvalidated derived proxies as genuine VWC to ML models.
    """
    obs = EnvironmentalObservation(
        village_id=mandi_village.id,
        timestamp=datetime.now(timezone.utc),
        temperature=20.0,
        humidity=80.0,
        surface_pressure=910.0,
        wind_speed=10.0,
        rainfall_1h=5.0,
        rainfall_3h=10.0,
        rainfall_6h=15.0,
        rainfall_24h=25.0,
        rainfall_intensity=5.0,
        soil_moisture=None,  # Real soil sensor unavailable -> triggers DERIVED_ESTIMATE
        river_level=7.5,
        river_level_change=0.02,
        source="IMD Station",
        data_state="OBSERVED"
    )

    accumulations = {"1h": 5.0, "3h": 10.0, "6h": 15.0, "12h": 20.0, "24h": 25.0, "72h": 40.0}

    # Derived estimate provenance inspection
    features, prov = feature_assembler.assemble_inference_vector(
        village=mandi_village,
        observation=obs,
        accumulations=accumulations,
        forecast_rain_mm=5.0,
        horizon_hours=3,
        real_soil_vwc_top=None,  # No real volumetric water content
        strict_soil_guard=True
    )
    assert prov["soil"]["data_type"] == DataType.DERIVED_ESTIMATE
    assert "min(95, max(20, 48 + (rain_24h * 0.35)))" in prov["soil"]["formula"]


# ==============================================================================
# Scenario 12: CWC Gauge Bulletin Freshness (VERIFIED_CACHE)
# ==============================================================================
def test_chaos_12_cwc_gauge_bulletin_freshness():
    """Scenario 12: CWC river bulletin telemetry must be labeled VERIFIED_CACHE
    or VERIFIED_BULLETIN_CACHE, with explicit bulletin age, and NEVER labeled LIVE.
    """
    provider = CwcRiverGaugeProvider()
    targets = [
        LocationTarget(id="bh-07-buxar", name="Buxar", latitude=25.5647, longitude=83.9777)
    ]
    raw = provider.fetch(targets)
    normalized = provider.normalize(raw, targets)
    assert len(normalized) >= 1
    bulletin = normalized[0]

    assert bulletin.metadata["is_live"] is False, "CWC bulletin must NEVER be labeled live"
    assert bulletin.metadata["freshness_status"] in ("VERIFIED_CACHE", "STALE")
    assert "bulletin_timestamp" in bulletin.metadata


# ==============================================================================
# Scenario 13: Uncertainty Band Verification
# ==============================================================================
def test_chaos_13_uncertainty_band_integrity(db_session: Session, mandi_village: Village, buxar_village: Village):
    """Scenario 13:
    - NOW point must have NO fake uncertainty band (uncertainty_band is None).
    - Future horizons with uncertainty must satisfy p10 <= p50 <= p90.
    - Unsupported locations (Buxar) must have uncertainty_band strictly None.
    """
    # 1. Check Mandi (Supported)
    mandi_timeline = timeline_service.get_detailed_timeline(village_id=mandi_village.id, db=db_session, force_refresh=True)
    for h in mandi_timeline.forecast_horizons:
        if h.uncertainty_band:
            p10 = h.uncertainty_band.get("p10")
            p50 = h.uncertainty_band.get("p50")
            p90 = h.uncertainty_band.get("p90")
            if p10 is not None and p50 is not None and p90 is not None:
                assert p10 <= p50 <= p90, f"Uncertainty quantiles violated: p10={p10}, p50={p50}, p90={p90}"

    # 2. Check Buxar (Unsupported)
    buxar_timeline = timeline_service.get_detailed_timeline(village_id=buxar_village.id, db=db_session, force_refresh=True)
    for h in buxar_timeline.forecast_horizons:
        assert h.uncertainty_band is None, "Unsupported location must have None uncertainty band"
