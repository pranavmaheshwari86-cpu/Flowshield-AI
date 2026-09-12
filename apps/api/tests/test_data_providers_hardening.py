"""Unit tests for Phase B: Data Provider Hardening and Fabrication Eradication."""

import pytest
from unittest.mock import patch, MagicMock
import urllib.error
from datetime import datetime, timezone

from apps.api.app.services.forecast_service import forecast_service
from apps.api.app.services.providers.cwc_gauge import CwcRiverGaugeProvider
from apps.api.app.services.providers.base import LocationTarget
from apps.api.app.models.village import Village


def test_forecast_service_returns_none_on_api_failure():
    """Verify forecast_service does NOT fabricate [0.0] * 48 on network failure."""
    village = Village(
        id="test-village-1",
        name="Test Village",
        latitude=31.70,
        longitude=76.93,
        district="Mandi",
        state="Himachal Pradesh",
        tehsil="Mandi",
        population=1000,
        elevation=1000.0,
        slope=10.0,
        distance_to_river=1.0,
        historical_flood_frequency=0.1,
        vulnerability_index=0.2,
    )
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Network unreachable")):
        projections = forecast_service._fetch_precipitation_projections(village, db=None)
        assert projections is None, "Failed API fetch must return None, not [0.0] * 48"

        response = forecast_service.get_multi_horizon_forecast(village, db=None)
        assert response.cumulative_48h_rainfall_mm is None
        assert response.peak_intensity_horizon_hours is None
        for h in response.horizons:
            assert h.projected_rainfall_mm is None
            assert h.rainfall_intensity_mm_hr is None
            assert h.uncertainty_state == "UNCERTAINTY_UNAVAILABLE"


def test_cwc_gauge_freshness_and_is_live_false():
    """Verify CWC provider honestly declares is_live: False and includes bulletin age."""
    provider = CwcRiverGaugeProvider()
    targets = [
        LocationTarget(
            id="bh-07-buxar",
            name="Buxar",
            latitude=25.5647,
            longitude=83.9777,
        )
    ]
    raw_payload = provider.fetch(targets)
    assert raw_payload["matched_gauges"]["bh-07-buxar"] is not None

    observations = provider.normalize(raw_payload, targets)
    assert len(observations) == 1
    obs = observations[0]
    meta = obs.metadata

    # Core assertions from architectural correction #4
    assert meta["is_live"] is False, "Cached CWC bulletin must NEVER be labeled as live telemetry"
    assert meta["freshness_status"] in ("VERIFIED_CACHE", "STALE")
    assert "bulletin_age_hours" in meta
    assert meta["bulletin_age_hours"] >= 0.0
    assert meta["river"] == "Ganga"
    assert meta["gauge_station"] == "Buxar CWC Station, Buxar"


def test_cwc_gauge_unmonitored_location():
    """Verify unmonitored location correctly returns UNAVAILABLE without fake stage."""
    provider = CwcRiverGaugeProvider()
    targets = [
        LocationTarget(
            id="hp-remote-mountain",
            name="Remote Mountain Village",
            latitude=32.80,
            longitude=77.50,
        )
    ]
    raw_payload = provider.fetch(targets)
    assert raw_payload["matched_gauges"]["hp-remote-mountain"] is None

    observations = provider.normalize(raw_payload, targets)
    obs = observations[0]
    assert obs.river_level_m is None
    assert obs.metadata["is_live"] is False
    assert obs.metadata["freshness_status"] == "UNAVAILABLE"
