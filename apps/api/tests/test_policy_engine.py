"""
apps/api/tests/test_policy_engine.py
Unit tests for Operational Policy & Risk Engine (v2.4).
"""

import pytest
from apps.api.app.services.risk_engine import RiskEngine, risk_engine


def test_policy_engine_severity_mapping():
    """Verify operational risk level bands mapped from probability and policy score."""
    # Critical condition: high probability >= 0.50
    score, level, color, capped = risk_engine.compute_operational_risk(
        flood_probability=0.65,
        trend_factor=1.0,
        vulnerability_index=0.8,
    )
    assert level == "CRITICAL"
    assert color == "#ef4444"
    assert not capped

    # High condition: exceeds operational decision threshold tau=0.08
    score, level, color, capped = risk_engine.compute_operational_risk(
        flood_probability=0.12,
        trend_factor=1.0,
        vulnerability_index=0.5,
    )
    assert level == "HIGH"
    assert color == "#f97316"

    # Watch condition: 0.04 <= prob < 0.08
    score, level, color, capped = risk_engine.compute_operational_risk(
        flood_probability=0.05,
        trend_factor=1.0,
        vulnerability_index=0.3,
    )
    assert level == "WATCH"
    assert color == "#f59e0b"

    # Low condition: baseline
    score, level, color, capped = risk_engine.compute_operational_risk(
        flood_probability=0.01,
        trend_factor=1.0,
        vulnerability_index=0.2,
    )
    assert level == "LOW"
    assert color == "#10b981"


def test_policy_engine_data_quality_capping():
    """Verify that stale (>3600s) or low-quality data (<0.60) is capped at 55."""
    score, level, color, capped = risk_engine.compute_operational_risk(
        flood_probability=0.90,
        trend_factor=1.2,
        vulnerability_index=0.9,
        data_quality_score=0.45,  # Low quality
        freshness_seconds=5000,    # Stale
    )
    assert capped is True
    assert score <= 55


def test_policy_engine_trend_calculation():
    """Verify temporal trend slope calculation and multipliers."""
    # Rising trend
    mult, trend = risk_engine.calculate_trend_factor([40, 50, 62])
    assert trend == "RISING"
    assert mult == 1.20

    # Falling trend
    mult, trend = risk_engine.calculate_trend_factor([75, 65, 55])
    assert trend == "FALLING"
    assert mult == 0.85

    # Stable trend
    mult, trend = risk_engine.calculate_trend_factor([50, 52, 51])
    assert trend == "STABLE"
    assert mult == 1.00


def test_insufficient_data_guardrail():
    """Verify that corrupt data quality (<0.1) produces INSUFFICIENT_DATA."""
    score, level, color, capped = risk_engine.compute_operational_risk(
        flood_probability=0.50,
        data_quality_score=0.05,
    )
    assert level == "INSUFFICIENT_DATA"
    assert score == 0
    assert capped is True
