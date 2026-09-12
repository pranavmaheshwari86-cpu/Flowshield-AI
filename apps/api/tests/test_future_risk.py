"""
apps/api/tests/test_future_risk.py
Unit and integration tests for Multi-Horizon Future Flood Risk Forecasting.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_future_risk_forecast_endpoint(monkeypatch):
    """Tests GET /api/v1/risk/forecast for a known village."""
    from app.services.forecast_service import forecast_service
    monkeypatch.setattr(forecast_service, "_fetch_precipitation_projections", lambda v, db: [2.0] * 48)

    response = client.get("/api/v1/risk/forecast?village_id=mandi_sadar")
    assert response.status_code == 200
    data = response.json()

    assert "village_id" in data
    assert "timeline" in data
    assert isinstance(data["timeline"], list)
    assert len(data["timeline"]) > 0

    first_horizon = data["timeline"][0]
    assert "horizon_hours" in first_horizon
    assert "flood_probability" in first_horizon
    assert 0.0 <= first_horizon["flood_probability"] <= 1.0
    assert "risk_score" in first_horizon
    assert 0.0 <= first_horizon["risk_score"] <= 100.0
    assert "risk_level" in first_horizon
    assert first_horizon["risk_level"] in ["LOW", "WATCH", "HIGH", "CRITICAL"]
    assert "uncertainty_band" in first_horizon
    assert "p10" in first_horizon["uncertainty_band"]
    assert "p90" in first_horizon["uncertainty_band"]
    assert first_horizon["uncertainty_band"]["p10"] <= first_horizon["uncertainty_band"]["p90"]


def test_future_risk_summary(monkeypatch):
    """Tests GET /api/v1/risk/forecast/summary for regional overview."""
    from app.services.forecast_service import forecast_service
    monkeypatch.setattr(forecast_service, "_fetch_precipitation_projections", lambda v, db: [2.0] * 48)

    response = client.get("/api/v1/risk/forecast/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_monitored" in data
    assert "settlements" in data
    assert isinstance(data["settlements"], list)
