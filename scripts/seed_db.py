"""
Database Seeding Script for Flowshield
Initializes tables, seeds GIS entities (villages, shelters, rivers, routes),
computes Voronoi catchment polygons, creates authority demo user, and sets baseline state.
"""

import os
import sys
import json
import numpy as np
from datetime import datetime, timezone
from shapely.geometry import Point, Polygon, box, mapping
from scipy.spatial import Voronoi

# Ensure app package is reachable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../apps/api")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ml")))

from app.database import engine, Base, SessionLocal
from app.models.village import Village, RiskZone
from app.models.shelter import Shelter
from app.models.river import River
from app.models.route import Route
from app.models.user import User
from app.models.observation import EnvironmentalObservation
from app.models.prediction import Prediction
from app.models.risk_snapshot import RiskSnapshot
from app.models.simulation import Simulation
from app.models.alert import Alert
from app.auth.jwt_handler import hash_password
from app.services.prediction_service import prediction_service
from app.services.risk_engine import risk_engine
from app.services.simulation_engine import simulation_engine, SimulationEngine


def compute_voronoi_catchments(villages_data: list) -> dict:
    """
    Computes Voronoi polygons around village points clipped to the Mandakini valley bounding box.
    Returns a dict mapping village_id -> GeoJSON polygon dict.
    """
    coords = []
    v_ids = []
    for f in villages_data:
        lon, lat = f["geometry"]["coordinates"]
        coords.append([lon, lat])
        v_ids.append(f["properties"]["id"])

    pts = np.array(coords)
    # Bounding box of Mandakini watershed with padding
    min_lon, max_lon = pts[:, 0].min() - 0.08, pts[:, 0].max() + 0.08
    min_lat, max_lat = pts[:, 1].min() - 0.08, pts[:, 1].max() + 0.08
    boundary_box = box(min_lon, min_lat, max_lon, max_lat)

    # Pad points to bound outer Voronoi cells
    pad = 0.5
    dummy_pts = np.array([
        [min_lon - pad, min_lat - pad],
        [min_lon - pad, max_lat + pad],
        [max_lon + pad, min_lat - pad],
        [max_lon + pad, max_lat + pad],
    ])
    all_pts = np.vstack([pts, dummy_pts])

    vor = Voronoi(all_pts)
    catchments = {}

    for i in range(len(pts)):
        region_idx = vor.point_region[i]
        region = vor.regions[region_idx]
        if not region or -1 in region:
            continue
        poly_coords = [vor.vertices[v] for v in region]
        poly = Polygon(poly_coords)
        clipped = poly.intersection(boundary_box)
        if not clipped.is_empty and clipped.geom_type == "Polygon":
            catchments[v_ids[i]] = mapping(clipped)
        else:
            # Fallback buffer around point if intersection was non-standard
            catchments[v_ids[i]] = mapping(Point(pts[i]).buffer(0.02))

    return catchments


