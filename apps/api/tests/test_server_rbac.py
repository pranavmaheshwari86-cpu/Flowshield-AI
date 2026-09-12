"""
apps/api/tests/test_server_rbac.py
Unit tests for server-enforced Role-Based Access Control (RBAC) (v2.4).
Verifies that unauthorized roles receive HTTP 403 FORBIDDEN on protected endpoints.
"""

import pytest
from app.models.user import User
from app.models.route import Route
from app.auth.jwt_handler import create_access_token, hash_password


@pytest.fixture
def test_roles(db_session):
    """Ensures test users for AUTHORITY, RESPONDER, and CITIZEN exist in the database."""
    roles_data = [
        ("auth_user", "AUTHORITY"),
        ("resp_user", "RESPONDER"),
        ("cit_user", "CITIZEN"),
    ]
    tokens = {}
    for uname, role in roles_data:
        user = db_session.query(User).filter(User.username == uname).first()
        if not user:
            user = User(
                username=uname,
                email=f"{uname}@flowshield.local",
                hashed_password=hash_password("password123"),
                role=role,
                full_name=f"Test {role}",
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
        token = create_access_token(data={"sub": user.username, "role": user.role, "id": user.id})
        tokens[role] = token
    return tokens


def test_rbac_citizen_forbidden_on_blockage_report(client, db_session, test_roles):
    """A CITIZEN token must be rejected with HTTP 403 when attempting to report road blockages."""
    route = db_session.query(Route).first()
    assert route is not None

    headers = {"Authorization": f"Bearer {test_roles['CITIZEN']}"}
    response = client.post(
        f"/api/v1/routes/blockage/{route.id}",
        json={"is_blocked": True, "blockage_reason": "Mudslide detected by citizen"},
        headers=headers,
    )
    assert response.status_code == 403
    assert "Access forbidden" in response.json()["detail"]


def test_rbac_responder_allowed_on_blockage_report(client, db_session, test_roles):
    """A RESPONDER token must be authorized (HTTP 200) to report road blockages."""
    route = db_session.query(Route).first()
    assert route is not None

    headers = {"Authorization": f"Bearer {test_roles['RESPONDER']}"}
    response = client.post(
        f"/api/v1/routes/blockage/{route.id}",
        json={"is_blocked": True, "blockage_reason": "SDRF barrier placed across inundated culvert"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_blocked"] is True

    # Reset blockage
    client.post(
        f"/api/v1/routes/blockage/{route.id}",
        json={"is_blocked": False},
        headers=headers,
    )
