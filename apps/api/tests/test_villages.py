def test_list_villages(client):
    response = client.get("/api/v1/villages")
    assert response.status_code == 200
    villages = response.json()
    assert len(villages) >= 20
    # Verify state filtering
    bihar_res = client.get("/api/v1/villages?state=Bihar")
    assert bihar_res.status_code == 200
    assert len(bihar_res.json()) >= 5

    # Verify first village structure
    v1 = villages[0]
    assert "id" in v1
    assert "name" in v1
    assert "risk_score" in v1
    assert "risk_level" in v1
    assert "elevation" in v1
    assert "distance_to_river" in v1


def test_get_village_detail(client):
    # Fetch list first to get valid ID
    list_res = client.get("/api/v1/villages")
    v_id = list_res.json()[0]["id"]

    response = client.get(f"/api/v1/villages/{v_id}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["id"] == v_id
    assert "current_conditions" in detail
    assert "historical_risk_trend" in detail
    assert "recommended_actions" in detail
    assert isinstance(detail["recommended_actions"], list)
