"""
tests/test_agro_monitoring.py
Automated test suite for AgroMonitoring Soil Moisture GIS and API Integration
"""

import json
import pytest
from shapely.geometry import Polygon, shape

from apps.api.app.services.agro_grid_service import (
    agro_grid_service,
    calculate_geodesic_area_ha,
    subdivide_polygon_recursively,
    AGRO_MIN_AREA_HA,
    AGRO_MAX_AREA_HA,
)
from apps.api.app.services.agro_monitoring_service import (
    classify_soil_moisture_tier,
    agro_monitoring_service,
)
from apps.api.app.models.monitoring_polygon import MonitoringPolygon, SoilObservation


def test_administrative_boundary_loading():
    """Verify that the administrative boundary dataset loads properly."""
    features = agro_grid_service.load_features()
    assert len(features) > 100, f"Expected >100 district features, found {len(features)}"

    hierarchy = agro_grid_service.get_hierarchy()
    assert "Himachal Pradesh" in hierarchy
    assert "Mandi" in hierarchy["Himachal Pradesh"]
    assert "Uttarakhand" in hierarchy
    assert "Kerala" in hierarchy


def test_geodesic_area_calculation():
    """Verify geodesic authalic area calculation on a known square degree."""
    # 0.1 deg x 0.1 deg box near equator (0,0) ~ 11.1km x 11.1km = ~12,300 ha
    equator_poly = Polygon([(0.0, 0.0), (0.1, 0.0), (0.1, 0.1), (0.0, 0.1), (0.0, 0.0)])
    area_equator = calculate_geodesic_area_ha(equator_poly)
    assert 12000.0 < area_equator < 12500.0

    # Same degree box at 60 deg latitude has much less area due to convergence of meridians
    high_lat_poly = Polygon([(0.0, 60.0), (0.1, 60.0), (0.1, 60.1), (0.0, 60.1), (0.0, 60.0)])
    area_high_lat = calculate_geodesic_area_ha(high_lat_poly)
    assert area_high_lat < (area_equator * 0.6)


def test_adaptive_grid_tiling_mandi():
    """Verify that district boundary is divided into valid polygons complying with AgroMonitoring rules."""
    cells = agro_grid_service.generate_grid_cells(
        scope="district",
        state_name="Himachal Pradesh",
        district_name="Mandi",
        target_cell_ha=2000.0,
    )

    assert len(cells) > 10, "Should generate multiple cells for Mandi district"

    for cell in cells:
        # Constraint 1: Area within AgroMonitoring limits
        area = cell["area_hectares"]
        assert AGRO_MIN_AREA_HA <= area <= AGRO_MAX_AREA_HA, (
            f"Cell {cell['name']} area {area} ha violates Agro limits [{AGRO_MIN_AREA_HA}, {AGRO_MAX_AREA_HA}]"
        )

        # Constraint 2: Valid GeoJSON Polygon geometry
        geom = cell["geometry"]
        assert geom["type"] == "Polygon"
        coords = geom["coordinates"][0]

        # Constraint 3: Closed ring
        assert coords[0] == coords[-1], "Exterior ring must be closed"

        # Constraint 4: [longitude, latitude] coordinate ordering (India is ~68-98E, 6-38N)
        for pt in coords:
            lon, lat = pt[0], pt[1]
            assert 65.0 <= lon <= 100.0, f"Longitude {lon} out of Indian range"
            assert 5.0 <= lat <= 40.0, f"Latitude {lat} out of Indian range"

        # Constraint 5: Valid shapely polygon
        poly_shape = shape(geom)
        assert poly_shape.is_valid, "Polygon must be geometrically valid"


def test_soil_moisture_classification():
    """Verify hydrological soil moisture classification tiers."""
    assert classify_soil_moisture_tier(None) == "UNKNOWN"
    assert classify_soil_moisture_tier(0.08) == "LOW"
    assert classify_soil_moisture_tier(0.22) == "MODERATE"
    assert classify_soil_moisture_tier(0.38) == "HIGH"
    assert classify_soil_moisture_tier(0.52) == "VERY_HIGH"


def test_api_endpoints(client, db_session):
    """Test full REST endpoint workflow: status, hierarchy, initialize, polygons, soil GeoJSON."""
    # 1. Status endpoint
    resp = client.get("/api/agro-monitoring/status")
    assert resp.status_code == 200
    status_data = resp.json()
    assert "api_configured" in status_data
    assert "total_cells_generated" in status_data

    # 2. Hierarchy endpoint
    h_resp = client.get("/api/agro-monitoring/hierarchy")
    assert h_resp.status_code == 200
    hierarchy = h_resp.json()
    assert "Himachal Pradesh" in hierarchy

    # 3. Initialize grid (offline/DB-only mode by disabling immediate API registration to isolate test)
    init_resp = client.post(
        "/api/agro-monitoring/initialize",
        json={
            "scope": "district",
            "state_name": "Himachal Pradesh",
            "district_name": "Mandi",
            "register_with_agro": False,
            "batch_limit": 5,
        },
    )
    assert init_resp.status_code == 200
    init_data = init_resp.json()
    assert init_data["status"] == "success"
    assert init_data["result"]["total_cells_generated"] > 0
    assert (init_data["result"]["newly_inserted_in_db"] + init_data["result"]["already_existing_in_db"]) > 0

    # 4. Duplicate prevention: running again should detect existing
    init_resp_2 = client.post(
        "/api/agro-monitoring/initialize",
        json={
            "scope": "district",
            "state_name": "Himachal Pradesh",
            "district_name": "Mandi",
            "register_with_agro": False,
            "batch_limit": 5,
        },
    )
    assert init_resp_2.status_code == 200
    init_data_2 = init_resp_2.json()
    assert init_data_2["result"]["already_existing_in_db"] > 0
    assert init_data_2["result"]["newly_inserted_in_db"] == 0

    # 5. List polygons
    poly_resp = client.get("/api/agro-monitoring/polygons?district=Mandi")
    assert poly_resp.status_code == 200
    polys = poly_resp.json()
    assert len(polys) > 0
    assert polys[0]["district"] == "Mandi"
    assert polys[0]["status"] == "PENDING"

    # 6. Fetch GeoJSON
    geojson_resp = client.get("/api/agro-monitoring/soil?district=Mandi")
    assert geojson_resp.status_code == 200
    geojson_data = geojson_resp.json()
    assert geojson_data["type"] == "FeatureCollection"
    assert len(geojson_data["features"]) > 0
    assert "soil_moisture" in geojson_data["features"][0]["properties"]
