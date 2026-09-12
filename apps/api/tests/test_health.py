def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["database"] == "healthy"
    assert data["model"]["loaded"] is True
    assert "flowshield" in data["model"]["version"] or "v2" in data["model"]["version"] or "xgb" in data["model"]["version"]
