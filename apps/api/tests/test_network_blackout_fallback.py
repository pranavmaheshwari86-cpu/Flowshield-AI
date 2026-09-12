"""
apps/api/tests/test_network_blackout_fallback.py
Unit test for network blackout graceful fallback in LiveTelemetryService (v2.4).
Simulates upstream provider failure and verifies system continues serving cached data without 500 errors.
"""

import pytest
from unittest.mock import patch
from app.services.live_telemetry_service import live_telemetry_service
from app.models.telemetry_sync_log import TelemetrySyncLog


def test_network_blackout_graceful_fallback(client, db_session):
    """
    Simulates a total Open-Meteo network outage.
    Verifies that POST /api/v1/telemetry/sync-live falls back to cached data,
    sets mode=DEGRADED, logs TelemetrySyncLog, and returns HTTP 200 without throwing 500.
    """
    # Mock open_meteo_provider.fetch to simulate upstream outage
    def mock_broken_fetch(targets):
        return {"error": "Connection refused: api.open-meteo.com unreachable (Blackout Simulation)"}

    live_telemetry_service.last_sync_time = None
    with patch.object(live_telemetry_service.tomorrow_provider, "fetch", side_effect=mock_broken_fetch), \
         patch.object(live_telemetry_service.open_meteo_provider, "fetch", side_effect=mock_broken_fetch), \
         patch.object(live_telemetry_service.open_weather_provider, "fetch", side_effect=mock_broken_fetch):
        response = client.post("/api/v1/telemetry/sync-live?force=true")

        # Must return 200 OK — zero unhandled 500 crashes
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "DEGRADED_CACHED_FALLBACK"
        assert data["mode"] == "DEGRADED"
        assert "Live upstream API unreachable" in data["message"]
        assert data["degraded_tier"] == 3

        # Verify TelemetrySyncLog recorded the event
        latest_log = (
            db_session.query(TelemetrySyncLog)
            .order_by(TelemetrySyncLog.timestamp.desc())
            .first()
        )
        assert latest_log is not None
        assert latest_log.status == "DEGRADED"
        assert "Connection refused" in latest_log.error_message
