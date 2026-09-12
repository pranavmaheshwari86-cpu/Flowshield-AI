"""
apps/api/tests/test_off_network_snap.py
Unit tests for off-network snap threshold guard in RouteService (v2.4).
Verifies that coordinates > 1.5 km from the mapped road network return ROUTING_UNAVAILABLE_OFF_GRID.
"""

import pytest
from app.services.route_service import route_service


def test_off_network_snap_guard(client, db_session):
    """
    Coordinates situated deep in the wilderness far from any mapped settlement (>1.5 km)
    must trigger ROUTING_UNAVAILABLE_OFF_GRID and demand authority coordination.
    """
    # Coordinates in remote high Himalayas (remote coordinate far from Beas Basin villages)
    remote_lat = 32.5500
    remote_lon = 78.2500

    response = client.post(
        "/api/v1/routes/evaluate",
        json={
            "origin_latitude": remote_lat,
            "origin_longitude": remote_lon,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ROUTING_UNAVAILABLE_OFF_GRID"
    assert data["route_label"] == "OFF-GRID COORDINATES"
    assert data["requires_authority_coordination"] is True
    assert data["selected_route"] is None
    assert data["snap_distance_km"] > 1.5
    assert "1.5 km" in data["message"]


def test_on_network_snap_success(client, db_session):
    """Coordinates within 500 meters of a known village snap cleanly to the network."""
    from app.models.village import Village

    village = db_session.query(Village).first()
    assert village is not None

    # Slightly offset coordinate (approx 200 meters away)
    near_lat = village.latitude + 0.001
    near_lon = village.longitude + 0.001

    response = client.post(
        "/api/v1/routes/evaluate",
        json={
            "origin_latitude": near_lat,
            "origin_longitude": near_lon,
            "village_id": village.id,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ["RECOMMENDED_LOWER_RISK_ROUTE", "NO_SAFE_ROUTE_FOUND"]
    assert data["snap_distance_km"] <= 1.5
