"""
apps/api/tests/test_ai_endpoints.py
Unit and integration tests for the Flowshield Real-Data AI Risk Inference API (V2).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ai_risk_inference_with_coords_and_timestamp():
    """Tests POST /api/v1/ai/risk with spatial coordinates and disaster timestamp."""
    payload = {
        "latitude": 31.7087,
        "longitude": 76.9320,
        "timestamp": "2023-07-09T10:00:00+05:30"
    }
    response = client.post("/api/v1/ai/risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 100.0
    assert "risk_level" in data
    assert data["risk_level"] in ["LOW", "NORMAL", "WATCH", "ADVISORY", "HIGH", "WARNING", "CRITICAL", "INSUFFICIENT_DATA"]
    assert "flood_probability" in data
    assert 0.0 <= data["flood_probability"] <= 1.0
    assert "confidence" in data
    assert "threshold" in data
    assert "calibration_method" in data
    assert "explanation" in data
    assert isinstance(data["explanation"], list)
    assert len(data["explanation"]) > 0
    assert data["status"] in ["research_prototype_public_data", "operational_v2_validated"]


def test_ai_risk_inference_compatibility_path():
    """Tests POST /api/ai/risk mounted directly for backward compatibility."""
    payload = {
        "latitude": 31.6690,
        "longitude": 77.0580,
        "timestamp": "2023-08-14T14:00:00+05:30"
    }
    response = client.post("/api/ai/risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "model_version" in data
    assert data["model_version"] == "flowshield-flood-risk-v2"


def test_ai_risk_inference_with_feature_overrides():
    """Tests POST /api/v1/ai/risk with explicit rainfall and soil moisture telemetry."""
    payload = {
        "latitude": 31.7450,
        "longitude": 77.2100,
        "rainfall_1h_mm": 55.0,
        "rainfall_3h_mm": 110.0,
        "soil_saturation_pct": 92.0,
        "catchment_slope_deg": 35.0,
        "dist_to_river_m": 40.0
    }
    response = client.post("/api/v1/ai/risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] > 0.0
    assert data["risk_level"] in ["HIGH", "CRITICAL"]
    assert any("rainfall" in exp.lower() or "precipitation" in exp.lower() for exp in data["explanation"])


def test_ai_risk_insufficient_data_safety_state():
    """Tests POST /api/v1/ai/risk with corrupt/out-of-range sensor telemetry trips safety state."""
    payload = {
        "latitude": 31.7087,
        "longitude": 76.9320,
        "rainfall_1h_mm": -50.0  # Physically impossible negative precipitation
    }
    response = client.post("/api/v1/ai/risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "INSUFFICIENT_DATA"
    assert data["status"] == "insufficient_data"
    assert any("Data quality safety guardrail" in exp for exp in data["explanation"])


def test_ai_models_endpoint():
    """Tests GET /api/v1/ai/models returns the multi-model benchmark results."""
    response = client.get("/api/v1/ai/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "logistic_regression" in data["models"]
    assert "random_forest" in data["models"]
    assert "xgboost" in data["models"]
    assert data["selected_model"] == "logistic_regression"
    assert data["calibration_method"] == "isotonic"


def test_ai_features_metadata():
    """Tests GET /api/v1/ai/features returns the 15 canonical physical features."""
    response = client.get("/api/v1/ai/features")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 15
    assert "canonical_features" in data
    assert "rainfall_3h_mm" in data["canonical_features"]
