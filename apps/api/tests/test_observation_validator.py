"""Unit tests for Phase C: Observation Validator and Freshness Engine."""

import math
import pytest
from datetime import datetime, timezone, timedelta
from apps.api.app.services.observation_validator import (
    observation_validator,
    PhysicalLimits,
    FreshnessStatus,
)


def test_validate_coordinates():
    """Verify coordinate bounds [-90, 90] and [-180, 180]."""
    valid, err = observation_validator.validate_coordinates(31.70, 76.93)
    assert valid is True
    assert err is None

    # Out of bounds
    valid, err = observation_validator.validate_coordinates(91.0, 76.93)
    assert valid is False
    assert "Latitude 91.0 out of bounds" in err

    valid, err = observation_validator.validate_coordinates(31.70, -181.0)
    assert valid is False
    assert "Longitude -181.0 out of bounds" in err

    # NaN / Inf
    valid, err = observation_validator.validate_coordinates(float("nan"), 76.93)
    assert valid is False


def test_evaluate_freshness_lifecycle():
    """Verify temporal freshness states."""
    now = datetime.now(timezone.utc)

    # 15 minutes ago -> LIVE for sensor
    assert observation_validator.evaluate_freshness(now - timedelta(minutes=15), is_official_bulletin=False) == FreshnessStatus.LIVE

    # 2 hours ago -> RECENT for sensor
    assert observation_validator.evaluate_freshness(now - timedelta(hours=2), is_official_bulletin=False) == FreshnessStatus.RECENT

    # 4 hours ago -> STALE for sensor
    assert observation_validator.evaluate_freshness(now - timedelta(hours=4), is_official_bulletin=False) == FreshnessStatus.STALE

    # 4 hours ago -> VERIFIED_CACHE for official bulletin (< 24h)
    assert observation_validator.evaluate_freshness(now - timedelta(hours=4), is_official_bulletin=True) == FreshnessStatus.VERIFIED_CACHE

    # 30 hours ago -> STALE for bulletin (> 24h)
    assert observation_validator.evaluate_freshness(now - timedelta(hours=30), is_official_bulletin=True) == FreshnessStatus.STALE

    # None -> UNAVAILABLE
    assert observation_validator.evaluate_freshness(None) == FreshnessStatus.UNAVAILABLE


def test_reject_unphysical_measurements():
    """Verify rejection of unphysical values: negative rainfall, out-of-range temp/humidity, NaN/Inf."""
    now = datetime.now(timezone.utc)

    # Negative rainfall
    res = observation_validator.validate_observation({
        "timestamp": now,
        "rainfall_1h_mm": -2.5,
        "temperature_c": 25.0,
    })
    assert res.is_valid is False
    assert any("Negative rainfall" in e for e in res.errors)

    # Extreme temperature
    res = observation_validator.validate_observation({
        "timestamp": now,
        "rainfall_1h_mm": 5.0,
        "temperature_c": 85.0,  # Unphysical
    })
    assert res.is_valid is False
    assert any("Temperature 85.0°C outside physical bounds" in e for e in res.errors)

    # Humidity > 100%
    res = observation_validator.validate_observation({
        "timestamp": now,
        "humidity": 120.0,
    })
    assert res.is_valid is False
    assert any("Humidity 120.0% outside" in e for e in res.errors)

    # NaN value
    res = observation_validator.validate_observation({
        "timestamp": now,
        "rainfall_1h_mm": float("nan"),
    })
    assert res.is_valid is False
    assert any("NaN" in e for e in res.errors)


def test_future_timestamp_rejection():
    """Verify rejection of timestamps in the future (> 10 mins)."""
    now = datetime.now(timezone.utc)
    future_ts = now + timedelta(hours=2)

    res = observation_validator.validate_observation({
        "timestamp": future_ts,
        "rainfall_1h_mm": 0.0,
    })
    assert res.is_valid is False
    assert any("Future timestamp rejected" in e for e in res.errors)


def test_deduplicate_and_sort_timeseries():
    """Verify deduplication of identical timestamps and chronological sorting."""
    now = datetime.now(timezone.utc)
    t1 = now - timedelta(hours=3)
    t2 = now - timedelta(hours=2)
    t3 = now - timedelta(hours=1)

    points = [
        {"timestamp": t2, "val": 2},
        {"timestamp": t1, "val": 1},
        {"timestamp": t2, "val": "2_duplicate"},
        {"timestamp": t3, "val": 3},
    ]

    deduped = observation_validator.deduplicate_and_sort_timeseries(points)
    assert len(deduped) == 3
    assert deduped[0]["timestamp"] == t1
    assert deduped[1]["timestamp"] == t2
    assert deduped[2]["timestamp"] == t3
