"""
apps/api/tests/test_forecast_uncertainty.py
Unit tests for honest forecasting and decoupled soil moisture prototype (v2.4).
Verifies UNCERTAINTY_UNAVAILABLE when variance is absent, and PROTOTYPE_BASELINE soil moisture.
"""

import pytest
from app.models.village import Village


def test_precipitation_forecast_honest_uncertainty(client, db_session):
    """Verify forecast returns structured horizons and UNCERTAINTY_UNAVAILABLE without fake decay curves."""
    village = db_session.query(Village).first()
    assert village is not None

    response = client.get(f"/api/v1/hazards/forecast/{village.id}")
    assert response.status_code == 200
    data = response.json()

    assert data["village_id"] == village.id
    assert "horizons" in data
    assert len(data["horizons"]) == 6  # 1h, 3h, 6h, 12h, 24h, 48h

    expected_lead_times = [1, 3, 6, 12, 24, 48]
    actual_lead_times = [h["lead_time_hours"] for h in data["horizons"]]
    assert actual_lead_times == expected_lead_times

    # Verify honest uncertainty semantics (no fabricated decay curves)
    for h in data["horizons"]:
        assert h["uncertainty_state"] == "UNCERTAINTY_UNAVAILABLE"
        assert h["confidence_interval_p10"] is None
        assert h["confidence_interval_p90"] is None
        assert h["projected_rainfall_mm"] >= 0.0

    assert data["cumulative_48h_rainfall_mm"] >= 0.0
    assert data["peak_intensity_horizon_hours"] in expected_lead_times


def test_soil_moisture_forecast_prototype_baseline(client, db_session):
    """Verify soil moisture forecast is decoupled and declared PROTOTYPE_BASELINE."""
    village = db_session.query(Village).first()
    assert village is not None

    response = client.get(f"/api/v1/hazards/soil-moisture-forecast/{village.id}")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "PROTOTYPE_BASELINE"
    assert data["is_ml_model"] is False
    assert "1D water-balance" in data["scientific_disclosure"]

    assert len(data["horizons"]) == 6
    for h in data["horizons"]:
        assert h["model_type"] == "1D_WATER_BALANCE_BUCKET"
        assert h["status"] == "PROTOTYPE_BASELINE"
        assert h["is_ml_model"] is False
        assert 0.0 <= h["projected_soil_saturation_pct"] <= 100.0
