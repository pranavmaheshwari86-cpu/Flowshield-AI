"""
apps/api/tests/test_evacuation_intelligence.py
Unit and integration tests for Flowshield Evacuation Intelligence & Tactical Routing.
Validates:
- State & dependent district dynamic hierarchy
- Strict non-fabrication of unpublished capacities & occupancies
- Multi-factor evacuation suitability ranking
- Road incident reporting & blockage propagation
- Geographic coverage synchronization
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.app.main import app
from apps.api.app.database import SessionLocal
from apps.api.app.models.shelter import Shelter
from apps.api.app.models.route import Route
from apps.api.app.models.village import Village
from apps.api.app.services.shelter_service import shelter_service
from apps.api.app.services.geography_service import geography_service


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_geography_supported_states(client):
    """Verify that only ML-supported states are returned."""
    resp = client.get("/api/v1/geography/states")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    state_names = [s["state"] for s in data]
    assert "Uttarakhand" in state_names
    assert "Himachal Pradesh" in state_names


def test_geography_dependent_districts_uttarakhand(client):
    """Verify dependent districts for Uttarakhand contain Rudraprayag and Chamoli."""
    resp = client.get("/api/v1/geography/states/Uttarakhand/districts")
    assert resp.status_code == 200
    districts = resp.json()
    names = [d["district"] for d in districts]
    assert "Rudraprayag" in names
    assert "Chamoli" in names
    rud = next(d for d in districts if d["district"] == "Rudraprayag")
    assert rud["center_lat"] == 30.500
    assert rud["center_lon"] == 79.030
    assert rud["bounds"]["min_lat"] <= rud["center_lat"] <= rud["bounds"]["max_lat"]


def test_geography_dependent_districts_himachal(client):
    """Verify dependent districts for Himachal Pradesh contain Mandi and Kullu."""
    resp = client.get("/api/v1/geography/states/Himachal%20Pradesh/districts")
    assert resp.status_code == 200
    districts = resp.json()
    names = [d["district"] for d in districts]
    assert "Mandi" in names
    assert "Kullu" in names
    mandi = next(d for d in districts if d["district"] == "Mandi")
    assert mandi["river_basin"] == "Beas River Basin"


def test_shelters_non_fabrication_rule(client, db_session):
    """
    Verify strict non-fabrication policy:
    If capacity is unpublished, capacity_display must indicate 'Not officially published'.
    If occupancy is unpublished, occupancy_display must indicate 'Not currently available'.
    """
    resp = client.get("/api/v1/shelters?district=Rudraprayag")
    assert resp.status_code == 200
    shelters = resp.json()
    assert len(shelters) > 0

    has_unpublished_cap = False
    for s in shelters:
        assert "source_name" in s
        assert "verification_status" in s
        assert "confidence_score" in s
        assert s["confidence_score"] >= 70

        if s["capacity"] is None:
            has_unpublished_cap = True
            assert s["capacity_display"] == "Not officially published"

        if s["current_occupancy"] is None:
            assert s["occupancy_display"] == "Not currently available"

    assert has_unpublished_cap, "Must contain authentic facilities with unpublished capacity quotas"


def test_multi_factor_shelter_recommendation(client):
    """
    Verify that multi-factor recommendation ranks safe, verified shelters
    and includes suitability scores and recommendation labels.
    """
    # Sonprayag coordinates
    resp = client.get("/api/v1/shelters/recommended?lat=30.598&lon=79.036&state=Uttarakhand&district=Rudraprayag&limit=5")
    assert resp.status_code == 200
    ranked = resp.json()
    assert len(ranked) > 0
    top = ranked[0]
    assert "suitability_score" in top
    assert "recommendation_label" in top
    assert top["suitability_score"] >= 75.0
    assert "RECOMMENDED" in top["recommendation_label"]
    assert len(top["rationale"]) > 0


def test_route_evaluation_and_snap_guard(client):
    """
    Verify dynamic route evaluation enforces off-network snap limits (> 1.5 km).
    """
    # Close coordinates in Mandi
    resp = client.post("/api/v1/routes/evaluate", json={
        "origin_latitude": 31.7087,
        "origin_longitude": 76.9320,
        "state": "Himachal Pradesh",
        "district": "Mandi"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["RECOMMENDED_LOWER_RISK_ROUTE", "NO_SAFE_ROUTE_FOUND"]

    # Remote glacial coordinates far off-grid (> 1.5 km from any road)
    resp_offgrid = client.post("/api/v1/routes/evaluate", json={
        "origin_latitude": 32.5000,
        "origin_longitude": 78.5000,
        "state": "Himachal Pradesh",
        "district": "Mandi"
    })
    assert resp_offgrid.status_code == 200
    data_offgrid = resp_offgrid.json()
    assert data_offgrid["status"] == "ROUTING_UNAVAILABLE_OFF_GRID"
    assert data_offgrid["requires_authority_coordination"] is True


def test_incident_reporting_workflow(client, db_session):
    """
    Verify blockage incident reporting creates an incident and severs the route.
    """
    routes = db_session.query(Route).all()
    assert len(routes) > 0
    target_route = routes[0]

    incident_payload = {
        "corridor_name": target_route.name,
        "route_id": target_route.id,
        "latitude": 30.598,
        "longitude": 79.036,
        "blockage_type": "Landslide",
        "severity": "CRITICAL",
        "description": "Massive boulder slide blocking entire carriage way at KM 4.2",
        "reported_by": "SDRF Tactical Unit 4",
    }

    resp = client.post("/api/v1/routes/incidents", json=incident_payload)
    assert resp.status_code == 200
    incident = resp.json()
    assert incident["status"] == "ACTIVE"
    assert incident["blockage_type"] == "Landslide"

    # Verify route status updated
    db_session.refresh(target_route)
    assert target_route.is_blocked is True
    assert target_route.assessed_risk_score >= 90

    # Restore route status for test cleanup
    target_route.is_blocked = False
    target_route.assessed_risk_score = 15
    db_session.commit()


def test_data_sources_provenance_endpoint(client):
    """Verify data sources endpoint exposes official DDMP and open scientific sources."""
    resp = client.get("/api/v1/data-sources")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provenance_standard"] == "Strict Open-Access & Non-Fabrication Policy"
    source_names = [s["name"] for s in data["sources"]]
    assert any("USDMA" in name for name in source_names)
    assert any("HPSDMA" in name for name in source_names)
    assert any("OpenStreetMap" in name for name in source_names)
