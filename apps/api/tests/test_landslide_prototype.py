"""
apps/api/tests/test_landslide_prototype.py
Unit tests for Landslide Screening Prototype (v2.4).
Verifies empirical GSI/Caine threshold, prototype labeling, and non-ML declaration.
"""

import pytest
from app.models.village import Village
from app.services.landslide_service import landslide_service


def test_landslide_empirical_prototype_labeling(client, db_session):
    """Verify endpoint /api/v1/hazards/landslide/{village_id} returns non-ML prototype tags."""
    # Retrieve a known village
    village = db_session.query(Village).first()
    assert village is not None

    response = client.get(f"/api/v1/hazards/landslide/{village.id}")
    assert response.status_code == 200
    data = response.json()

    # Verify non-ML declaration and prototype status
    assert data["is_ml_model"] is False
    assert data["status"] == "PROTOTYPE_EMPIRICAL_THRESHOLD"
    assert "GSI / Caine" in data["methodology"]
    assert "scientific_disclosure" in data
    assert "NOT a trained machine learning model" in data["scientific_disclosure"]
    assert "advisory_notice" in data
    assert "Geological Survey of India" in data["advisory_notice"]

    # Verify trigger index bounds
    assert 0.0 <= data["trigger_index"] <= 1.0
    assert data["susceptibility_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL", "SUSCEPTIBILITY_UNAVAILABLE"]


def test_landslide_invalid_slope_handling():
    """Verify that missing/negative slope triggers SUSCEPTIBILITY_UNAVAILABLE."""
    broken_village = Village(
        id="broken-slope-test",
        name="Broken Slope Settlement",
        latitude=31.5,
        longitude=77.1,
        elevation=1200.0,
        slope=-5.0,  # Physically impossible negative slope
        distance_to_river=0.5,
    )

    res = landslide_service.assess_village_landslide_hazard(broken_village)
    assert res.susceptibility_level == "SUSCEPTIBILITY_UNAVAILABLE"
    assert res.trigger_index == 0.0
    assert res.is_ml_model is False
