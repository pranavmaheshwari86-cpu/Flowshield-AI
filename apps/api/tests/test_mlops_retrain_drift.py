"""
apps/api/tests/test_mlops_retrain_drift.py
Unit tests for MLOps model registry, drift monitoring, and retraining pipeline.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_model_status_endpoint():
    """Tests GET /api/v1/model/status."""
    response = client.get("/api/v1/model/status")
    assert response.status_code == 200
    data = response.json()
    assert "pipeline_version" in data
    assert "operational_threshold" in data
    assert "evaluation_metrics" in data
    assert data["evaluation_metrics"]["recall"] >= 0.85


def test_system_drift_endpoint():
    """Tests GET /api/v1/system/drift."""
    response = client.get("/api/v1/system/drift")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "drift_level" in data
    assert data["drift_level"] in ["HEALTHY", "MONITORING", "DRIFT_ALERT", "INSUFFICIENT_SAMPLES"]


def test_submit_verified_outcome():
    """Tests POST /api/v1/model/outcome."""
    payload = {
        "village_id": "mandi_sadar",
        "actual_flood_occurred": True,
        "severity_observed": "MODERATE",
        "flood_depth_cm": 45.0,
        "verification_source": "SDRF_BATTALION_7",
        "verified_by": "Inspector R. Sharma",
        "notes": "Beas river inundation reached lower vegetable market."
    }
    response = client.post("/api/v1/model/outcome", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "verified_outcome_recorded"
    assert "outcome_id" in data


def test_list_verified_outcomes():
    """Tests GET /api/v1/model/outcomes."""
    response = client.get("/api/v1/model/outcomes")
    assert response.status_code == 200
    data = response.json()
    assert "total_outcomes" in data
    assert "items" in data
