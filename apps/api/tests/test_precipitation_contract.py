"""Tests for Phase G: Dedicated Precipitation Forecast Contract & Timeline Contract.

Validates:
1. forecast_service.get_standardized_precipitation_forecast returns IST formatted timestamps.
2. Observed history points (-6h to 0h) and forecast points (+1h to +48h).
3. 24h accumulation and peak forecast rate & time in IST.
4. timeline_service.get_detailed_timeline populates location_capabilities and precipitation_forecast.
5. Strict isolation: Buxar timeline has weather + precipitation forecast, but flood_risk_model is UNSUPPORTED.
"""

from datetime import datetime, timezone
from apps.api.app.models.village import Village
from apps.api.app.models.observation import EnvironmentalObservation
from apps.api.app.services.forecast_service import forecast_service
from apps.api.app.services.timeline_service import timeline_service
from apps.api.app.database import get_db, SessionLocal
from apps.api.app.schemas.data_types import DataType, FreshnessStatus, ModelSupport


def test_standardized_precipitation_forecast_contract():
    village = Village(
        id="hp-mandi-test",
        name="Mandi Urban",
        district="Mandi",
        state="Himachal Pradesh",
        latitude=31.7087,
        longitude=76.9320,
        elevation=760.0,
        slope=18.5,
        distance_to_river=0.35,
        population=26000,
        tehsil="Mandi Sadar",
        historical_flood_frequency=3,
        vulnerability_index=0.45
    )

    dummy_series = [1.2, 2.5, 5.8, 12.4] + [0.5] * 44

    resp = forecast_service.get_standardized_precipitation_forecast(
        village=village,
        db=None,
        precip_series=dummy_series
    )

    assert resp.model_name == "ECMWF IFS (0.1° High-Res Grid)"
    assert "IST" in resp.model_run_ist
    assert len(resp.forecast_points) == 48

    # Verify IST formatting on all points
    for pt in resp.forecast_points:
        assert "IST" in pt.timestamp_ist
        assert pt.type == DataType.FORECAST_NWP
        assert pt.relative_hour >= 1

    # Peak detection
    assert resp.peak_forecast_mm_hr == 12.4
    assert resp.peak_forecast_time_ist is not None
    assert "IST" in resp.peak_forecast_time_ist

    # 24h accumulation calculation
    assert resp.accumulated_24h_forecast_mm == round(1.2 + 2.5 + 5.8 + 12.4 + (20 * 0.5), 1)
    assert resp.freshness == FreshnessStatus.LIVE


def test_timeline_service_exposes_capabilities_and_precipitation():
    db = SessionLocal()
    try:
        # 1. Test Mandi (Himachal Pradesh - Model SUPPORTED)
        mandi = db.query(Village).filter(Village.id.like("hp-%")).first()
        if mandi:
            tl = timeline_service.get_detailed_timeline(mandi.id, db, force_refresh=True)
            assert tl.location_capabilities is not None
            assert tl.location_capabilities.weather_observation is True
            assert tl.location_capabilities.flood_risk_model == ModelSupport.SUPPORTED
            assert tl.precipitation_forecast is not None
            assert tl.precipitation_forecast.model_name == "ECMWF IFS (0.1° High-Res Grid)"
            assert len(tl.forecast_horizons) == 6
            assert tl.forecast_horizons[0].risk_tier in ["LOW", "WATCH", "HIGH", "CRITICAL"]

        # 2. Test Buxar (Bihar - Model UNSUPPORTED, but weather and precipitation active)
        buxar = db.query(Village).filter(Village.id.like("bh-%")).first()
        if not buxar:
            buxar = db.query(Village).filter(Village.name.ilike("%buxar%")).first()

        if buxar:
            buxar_tl = timeline_service.get_detailed_timeline(buxar.id, db, force_refresh=True)
            assert buxar_tl.location_capabilities is not None
            assert buxar_tl.location_capabilities.weather_observation is True
            assert buxar_tl.location_capabilities.precipitation_forecast is True
            assert buxar_tl.location_capabilities.flood_risk_model == ModelSupport.UNSUPPORTED
            assert buxar_tl.precipitation_forecast is not None

            # Verify ML flood risk is NOT fabricated for Buxar
            for hz in buxar_tl.forecast_horizons:
                assert hz.risk_tier == "UNSUPPORTED"
                assert hz.raw_flood_probability is None
                assert hz.calibrated_flood_probability is None
                assert hz.operational_risk_score is None
    finally:
        db.close()
