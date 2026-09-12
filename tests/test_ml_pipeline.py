"""
tests/test_ml_pipeline.py
Flowshield — Comprehensive ML Pipeline Regression Suite
Smart India Hackathon 2026 (PS ID: 26192)
"""

import os
import sys
import copy
import pytest
import numpy as np

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES
from ml.inference.predict import predict_flood_risk, load_inference_artifacts, get_explainer
from apps.api.app.services.model_integrity import model_integrity_checker, ModelIntegrityState, EXPECTED_CHECKSUMS


@pytest.fixture(scope="module", autouse=True)
def ensure_artifacts():
    load_inference_artifacts()


def test_15_feature_inference_valid_vectors():
    """Test 15-feature inference returns strictly typed outputs and valid probabilities."""
    # Low-risk baseline vector
    low_risk_features = {
        "rainfall_1h_mm": 0.0,
        "rainfall_3h_mm": 0.0,
        "rainfall_6h_mm": 0.0,
        "rainfall_24h_mm": 0.5,
        "rainfall_72h_mm": 2.0,
        "soil_saturation_pct": 35.0,
        "deep_soil_saturation_pct": 40.0,
        "temperature_c": 18.0,
        "relative_humidity_pct": 55.0,
        "surface_pressure_hpa": 925.0,
        "wind_speed_kmh": 8.0,
        "elevation_m": 1200.0,
        "catchment_slope_deg": 18.0,
        "dist_to_river_m": 450.0,
        "upstream_drainage_sqkm": 800.0,
    }

    res_low = predict_flood_risk(low_risk_features)
    assert "calibrated_probability" in res_low
    assert "raw_probability" in res_low
    assert 0.0 <= res_low["calibrated_probability"] <= 1.0
    assert 0.0 <= res_low["raw_probability"] <= 1.0
    assert res_low["decision_threshold"] == 0.08
    assert res_low["calibrated_probability"] < 0.08
    assert res_low["threshold_exceeded"] is False
    assert len(res_low["top_contributing_factors"]) > 0

    # Severe cloudburst / flood trigger vector
    high_risk_features = {
        "rainfall_1h_mm": 85.0,
        "rainfall_3h_mm": 140.0,
        "rainfall_6h_mm": 210.0,
        "rainfall_24h_mm": 350.0,
        "rainfall_72h_mm": 520.0,
        "soil_saturation_pct": 98.0,
        "deep_soil_saturation_pct": 95.0,
        "temperature_c": 26.0,
        "relative_humidity_pct": 98.0,
        "surface_pressure_hpa": 905.0,
        "wind_speed_kmh": 45.0,
        "elevation_m": 720.0,
        "catchment_slope_deg": 38.0,
        "dist_to_river_m": 25.0,
        "upstream_drainage_sqkm": 6500.0,
    }

    res_high = predict_flood_risk(high_risk_features)
    assert res_high["calibrated_probability"] > res_low["calibrated_probability"]
    assert res_high["threshold_exceeded"] is True
    assert 0.0 <= float(res_high["confidence"]) <= 1.0


def test_missing_feature_imputation_graceful():
    """Test that missing/None/NaN features are imputed via training medians without failure."""
    partial_features = {
        "rainfall_1h_mm": 15.0,
        "rainfall_24h_mm": 80.0,
        "soil_saturation_pct": 75.0,
        # Other 12 features missing
    }

    res = predict_flood_risk(partial_features)
    assert 0.0 <= res["calibrated_probability"] <= 1.0
    assert isinstance(res["top_contributing_factors"], list)
    assert len(res["top_contributing_factors"]) > 0


def test_extreme_value_handling():
    """Test physical boundary conditions and extreme weather inputs."""
    extreme_features = {
        "rainfall_1h_mm": 300.0,
        "rainfall_3h_mm": 600.0,
        "rainfall_6h_mm": 900.0,
        "rainfall_24h_mm": 1500.0,
        "rainfall_72h_mm": 2500.0,
        "soil_saturation_pct": 100.0,
        "deep_soil_saturation_pct": 100.0,
        "temperature_c": 48.0,
        "relative_humidity_pct": 100.0,
        "surface_pressure_hpa": 1050.0,
        "wind_speed_kmh": 150.0,
        "elevation_m": 4500.0,
        "catchment_slope_deg": 65.0,
        "dist_to_river_m": 5.0,
        "upstream_drainage_sqkm": 20000.0,
    }

    res = predict_flood_risk(extreme_features)
    assert not np.isnan(res["calibrated_probability"])
    assert not np.isinf(res["calibrated_probability"])
    assert 0.0 <= res["calibrated_probability"] <= 1.0
    assert res["threshold_exceeded"] is True


def test_feature_attribution_determinism():
    """Test that identical input vectors produce strictly deterministic feature attributions."""
    test_vec = {
        "rainfall_1h_mm": 25.0,
        "rainfall_3h_mm": 45.0,
        "rainfall_6h_mm": 65.0,
        "rainfall_24h_mm": 110.0,
        "rainfall_72h_mm": 160.0,
        "soil_saturation_pct": 82.0,
        "deep_soil_saturation_pct": 78.0,
        "temperature_c": 21.0,
        "relative_humidity_pct": 88.0,
        "surface_pressure_hpa": 915.0,
        "wind_speed_kmh": 18.0,
        "elevation_m": 890.0,
        "catchment_slope_deg": 24.0,
        "dist_to_river_m": 60.0,
        "upstream_drainage_sqkm": 4200.0,
    }

    res1 = predict_flood_risk(test_vec)
    res2 = predict_flood_risk(test_vec)

    assert res1["calibrated_probability"] == res2["calibrated_probability"]
    assert res1["raw_probability"] == res2["raw_probability"]

    factors1 = res1["top_contributing_factors"]
    factors2 = res2["top_contributing_factors"]
    assert len(factors1) == len(factors2)
    for f1, f2 in zip(factors1, factors2):
        assert f1["feature"] == f2["feature"]
        assert f1["contribution"] == f2["contribution"]
        assert f1["direction"] == f2["direction"]
        assert f1["value"] == f2["value"]


def test_model_integrity_validation():
    """Test that ModelIntegrityChecker confirms MODEL_READY and rejects corrupted hashes."""
    # 1. Verification of promoted artifacts should pass
    state, details = model_integrity_checker.verify_integrity(enforce_checksums=True)
    assert state == ModelIntegrityState.MODEL_READY
    assert details["status"] == "ALL_CHECKS_PASSED"
    assert details["verified_features_count"] == 15

    # 2. Tampering simulation
    orig_hash = EXPECTED_CHECKSUMS["v2_selected_model.joblib"]
    try:
        EXPECTED_CHECKSUMS["v2_selected_model.joblib"] = "0000000000000000000000000000000000000000000000000000000000000000"
        bad_state, bad_details = model_integrity_checker.verify_integrity(enforce_checksums=True)
        assert bad_state == ModelIntegrityState.MODEL_ARTIFACT_INVALID
        assert any("Checksum mismatch" in err for err in bad_details["errors"])
    finally:
        # Restore valid hash
        EXPECTED_CHECKSUMS["v2_selected_model.joblib"] = orig_hash
        restored_state, _ = model_integrity_checker.verify_integrity(enforce_checksums=True)
        assert restored_state == ModelIntegrityState.MODEL_READY
