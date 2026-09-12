"""
apps/api/tests/test_freshness_evaluation.py
Unit tests for FreshnessService and 5-tier degradation transitions (v2.4).
"""

import pytest
from datetime import datetime, timezone, timedelta
from apps.api.app.services.freshness_service import (
    freshness_service,
    FreshnessState,
    DegradationTier,
)


def test_freshness_evaluation_lifecycle():
    """Verify transitions: FRESH (<30m) -> STALE (30m-24h) -> EXPIRED (>24h)."""
    now = datetime(2026, 9, 11, 12, 0, 0, tzinfo=timezone.utc)

    # 1. Fresh observation: 10 minutes ago
    obs_10m = now - timedelta(minutes=10)
    state, age, factor = freshness_service.evaluate_freshness(obs_10m, now=now)
    assert state == FreshnessState.FRESH
    assert age == 600
    assert 0.80 <= factor <= 1.0

    # 2. Stale observation: 90 minutes ago
    obs_90m = now - timedelta(minutes=90)
    state, age, factor = freshness_service.evaluate_freshness(obs_90m, now=now)
    assert state == FreshnessState.STALE
    assert age == 5400
    assert 0.10 <= factor <= 0.70

    # 3. Expired observation: 36 hours ago
    obs_36h = now - timedelta(hours=36)
    state, age, factor = freshness_service.evaluate_freshness(obs_36h, now=now)
    assert state == FreshnessState.EXPIRED
    assert age == 36 * 3600
    assert factor == 0.0

    # 4. None / missing observation
    state, age, factor = freshness_service.evaluate_freshness(None, now=now)
    assert state == FreshnessState.UNAVAILABLE
    assert factor == 0.0


def test_system_status_degradation_tier(client):
    """Verify GET /api/v1/telemetry/status reports degradation tier and cached observations."""
    response = client.get("/api/v1/telemetry/status")
    assert response.status_code == 200
    data = response.json()

    assert "degradation_tier" in data
    assert data["degradation_tier"] in [1, 2, 3, 4, 5]
    assert "freshness_state" in data
    assert "total_cached_observations" in data
    assert "system_status" in data
