def test_national_summary(client):
    response = client.get("/api/v1/national/summary")
    assert response.status_code == 200
    data = response.json()
    assert "national_overview" in data
    assert data["national_overview"]["total_affected_population"] > 4000000
    assert "Bihar" in data["states"]
    assert "Uttar Pradesh" in data["states"]
    assert len(data["live_gauges"]) > 0


def test_national_river_gauges(client):
    response = client.get("/api/v1/national/river-gauges")
    assert response.status_code == 200
    data = response.json()
    gauges = data["gauges"]
    assert len(gauges) >= 8
    # Verify Ganga and Pandu gauges exist
    rivers = [g["river"] for g in gauges]
    assert any("Ganga" in r for r in rivers)
    assert any("Pandu" in r for r in rivers)


def test_historical_events(client):
    response = client.get("/api/v1/historical/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 6
    # Verify key historical disasters are present
    ids = [e["id"] for e in events]
    assert "hist-2019-patna" in ids
    assert "hist-2013-kedarnath" in ids
    assert "hist-2023-yamuna" in ids


def test_historical_event_detail(client):
    response = client.get("/api/v1/historical/events/hist-2019-patna")
    assert response.status_code == 200
    event = response.json()
    assert event["year"] == 2019
    assert "Ganga" in event["river_basin"] or "Punpun" in event["river_basin"]
    assert event["flowshield_ai_advantage"]["hours_lead_time_gained"] > 10


def test_alerts_and_map_state_filtering(client):
    # State-filtered alerts
    alerts_bihar = client.get("/api/v1/alerts?state=Bihar")
    assert alerts_bihar.status_code == 200
    bihar_list = alerts_bihar.json()
    assert len(bihar_list) > 0

    # State-filtered map geojson
    map_bihar = client.get("/api/v1/map/geojson?state=Bihar")
    assert map_bihar.status_code == 200
    geojson = map_bihar.json()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 0
