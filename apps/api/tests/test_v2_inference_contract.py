"""
apps/api/tests/test_v2_inference_contract.py
Unit tests for Flowshield V2 inference contract and canonical 15 features (v2.4).
"""

import pytest
from apps.api.app.services.prediction_service import prediction_service


def test_v2_canonical_prediction_success():
    """Verify that canonical 15-feature input produces calibrated probability and threshold evaluation."""
    payload = {
        "rainfall_1h_mm": 55.0,
        "rainfall_3h_mm": 110.0,
        "rainfall_6h_mm": 160.0,
        "rainfall_24h_mm": 230.0,
        "rainfall_72h_mm": 350.0,
        "soil_saturation_pct": 88.0,
        "deep_soil_saturation_pct": 82.0,
        "temperature_c": 19.5,
        "relative_humidity_pct": 96.0,
        "surface_pressure_hpa": 920.0,
        "wind_speed_kmh": 28.0,
        "elevation_m": 720.0,
        "catchment_slope_deg": 32.0,
        "dist_to_river_m": 60.0,
        "upstream_drainage_sqkm": 5400.0,
        "vulnerability_index": 0.80,
    }

    res = prediction_service.predict_full(payload)

    assert "flood_probability" in res
    assert 0.0 <= res["flood_probability"] <= 1.0
    assert res["decision_threshold"] == 0.08
    assert isinstance(res["threshold_exceeded"], bool)
    assert res["model_integrity_status"] == "MODEL_READY"
    assert res["status"] == "operational_v2_validated"

    # High rainfall near river should exceed 0.08 threshold
    assert res["threshold_exceeded"] is True
    assert res["risk_level"] in ["HIGH", "CRITICAL"]

    # Check top contributing factors
    assert len(res["top_contributing_factors"]) > 0
    top = res["top_contributing_factors"][0]
    assert "feature" in top
    assert "contribution" in top
    assert top["direction"] == "increases_risk"


def test_v2_legacy_alias_mapping():
    """Verify that legacy parameter names (rainfall_1h, soil_moisture, distance_to_river) map cleanly."""
    legacy_payload = {
        "rainfall_1h": 65.0,
        "rainfall_3h": 120.0,
        "rainfall_6h": 180.0,
        "rainfall_24h": 260.0,
        "soil_moisture": 86.0,
        "elevation": 950.0,
        "slope": 28.0,
        "distance_to_river": 0.35,  # legacy km -> 350m
        "vulnerability_index": 0.65,
    }

    prob, quality, factors = prediction_service.predict(legacy_payload)

    assert 0.0 <= prob <= 1.0
    assert 0.0 <= quality <= 1.0
    assert len(factors) > 0


def test_v2_invalid_telemetry_trips_insufficient_data():
    """Verify that physically impossible inputs (negative rainfall, >100% soil) trip safety guardrails."""
    corrupt_payload = {
        "rainfall_1h_mm": -40.0,  # Impossible negative rainfall
        "soil_saturation_pct": 140.0,  # Impossible > 100%
    }

    res = prediction_service.predict_full(corrupt_payload)
    assert res["risk_level"] == "INSUFFICIENT_DATA"
    assert res["status"] == "insufficient_data"
    assert any("guardrail" in exp.lower() for exp in res["physical_explanations"])