def seed_initial_observations_and_baseline_predictions(db):
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
    obs_path = os.path.join(root_dir, "data", "seed", "initial_observations.json")
    if not os.path.exists(obs_path):
        print(f"Warning: {obs_path} not found")
        return

    with open(obs_path, "r") as f:
        obs_list = json.load(f)

    # Initialize model if needed
    prediction_service.load_artifacts()

    now = datetime.now(timezone.utc)
    for obs_data in obs_list:
        v_id = obs_data["village_id"]
        village = db.query(Village).filter(Village.id == v_id).first()
        if not village:
            continue

        obs = EnvironmentalObservation(
            village_id=v_id,
            timestamp=now,
            rainfall_1h=obs_data["rainfall_1h"],
            rainfall_3h=obs_data["rainfall_3h"],
            rainfall_6h=obs_data["rainfall_6h"],
            rainfall_24h=obs_data["rainfall_24h"],
            rainfall_intensity=obs_data["rainfall_intensity"],
            soil_moisture=obs_data["soil_moisture"],
            river_level=obs_data["river_level"],
            river_level_change=obs_data["river_level_change"],
            source=obs_data.get("source", "Demonstration Telemetry Network"),
            is_simulated=obs_data.get("is_simulated", True),
            quality_score=obs_data.get("quality_score", 0.98),
            freshness_seconds=obs_data.get("freshness_seconds", 15),
        )
        db.add(obs)
        db.flush()

        # Run Prediction
        feature_dict = {
            "rainfall_1h": obs.rainfall_1h,
            "rainfall_3h": obs.rainfall_3h,
            "rainfall_6h": obs.rainfall_6h,
            "rainfall_24h": obs.rainfall_24h,
            "rainfall_intensity": obs.rainfall_intensity,
            "soil_moisture": obs.soil_moisture,
            "river_level": obs.river_level,
            "river_level_change": obs.river_level_change,
            "elevation": village.elevation,
            "slope": village.slope,
            "distance_to_river": village.distance_to_river,
            "historical_flood_frequency": village.historical_flood_frequency,
        }
        prob, quality, top_contribs = prediction_service.predict(
            feature_dict, obs.quality_score, obs.freshness_seconds
        )

        pred = Prediction(
            village_id=v_id,
            observation_id=obs.id,
            flood_probability=prob,
            prediction_quality=quality,
            model_version=prediction_service.metadata.get("model_version", "xgb-v1.0.0") if prediction_service.metadata else "xgb-v1.0.0",
            feature_contributions=top_contribs,
        )
        db.add(pred)
        db.flush()

        # Risk Engine
        risk_score, risk_lvl, _, _ = risk_engine.compute_operational_risk(
            flood_probability=prob,
            trend_factor=1.0,
            vulnerability_index=village.vulnerability_index,
            data_quality_score=obs.quality_score,
            freshness_seconds=obs.freshness_seconds,
        )

        snap = RiskSnapshot(
            village_id=v_id,
            prediction_id=pred.id,
            risk_score=risk_score,
            risk_level=risk_lvl,
            trend="STABLE",
            timestamp=now,
        )
        db.add(snap)

    db.commit()
    print("Baseline observations, predictions, and risk snapshots seeded.")


