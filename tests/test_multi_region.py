"""
tests/test_multi_region.py
Flowshield — Multi-Region Model Registry, Inference & API Integration Test Suite
Validates all 10 regional ML pipelines, calibration, thresholds, fallback routing, and endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from ml.registry.region_resolver import ALL_REGIONS, region_resolver
from ml.registry.model_registry import model_registry
from ml.inference.predict import predict_flood_risk, predict_flood_risk_regional
from apps.api.app.services.model_adapter import flood_prediction_adapter
from apps.api.app.main import app

client = TestClient(app)

# Sample canonical test vectors
LOW_RISK_INPUT = {
    "rainfall_1h_mm": 0.0,
    "rainfall_3h_mm": 0.0,
    "rainfall_6h_mm": 0.5,
    "rainfall_24h_mm": 2.0,
    "rainfall_72h_mm": 5.0,
    "soil_saturation_pct": 30.0,
    "deep_soil_saturation_pct": 35.0,
    "temperature_c": 18.0,
    "relative_humidity_pct": 50.0,
    "surface_pressure_hpa": 925.0,
    "wind_speed_kmh": 8.0,
    "elevation_m": 1200.0,
    "catchment_slope_deg": 15.0,
    "dist_to_river_m": 450.0,
    "upstream_drainage_sqkm": 800.0,
}

HIGH_RISK_INPUT = {
    "rainfall_1h_mm": 75.0,
    "rainfall_3h_mm": 130.0,
    "rainfall_6h_mm": 200.0,
    "rainfall_24h_mm": 320.0,
    "rainfall_72h_mm": 480.0,
    "soil_saturation_pct": 96.0,
    "deep_soil_saturation_pct": 92.0,
    "temperature_c": 24.0,
    "relative_humidity_pct": 96.0,
    "surface_pressure_hpa": 905.0,
    "wind_speed_kmh": 40.0,
    "elevation_m": 650.0,
    "catchment_slope_deg": 35.0,
    "dist_to_river_m": 30.0,
    "upstream_drainage_sqkm": 5500.0,
}


def test_model_registry_loads_all_ten_regions():
    """Verify that model_registry successfully loads artifacts for all 10 regions."""
    for slug in ALL_REGIONS:
        bundle = model_registry.get("flood", slug)
        assert bundle is not None, f"Failed to load bundle for {slug}"
        assert bundle.model is not None, f"Model estimator missing for {slug}"
        assert bundle.preprocessor is not None, f"Preprocessor missing for {slug}"
        assert bundle.calibrator is not None or bundle.calibration_method == "none", f"Calibrator missing for {slug}"
        assert bundle.thresholds is not None, f"Thresholds missing for {slug}"
        assert bundle.feature_schema is not None, f"Feature schema missing for {slug}"
        assert bundle.metadata is not None, f"Metadata missing for {slug}"
        assert bundle.status in ["PRODUCTION_READY", "VALIDATION_ONLY", "DATA_INSUFFICIENT"]

        # Honest reporting check: Leh & Ladakh cold desert cloudburst profile must be VALIDATION_ONLY per §64
        if slug == "leh_ladakh":
            assert bundle.status == "VALIDATION_ONLY", f"Expected VALIDATION_ONLY for {slug}, got {bundle.status}"
        else:
            assert bundle.status == "PRODUCTION_READY", f"Expected PRODUCTION_READY for {slug}, got {bundle.status}"


def test_regional_predictions_all_ten_regions():
    """Verify inference across all 10 regions yields calibrated probabilities, thresholds, and factors."""
    for slug in ALL_REGIONS:
        # 1. Low risk prediction
        res_low = predict_flood_risk_regional(slug, LOW_RISK_INPUT)
        assert res_low is not None
        assert res_low["region"] == slug
        assert 0.0 <= res_low["calibrated_probability"] <= 1.0
        assert 0.0 <= res_low["raw_probability"] <= 1.0
        assert 0.0 < res_low["threshold"] < 1.0
        assert res_low["risk_level"] in ["LOW", "ADVISORY", "WATCH", "WARNING", "CRITICAL"]
        assert isinstance(res_low["top_contributing_factors"], list)
        assert len(res_low["top_contributing_factors"]) > 0

        # 2. High risk prediction
        res_high = predict_flood_risk_regional(slug, HIGH_RISK_INPUT)
        assert res_high is not None
        assert res_high["region"] == slug
        assert 0.0 <= res_high["calibrated_probability"] <= 1.0
        assert res_high["calibrated_probability"] >= res_low["calibrated_probability"]
        assert res_high["threshold_exceeded"] is True or res_high["risk_level"] in ["WATCH", "WARNING", "CRITICAL"]


def test_backward_compatibility_default_region():
    """Verify that calling predict_flood_risk without region preserves Himachal Pradesh V2 behavior."""
    res_default = predict_flood_risk(LOW_RISK_INPUT)
    assert res_default["region"] == "himachal_pradesh"
    assert "calibrated_probability" in res_default
    assert "decision_threshold" in res_default or "threshold" in res_default
    assert res_default["decision_threshold"] == 0.08

    # Explicit region routing via kwarg
    res_sikkim = predict_flood_risk(LOW_RISK_INPUT, region="sikkim")
    assert res_sikkim["region"] == "sikkim"

    # §45 Unknown region safety: must reject rather than silently fall back to Himachal Pradesh
    import pytest
    with pytest.raises(ValueError, match="UNSUPPORTED_REGION"):
        predict_flood_risk(LOW_RISK_INPUT, region="non_existent_region")


def test_model_adapter_regional_inference():
    """Verify that FloodModelAdapter handles regional parameters across all horizons."""
    multi_stream_features = {
        "location": {"altitude": 1400.0, "slope_deg": 22.0, "dist_to_river_m": 120.0},
        "rainfall": {"current_mm_hr": 12.0, "accumulated_1h_mm": 15.0, "accumulated_24h_mm": 45.0},
        "forecast": {"rainfall_1h_mm": 18.0, "rainfall_3h_mm": 35.0, "rainfall_6h_mm": 60.0},
        "river": {"stage_m": 3.8, "warning_level_m": 4.0, "danger_level_m": 5.5},
        "soil": {"saturation_percent": 68.0},
    }

    res = flood_prediction_adapter.predict(multi_stream_features, region="meghalaya")
    assert res["region"] == "meghalaya"
    assert "horizons" in res
    assert all(h in res["horizons"] for h in ["1h", "3h", "6h", "12h", "24h", "48h"])
    assert res["overallRisk"] in ["LOW", "WATCH", "HIGH", "CRITICAL"]
    assert 0.0 <= res["score"] <= 100.0


def test_api_regions_list_endpoint():
    """Verify GET /api/v1/regions returns all 10 regions with metadata."""
    response = client.get("/api/v1/regions")
    assert response.status_code == 200
    data = response.json()
    assert "regions" in data
    assert len(data["regions"]) == 10
    slugs = [r["slug"] for r in data["regions"]]
    for s in ALL_REGIONS:
        assert s in slugs


def test_api_region_detail_and_model_info_endpoints():
    """Verify GET /api/v1/regions/{slug} and /api/v1/regions/{slug}/model-info."""
    # 1. Sikkim detail
    resp_sikkim = client.get("/api/v1/regions/sikkim")
    assert resp_sikkim.status_code == 200
    s_data = resp_sikkim.json()
    assert s_data["region_slug"] == "sikkim"
    assert s_data["display_name"] == "Sikkim"

    # 2. Sikkim model-info
    resp_model = client.get("/api/v1/regions/sikkim/model-info")
    assert resp_model.status_code == 200
    m_data = resp_model.json()
    assert m_data["region"] == "sikkim"
    assert any(alg in m_data["model_type"].lower() for alg in ["xgboost", "xgb", "random_forest", "forest", "logistic"])
    assert m_data["status"] == "PRODUCTION_READY"
    assert "metrics" in m_data

    # 3. Leh & Ladakh model-info (§64 status check)
    resp_leh = client.get("/api/v1/regions/leh_ladakh/model-info")
    assert resp_leh.status_code == 200
    leh_data = resp_leh.json()
    assert leh_data["status"] == "VALIDATION_ONLY"

    # 4. Non-existent region 404
    resp_404 = client.get("/api/v1/regions/atlantis")
    assert resp_404.status_code == 404


def test_api_predict_regional_endpoint():
    """Verify POST /api/v1/predict/{slug} produces predictions."""
    payload = {
        "rainfall_1h_mm": 45.0,
        "rainfall_3h_mm": 80.0,
        "rainfall_6h_mm": 110.0,
        "rainfall_24h_mm": 190.0,
        "rainfall_72h_mm": 280.0,
        "soil_saturation_pct": 82.0,
        "deep_soil_saturation_pct": 78.0,
        "temperature_c": 20.0,
        "relative_humidity_pct": 88.0,
        "surface_pressure_hpa": 915.0,
        "wind_speed_kmh": 22.0,
        "elevation_m": 920.0,
        "catchment_slope_deg": 26.0,
        "dist_to_river_m": 75.0,
        "upstream_drainage_sqkm": 3400.0,
    }

    # Predict for Arunachal Pradesh
    resp_ap = client.post("/api/v1/predict/arunachal_pradesh", json=payload)
    assert resp_ap.status_code == 200
    ap_data = resp_ap.json()
    assert ap_data["region"] == "arunachal_pradesh"
    assert 0.0 <= ap_data["flood_probability"] <= 1.0
    assert "threshold" in ap_data
    assert "risk_level" in ap_data
    assert len(ap_data["top_contributing_factors"]) > 0
