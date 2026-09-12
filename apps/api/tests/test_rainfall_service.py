"""
apps/api/tests/test_rainfall_service.py
Automated test suite for Flowshield Real-Time Rainfall & Precipitation Service
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.services.providers.rainfall_provider import (
    compute_rainfall_severity,
    RAINFALL_THRESHOLDS,
    RainfallReading,
    RainfallProvider,
    OpenMeteoRainfallProvider,
)
from app.services.rainfall_service import RainfallService
from app.services.providers.base import LocationTarget

client = TestClient(app)


class MockFailingProvider(RainfallProvider):
    @property
    def name(self) -> str:
        return "Mock Failing Provider"

    def get_provider_status(self):
        return {"status": "OFFLINE"}

    def get_current_rainfall(self, targets):
        return [], "Simulated network timeout or upstream 503 error"


class MockDeterministicProvider(RainfallProvider):
    @property
    def name(self) -> str:
        return "Mock Deterministic Provider"

    def get_provider_status(self):
        return {"status": "OPERATIONAL"}

    def get_current_rainfall(self, targets):
        now_iso = datetime.now(timezone.utc).isoformat()
        readings = [
            RainfallReading(
                id="station_dry",
                name="Dry Station",
                lat=28.0,
                lon=77.0,
                rainfallMmPerHour=0.0,
                severity="none",
                timestamp=now_iso,
                source=self.name,
                quality="live",
            ),
            RainfallReading(
                id="station_light",
                name="Light Rain Station",
                lat=28.5,
                lon=77.5,
                rainfallMmPerHour=1.2,
                severity="green",
                timestamp=now_iso,
                source=self.name,
                quality="live",
            ),
            RainfallReading(
                id="station_moderate",
                name="Moderate Rain Station",
                lat=25.0,
                lon=85.0,
                rainfallMmPerHour=5.0,
                rainfall_24h_mm=30.0,
                severity="yellow",
                timestamp=now_iso,
                source=self.name,
                quality="live",
            ),
            RainfallReading(
                id="station_heavy",
                name="Heavy Rain Station",
                lat=26.0,
                lon=91.0,
                rainfallMmPerHour=28.0,
                rainfall_24h_mm=150.0,
                severity="red",
                timestamp=now_iso,
                source=self.name,
                quality="live",
            ),
        ]
        return readings, None


def test_rainfall_threshold_classification():
    """Validates exact five-tier IMD boundary classification rules."""
    # 0 mm/h -> none
    assert compute_rainfall_severity(0.0, 0.0) == "none"
    assert compute_rainfall_severity(0.05, 0.0) == "none"

    # Green boundaries (Very light to light): 0.1 to 15.5 mm (or 0.1 to 2.4 mm/h)
    assert compute_rainfall_severity(0.1, 0.0) == "green"
    assert compute_rainfall_severity(1.0, 5.0) == "green"
    assert compute_rainfall_severity(2.4, 15.5) == "green"

    # Yellow boundaries (Moderate): 15.6 to 64.4 mm (or 2.5 to 7.4 mm/h)
    assert compute_rainfall_severity(2.5, 0.0) == "yellow"
    assert compute_rainfall_severity(5.0, 30.0) == "yellow"
    assert compute_rainfall_severity(7.4, 64.4) == "yellow"

    # Orange boundaries (Heavy): 64.5 to 115.5 mm (or 7.5 to 15.5 mm/h)
    assert compute_rainfall_severity(7.5, 0.0) == "orange"
    assert compute_rainfall_severity(10.0, 80.0) == "orange"
    assert compute_rainfall_severity(15.5, 115.5) == "orange"

    # Red boundaries (Very Heavy): 115.6 to 204.4 mm (or 15.6 to 29.9 mm/h)
    assert compute_rainfall_severity(15.6, 0.0) == "red"
    assert compute_rainfall_severity(20.0, 150.0) == "red"
    assert compute_rainfall_severity(29.9, 204.4) == "red"

    # Purple boundaries (Extremely Heavy): > 204.4 mm (or >= 30.0 mm/h)
    assert compute_rainfall_severity(30.0, 0.0) == "purple"
    assert compute_rainfall_severity(0.0, 204.5) == "purple"
    assert compute_rainfall_severity(50.0, 250.0) == "purple"


def test_zero_rainfall_filtering():
    """Asserts that zero-rainfall locations are excluded when active_only=True."""
    service = RainfallService(provider=MockDeterministicProvider())
    report = service.get_live_rainfall(active_only=True, force_refresh=True)

    assert report["success"] is True
    assert report["status"] == "live"
    assert "mm" in report["units"]
    assert report["total_monitored_points"] == 4
    assert report["active_rainfall_points_count"] == 3

    # Ensure dry station is not in data
    ids = [d["id"] for d in report["data"]]
    assert "station_dry" not in ids
    assert "station_light" in ids
    assert "station_moderate" in ids
    assert "station_heavy" in ids

    # When active_only=False, all 4 must be present
    all_report = service.get_live_rainfall(active_only=False, force_refresh=False)
    assert len(all_report["data"]) == 4


def test_stale_cache_degradation():
    """Validates that a recent cache is served with quality='stale' on upstream failure."""
    service = RainfallService(provider=MockDeterministicProvider(), cache_ttl_seconds=10)
    # First fetch succeeds and populates cache
    service.get_live_rainfall(force_refresh=True)
    assert service._cached_readings is not None

    # Now simulate upstream failure
    service.provider = MockFailingProvider()
    # Age the cache past TTL but within stale window (e.g. 15 seconds old, TTL=10s, stale threshold=3600s)
    service._last_fetch_time = datetime.now(timezone.utc) - timedelta(seconds=15)

    report = service.get_live_rainfall(force_refresh=False)
    assert report["status"] == "stale"
    assert report["success"] is True
    assert len(report["data"]) == 3
    for pt in report["data"]:
        assert pt["quality"] == "stale"


def test_unavailable_cache_degradation():
    """Validates that if upstream fails and no recent cache exists, returns UNAVAILABLE without 500 crash."""
    service = RainfallService(provider=MockFailingProvider())
    report = service.get_live_rainfall(force_refresh=True)

    assert report["status"] == "unavailable"
    assert report["success"] is False
    assert len(report["data"]) == 0
    assert report["error"] is not None


def test_rainfall_api_endpoints():
    """Validates GET /api/v1/rainfall/current and /status contracts."""
    from app.services.rainfall_service import rainfall_service
    orig = rainfall_service.provider
    orig_sec = getattr(rainfall_service, "secondary_provider", None)
    rainfall_service.provider = MockDeterministicProvider()
    rainfall_service.secondary_provider = None
    try:
        resp = client.get("/api/v1/rainfall/current")
        assert resp.status_code == 200
        data = resp.json()

        assert "status" in data
        assert "units" in data
        assert "mm" in data["units"]
        assert "source" in data
        assert "thresholds" in data
        assert "data" in data
        assert isinstance(data["data"], list)

        status_resp = client.get("/api/v1/rainfall/status")
        assert status_resp.status_code == 200
        sdata = status_resp.json()
        assert "active_provider" in sdata
        assert "cache_ttl_seconds" in sdata
    finally:
        rainfall_service.provider = orig
        rainfall_service.secondary_provider = orig_sec
