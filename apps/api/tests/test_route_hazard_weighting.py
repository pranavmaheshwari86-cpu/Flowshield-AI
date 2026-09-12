"""
apps/api/tests/test_route_hazard_weighting.py
Unit tests for hazard-weighted evacuation routing and NO_SAFE_ROUTE_FOUND state (v2.4).
"""

import pytest
from app.models.village import Village
from app.models.route import Route
from app.services.route_service import route_service


def test_hazard_weighted_route_selection(client, db_session):
    """Verify that routing penalizes high-risk/blocked paths and selects lowest-hazard corridor."""
    village = db_session.query(Village).first()
    assert village is not None

    routes = db_session.query(Route).filter(Route.origin_village_id == village.id).all()
    if len(routes) >= 2:
        # Intentionally block the first route and verify the second is chosen
        r1, r2 = routes[0], routes[1]
        r1.is_blocked = True
        r1.assessed_risk_score = 90
        r2.is_blocked = False
        r2.assessed_risk_score = 15
        db_session.commit()

        res = route_service.evaluate_route(
            db=db_session,
            origin_lat=village.latitude,
            origin_lon=village.longitude,
            village_id=village.id,
        )

        assert res.status == "RECOMMENDED_LOWER_RISK_ROUTE"
        assert res.route_label == "RECOMMENDED LOWER-RISK ROUTE"
        assert res.selected_route is not None
        assert res.selected_route.id == r2.id
        assert res.requires_authority_coordination is False


def test_no_safe_route_found_when_all_cut(client, db_session):
    """Verify that when all evacuation routes are severed, system outputs NO_SAFE_ROUTE_FOUND."""
    village = db_session.query(Village).first()
    assert village is not None

    routes = db_session.query(Route).filter(Route.origin_village_id == village.id).all()
    for r in routes:
        r.is_blocked = True
        r.blockage_reason = "Road completely washed away by torrential mudflow"
    db_session.commit()

    res = route_service.evaluate_route(
        db=db_session,
        origin_lat=village.latitude,
        origin_lon=village.longitude,
        village_id=village.id,
    )

    assert res.status == "NO_SAFE_ROUTE_FOUND"
    assert res.route_label == "NO SAFE ROUTE FOUND"
    assert res.selected_route is None
    assert res.requires_authority_coordination is True
    assert "severed" in res.message.lower()

    # Reset route blockage state
    for r in routes:
        r.is_blocked = False
    db_session.commit()
