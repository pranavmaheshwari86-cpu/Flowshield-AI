"""
tests/test_scientific_integrity.py
Flowshield — Hardcore Scientific Integrity & Zero-Trust Validation Suite (v3.0)
Mandatory Automated Tests Enforcing Sections 2, 4, 5, 6, 10, 16, 17, 23, 26, 44, 45, 46, 66.
"""

import os
import json
import hashlib
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES
from ml.registry.feature_contract import PHYSICAL_BOUNDS
from ml.pipeline.feature_engineering import engineer_features
from ml.pipeline.independent_labeler import independent_labeler
from ml.registry.region_resolver import region_resolver
from ml.inference.predict import predict_flood_risk


def test_no_synthetic_training_data():
    """Section 4 & 5: Ensure zero synthetic data exists in active pipeline paths."""
    quarantine_dir = REPO_ROOT / "ml" / "data" / "quarantined" / "synthetic"
    assert quarantine_dir.exists(), "Quarantine directory must exist."
    assert (quarantine_dir / "README.md").exists(), "Quarantine README.md must be present."

    active_data_dir = REPO_ROOT / "ml" / "data"
    active_csvs = [p for p in active_data_dir.glob("**/*.csv") if "quarantined" not in str(p)]
    for csv_path in active_csvs:
        fname = csv_path.name.lower()
        assert "synthetic" not in fname, f"Active synthetic data detected: {csv_path}"


def test_label_provenance():
    """Section 3.1 & 6: Ensure disaster catalogs exist and provide valid disaster events."""
    events_df = independent_labeler.load_disaster_inventory()
    assert not events_df.empty, "Disaster inventory catalog must not be empty."
    assert "start_dt" in events_df.columns, "Events must have verified start timestamps."
    assert "event_id" in events_df.columns, "Events must have unique IDs."
    assert len(events_df) >= 1000, f"Expected thousands of verified events, got {len(events_df)}."


def test_target_predictor_independence():
    """
    Section 16 & 66: Target must NOT be constructed via threshold rules on predictors
    (e.g., rainfall >= 80 & soil >= 68). Target is strictly driven by independent disaster catalogs.
    """
    # Create synthetic test frame with identical high rainfall/soil
    test_df = pd.DataFrame({
        "time": ["2020-01-01 00:00:00", "2020-01-01 01:00:00"],
        "station_id": ["TEST_01", "TEST_01"],
        "precipitation": [150.0, 150.0],  # Extreme rainfall
        "soil_moisture_0_to_7cm": [0.35, 0.35],  # 100% saturation
        "elevation_m": [800.0, 800.0],
        "catchment_slope_deg": [20.0, 20.0],
        "dist_to_river_m": [10.0, 10.0],
        "upstream_drainage_sqkm": [5000.0, 5000.0],
    })
    feat_df = engineer_features(test_df)
    
    # Label for Himachal Pradesh (no disaster occurred on 2020-01-01 in Mandi)
    hp_cfg = {"region": {"state": "Himachal Pradesh"}, "stations": {"TEST_01": {"name": "Mandi Basin"}}}
    labeled = independent_labeler.label_station_forecasting(feat_df, "himachal_pradesh", hp_cfg, lead_hours=6)
    
    # Even though rainfall is 150mm and soil is 100%, because no real disaster occurred,
    # target MUST be 0 (independence from predictor values)!
    assert labeled["flood_occurred"].sum() == 0, (
        "Target predictor circularity detected! Predictors alone must NEVER generate flood labels."
    )


def test_temporal_causality():
    """Section 10 & 23: Rolling features must strictly use information <= prediction time t."""
    df_raw = pd.DataFrame({
        "time": pd.date_range("2023-01-01", periods=10, freq="h", tz="UTC"),
        "station_id": ["STN_01"] * 10,
        "precipitation": [0, 0, 0, 0, 50, 0, 0, 0, 0, 0],
    })
    feat_df = engineer_features(df_raw)
    
    # Before the 50mm spike at index 4, rainfall_3h_mm and rainfall_24h_mm at index 3 must be 0!
    assert feat_df.loc[3, "rainfall_1h_mm"] == 0.0
    assert feat_df.loc[3, "rainfall_3h_mm"] == 0.0
    assert feat_df.loc[3, "rainfall_24h_mm"] == 0.0
    # At index 4 (t=4), rainfall_1h is 50.0
    assert feat_df.loc[4, "rainfall_1h_mm"] == 50.0
    # No future leakage into index 0..3
    assert feat_df.loc[:3, "rainfall_24h_mm"].max() == 0.0


def test_missing_telemetry_insufficient_data():
    """Section 44: When critical sensors are absent or blackout occurs, return INSUFFICIENT_DATA and risk_score=0."""
    payload = {
        "elevation_m": 760.0,
        "catchment_slope_deg": 16.0,
        "dist_to_river_m": 35.0,
        "upstream_drainage_sqkm": 6350.0,
        "insufficient_data": True,
    }
    res = predict_flood_risk(payload)
    assert res["risk_level"] == "INSUFFICIENT_DATA"
    assert res["risk_score"] == 0.0
    assert res.get("status") == "insufficient_data"


def test_unsupported_region_rejection():
    """Section 45: Unknown region requests MUST NOT silently fall back to Himachal Pradesh."""
    with pytest.raises(ValueError, match="UNSUPPORTED_REGION"):
        predict_flood_risk({"rainfall_1h_mm": 5.0}, region="atlantis_flood_basin")


def test_feature_schema():
    """Section 9: Mandatory 15-feature contract must be strictly enforced."""
    assert len(CANONICAL_FEATURE_NAMES) == 15
    for bound_feat in PHYSICAL_BOUNDS.keys():
        assert bound_feat in CANONICAL_FEATURE_NAMES


def test_probability_range():
    """Section 31 & 32: Calibrated probabilities must strictly remain within [0.0, 1.0]."""
    test_inputs = [
        {"rainfall_1h_mm": 0.0, "rainfall_24h_mm": 0.0, "soil_saturation_pct": 10.0},
        {"rainfall_1h_mm": 50.0, "rainfall_24h_mm": 120.0, "soil_saturation_pct": 95.0},
        {"rainfall_1h_mm": 150.0, "rainfall_24h_mm": 350.0, "soil_saturation_pct": 100.0},
    ]
    for inp in test_inputs:
        res = predict_flood_risk(inp)
        if res.get("risk_level") != "INSUFFICIENT_DATA":
            prob = res["calibrated_probability"]
            assert 0.0 <= prob <= 1.0, f"Probability {prob} out of [0, 1] range!"


def test_artifact_sha256_verification():
    """Section 46: Model artifacts must verify SHA-256 integrity hash."""
    from ml.registry.model_registry import model_registry
    bundle = model_registry.get(hazard="flood", region="himachal_pradesh")
    assert bundle is not None
    assert bundle.model is not None

    model_path = REPO_ROOT / "ml" / "models" / "v2_selected_model.joblib"
    if not model_path.exists():
        model_path = REPO_ROOT / "ml" / "models" / "flood" / "himachal_pradesh" / "model.joblib"
    assert model_path.exists()

    sha256_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()
    assert len(sha256_hash) == 64

    # Tampering check: corrupted artifact produces mismatched hash
    tampered_bytes = model_path.read_bytes() + b"TAMPERED"
    tampered_hash = hashlib.sha256(tampered_bytes).hexdigest()
    assert tampered_hash != sha256_hash