def seed_database():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
    seed_dir = os.path.join(root_dir, "data", "seed")

    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Authority, Responder, and Admin Users
        seed_users = [
            ("demo", "commander@flowshield.gov.in", "AUTHORITY", "District Disaster Management Commander"),
            ("responder", "sdrf.team1@flowshield.gov.in", "RESPONDER", "SDRF Quick Response Field Unit"),
            ("admin", "admin@flowshield.gov.in", "ADMIN", "Disaster Intelligence Administrator"),
            ("citizen", "citizen@flowshield.gov.in", "CITIZEN", "Citizen Observer"),
        ]
        for u_name, u_email, u_role, u_fn in seed_users:
            existing = db.query(User).filter(User.username == u_name).first()
            if not existing:
                u = User(
                    username=u_name,
                    email=u_email,
                    hashed_password=hash_password("flowshield2026"),
                    role=u_role,
                    full_name=u_fn,
                )
                db.add(u)
        db.commit()
        print("Users seeded: demo (AUTHORITY), responder (RESPONDER), admin (ADMIN), citizen (CITIZEN)")

        # 2. Villages & Voronoi Risk Zones
        villages_file = os.path.join(seed_dir, "villages.geojson")
        with open(villages_file, "r") as f:
            v_geojson = json.load(f)

        features = v_geojson["features"]
        voronoi_map = compute_voronoi_catchments(features)

        for feat in features:
            props = feat["properties"]
            v_id = props["id"]
            lon, lat = feat["geometry"]["coordinates"]

            existing_v = db.query(Village).filter(Village.id == v_id).first()
            if not existing_v:
                v = Village(
                    id=v_id,
                    name=props["name"],
                    tehsil=props["tehsil"],
                    district=props["district"],
                    state=props.get("state", "Uttarakhand"),
                    population=props["population"],
                    elevation=props["elevation"],
                    slope=props["slope"],
                    distance_to_river=props["distance_to_river"],
                    historical_flood_frequency=props["historical_flood_frequency"],
                    vulnerability_index=props["vulnerability_index"],
                    latitude=lat,
                    longitude=lon,
                    geometry=feat["geometry"],
                )
                db.add(v)
                db.flush()

                # Seed Voronoi Catchment
                if v_id in voronoi_map:
                    rz = RiskZone(village_id=v_id, geometry=voronoi_map[v_id])
                    db.add(rz)

        db.commit()
        print(f"Seeded {len(features)} villages with Voronoi catchments.")

        # 3. Shelters
        shelters_file = os.path.join(seed_dir, "shelters.geojson")
        with open(shelters_file, "r") as f:
            s_geojson = json.load(f)

        for feat in s_geojson["features"]:
            props = feat["properties"]
            s_id = props["id"]
            lon, lat = feat["geometry"]["coordinates"]
            if not db.query(Shelter).filter(Shelter.id == s_id).first():
                s = Shelter(
                    id=s_id,
                    name=props["name"],
                    type=props["type"],
                    total_capacity=props["total_capacity"],
                    current_occupancy=props["current_occupancy"],
                    status=props["status"],
                    has_medical=props.get("has_medical", True),
                    has_power_backup=props.get("has_power_backup", True),
                    contact_person=props["contact_person"],
                    contact_phone=props["contact_phone"],
                    latitude=lat,
                    longitude=lon,
                    geometry=feat["geometry"],
                )
                db.add(s)
        db.commit()
        print(f"Seeded {len(s_geojson['features'])} shelters.")

        # 4. Rivers
        rivers_file = os.path.join(seed_dir, "rivers.geojson")
        with open(rivers_file, "r") as f:
            r_geojson = json.load(f)

        for feat in r_geojson["features"]:
            props = feat["properties"]
            r_id = props["id"]
            if not db.query(River).filter(River.id == r_id).first():
                riv = River(
                    id=r_id,
                    name=props["name"],
                    danger_level_meters=props["danger_level_meters"],
                    warning_level_meters=props["warning_level_meters"],
                    gauge_station=props.get("gauge_station"),
                    basin=props.get("basin"),
                    geometry=feat["geometry"],
                )
                db.add(riv)
        db.commit()
        print(f"Seeded {len(r_geojson['features'])} river reaches.")

        # 5. Routes
        routes_file = os.path.join(seed_dir, "routes.geojson")
        with open(routes_file, "r") as f:
            rt_geojson = json.load(f)

        for feat in rt_geojson["features"]:
            props = feat["properties"]
            rt_id = props["id"]
            if not db.query(Route).filter(Route.id == rt_id).first():
                rt = Route(
                    id=rt_id,
                    name=props["name"],
                    origin_village_id=props["origin_village_id"],
                    destination_shelter_id=props["destination_shelter_id"],
                    distance_km=props["distance_km"],
                    assessed_risk_score=props.get("assessed_risk_score", 10),
                    is_blocked=False,
                    is_river_crossing=props.get("is_river_crossing", False),
                    crossing_coordinates=props.get("crossing_coordinates"),
                    notes=props.get("notes"),
                    geometry=feat["geometry"],
                )
                db.add(rt)
        db.commit()
        print(f"Seeded {len(rt_geojson['features'])} evacuation routes.")

        # 6. Baseline observations & predictions
        seed_initial_observations_and_baseline_predictions(db)

        # 7. Default Simulation State
        SimulationEngine.get_or_create_simulation(db)

        # 8. Seed National Flood Intelligence (Live Sept 2026 ground truth)
        try:
            from seed_national_flood_data import seed_national_flood_data
            seed_national_flood_data()
        except ImportError:
            from scripts.seed_national_flood_data import seed_national_flood_data
            seed_national_flood_data()

        print("\nFlowshield database seed complete! System ready for baseline presentation.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
