def test_on_demand_prediction(client):
    payload = {
        "rainfall_1h": 65.0,
        "rainfall_3h": 120.0,
        "rainfall_6h": 180.0,
        "rainfall_24h": 260.0,
        "rainfall_intensity": 45.0,
        "soil_moisture": 86.0,
        "river_level": 5.2,
        "river_level_change": 1.4,
        "elevation": 950.0,
        "slope": 28.0,
        "distance_to_river": 0.35,
        "historical_flood_frequency": 0.40,
    }

    response = client.post("/api/v1/predictions", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "flood_probability" in data
    assert 0.0 <= data["flood_probability"] <= 1.0
    assert "risk_score" in data
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ["LOW", "WATCH", "MODERATE", "HIGH", "CRITICAL"]

    # Verify SHAP attributions
    assert "top_contributing_factors" in data
    assert len(data["top_contributing_factors"]) > 0
    top1 = data["top_contributing_factors"][0]
    assert "feature" in top1
    assert "contribution" in top1
    assert "direction" in top1
    assert top1["direction"] in ["increases_risk", "decreases_risk"]

    # Verify Provenance
    assert "data_provenance" in data
    assert data["data_provenance"]["is_simulated"] is False
