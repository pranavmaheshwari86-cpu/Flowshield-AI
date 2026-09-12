from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.village import Village, RiskZone
from ..models.shelter import Shelter
from ..models.river import River
from ..models.route import Route
from ..models.risk_snapshot import RiskSnapshot
from ..models.alert import Alert

router = APIRouter(prefix="/map", tags=["GIS Map Data"])


@router.get("/geojson")
def get_map_geojson(
    layers: str = Query(
        "villages,risk_zones,rivers,shelters,routes",
        description="Comma-separated layers to return: villages, risk_zones, rivers, shelters, routes",
    ),
    state: Optional[str] = Query(
        None,
        description="Optional state filter (e.g. Bihar, Uttar Pradesh, Uttarakhand)",
    ),
    db: Session = Depends(get_db),
):
    requested_layers = [l.strip().lower() for l in layers.split(",") if l.strip()]
    if "zones" in requested_layers and "risk_zones" not in requested_layers:
        requested_layers.append("risk_zones")
    features = []

    # 1. Villages Layer
    if "villages" in requested_layers:
        v_query = db.query(Village)
        if state and state.upper() != "ALL":
            v_query = v_query.filter(Village.state.ilike(f"%{state}%"))
        villages = v_query.all()
        for v in villages:
            latest_snap = (
                db.query(RiskSnapshot)
                .filter(RiskSnapshot.village_id == v.id)
                .order_by(RiskSnapshot.timestamp.desc())
                .first()
            )
            has_alert = (
                db.query(Alert)
                .filter(Alert.village_id == v.id, Alert.status == "ACTIVE")
                .first()
                is not None
            )
            features.append(
                {
                    "type": "Feature",
                    "id": f"village_{v.id}",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [v.longitude, v.latitude],
                    },
                    "properties": {
                        "layer": "villages",
                        "id": v.id,
                        "name": v.name,
                        "tehsil": v.tehsil,
                        "district": v.district,
                        "elevation": v.elevation,
                        "population": v.population,
                        "distance_to_river": v.distance_to_river,
                        "risk_score": latest_snap.risk_score if latest_snap else 10,
                        "risk_level": latest_snap.risk_level if latest_snap else "LOW",
                        "has_active_alert": has_alert,
                    },
                }
            )

    # 2. Precomputed Voronoi Risk Zones
    if "risk_zones" in requested_layers:
        risk_zones = db.query(RiskZone).all()
        for rz in risk_zones:
            latest_snap = (
                db.query(RiskSnapshot)
                .filter(RiskSnapshot.village_id == rz.village_id)
                .order_by(RiskSnapshot.timestamp.desc())
                .first()
            )
            v = db.query(Village).filter(Village.id == rz.village_id).first()
            features.append(
                {
                    "type": "Feature",
                    "id": f"zone_{rz.id}",
                    "geometry": rz.geometry,
                    "properties": {
                        "layer": "risk_zones",
                        "village_id": rz.village_id,
                        "village_name": v.name if v else None,
                        "risk_score": latest_snap.risk_score if latest_snap else 10,
                        "risk_level": latest_snap.risk_level if latest_snap else "LOW",
                    },
                }
            )

    # 3. Rivers Layer
    if "rivers" in requested_layers:
        rivers = db.query(River).all()
        for riv in rivers:
            features.append(
                {
                    "type": "Feature",
                    "id": f"river_{riv.id}",
                    "geometry": riv.geometry,
                    "properties": {
                        "layer": "rivers",
                        "id": riv.id,
                        "name": riv.name,
                        "danger_level": riv.danger_level_meters,
                        "warning_level": riv.warning_level_meters,
                        "gauge_station": riv.gauge_station,
                    },
                }
            )

    # 4. Shelters Layer
    if "shelters" in requested_layers:
        shelters = db.query(Shelter).all()
        for s in shelters:
            features.append(
                {
                    "type": "Feature",
                    "id": f"shelter_{s.id}",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [s.longitude, s.latitude],
                    },
                    "properties": {
                        "layer": "shelters",
                        "id": s.id,
                        "name": s.name,
                        "type": s.type,
                        "total_capacity": s.total_capacity,
                        "current_occupancy": s.current_occupancy,
                        "available_capacity": s.available_capacity,
                        "status": s.status,
                        "contact_phone": s.contact_phone,
                    },
                }
            )

    # 5. Routes Layer
    if "routes" in requested_layers:
        routes = db.query(Route).all()
        for r in routes:
            features.append(
                {
                    "type": "Feature",
                    "id": f"route_{r.id}",
                    "geometry": r.geometry,
                    "properties": {
                        "layer": "routes",
                        "id": r.id,
                        "name": r.name,
                        "distance_km": r.distance_km,
                        "assessed_risk_score": r.assessed_risk_score,
                        "is_blocked": r.is_blocked,
                        "blockage_reason": r.blockage_reason,
                        "is_river_crossing": r.is_river_crossing,
                    },
                }
            )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


@router.get("/geojson/{layer_name}")
def get_single_map_layer(layer_name: str, db: Session = Depends(get_db)):
    return get_map_geojson(layers=layer_name, db=db)
