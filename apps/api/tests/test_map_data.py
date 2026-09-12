def test_geojson_layers(client):
    response = client.get("/api/v1/map/geojson?layers=villages,risk_zones,rivers,shelters,routes")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert len(data["features"]) > 0

    layers_found = set(f["properties"].get("layer") for f in data["features"])
    assert "villages" in layers_found
    assert "risk_zones" in layers_found
    assert "rivers" in layers_found
    assert "shelters" in layers_found
    assert "routes" in layers_found
