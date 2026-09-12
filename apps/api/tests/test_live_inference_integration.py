"""
apps/api/tests/test_live_inference_integration.py
Integration tests for real-time model inference pipeline, on-demand village prediction,
and regional batch evaluation across the Mandi basin.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_village_detail_includes_live_prediction_fields():
    """Verify GET /api/v1/villages/{village_id} contains calibrated prediction and model fields."""
    list_res = client.get("/api/v1/villages")
    assert list_res.status_code == 200
    v_id = list_res.json()[0]["id"]

    response = client.get(f"/api/v1/villages/{v_id}")
    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert data["id"] == v_id
    assert "risk_score" in data
    assert "risk_level" in data
    assert "calibrated_probability" in data
    assert 0.0 <= data["calibrated_probability"] <= 1.0
    assert "decision_threshold" in data
    assert data["decision_threshold"] == 0.08
    assert "threshold_exceeded" in data
    assert isinstance(data["threshold_exceeded"], bool)
    assert "model_version" in data


def test_on_demand_village_prediction_endpoint():
    """Verify POST /api/v1/villages/{village_id}/predict executes real-time inference and returns valid metrics."""
    list_res = client.get("/api/v1/villages")
    assert list_res.status_code == 200
    v_id = list_res.json()[0]["id"]

    response = client.post(f"/api/v1/villages/{v_id}/predict")
    assert response.status_code == 200
    data = response.json()

    assert data["village_id"] == v_id
    assert "flood_probability" in data
    assert "calibrated_probability" in data
    assert "decision_threshold" in data
    assert 0.0 < data["decision_threshold"] < 1.0
    assert "risk_score" in data
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ["LOW", "WATCH", "HIGH", "CRITICAL", "INSUFFICIENT_DATA"]
    assert "top_contributing_factors" in data
    assert isinstance(data["top_contributing_factors"], list)
    assert "canonical_features" in data
    assert len(data["canonical_features"]) >= 15


def test_on_demand_prediction_nonexistent_village():
    """Verify POST /api/v1/villages/{invalid_id}/predict returns 404."""
    response = client.post("/api/v1/villages/non_existent_village_xyz/predict")
    assert response.status_code == 404


def test_evaluate_all_settlements_batch_endpoint():
    """Verify POST /api/v1/predictions/evaluate-all executes regional batch inference."""
    response = client.post("/api/v1/predictions/evaluate-all")
    assert response.status_code == 200
    data = response.json()

    assert "total_evaluated" in data
    assert data["total_evaluated"] > 0
    assert "severity_breakdown" in data
    assert "LOW" in data["severity_breakdown"]
    assert "average_calibrated_probability" in data
    assert 0.0 <= data["average_calibrated_probability"] <= 1.0
    assert data["decision_threshold"] == 0.08
    assert "results" in data
    assert len(data["results"]) == data["total_evaluated"]
