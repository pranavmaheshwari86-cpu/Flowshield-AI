"""
apps/api/app/routers/agro_monitoring.py
Flowshield — AgroMonitoring Soil Moisture REST API Router
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.monitoring_polygon import MonitoringPolygon, SoilObservation
from ..schemas.agro_monitoring import (
    InitGridRequest,
    MonitoringPolygonOut,
    SoilObservationOut,
    AgroStatusResponse,
    SoilGeoJSONFeatureCollection,
    SoilGeoJSONFeature,
)
from ..services.agro_grid_service import agro_grid_service
from ..services.agro_monitoring_service import agro_monitoring_service, classify_soil_moisture_tier

router = APIRouter(tags=["AgroMonitoring Soil Moisture"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/status", response_model=AgroStatusResponse)
def get_agro_status(db: Session = Depends(get_db)):
    """Returns current system health, registered polygons count, and quota status."""
    total_cells = db.query(MonitoringPolygon).count()
    registered = db.query(MonitoringPolygon).filter(MonitoringPolygon.status == "REGISTERED").count()
    pending = db.query(MonitoringPolygon).filter(MonitoringPolygon.status == "PENDING").count()
    failed = db.query(MonitoringPolygon).filter(MonitoringPolygon.status == "FAILED").count()
    limit_exceeded = db.query(MonitoringPolygon).filter(MonitoringPolygon.status == "LIMIT_EXCEEDED").count()

    latest_obs = db.query(SoilObservation).order_by(SoilObservation.created_at.desc()).first()
    last_sync = latest_obs.created_at if latest_obs else None

    # Collect distinct states and districts currently in DB
    states = [r[0] for r in db.query(MonitoringPolygon.state).distinct().filter(MonitoringPolygon.state.isnot(None)).all()]
    districts = [r[0] for r in db.query(MonitoringPolygon.district).distinct().filter(MonitoringPolygon.district.isnot(None)).all()]

    plan_notice = None
    if limit_exceeded > 0:
        plan_notice = (
            f"{limit_exceeded} polygons hit AgroMonitoring plan limits. "
            f"{registered} polygons are active and streaming satellite telemetry."
        )

    return AgroStatusResponse(
        api_configured=agro_monitoring_service.is_configured(),
        total_cells_generated=total_cells,
        registered_polygons=registered,
        pending_polygons=pending,
        failed_polygons=failed,
        limit_exceeded_polygons=limit_exceeded,
        last_soil_sync=last_sync,
        plan_notice=plan_notice,
        active_states=sorted(states),
        active_districts=sorted(districts),
    )


@router.get("/hierarchy")
def get_administrative_hierarchy():
    """Returns all available Indian States and Districts from the administrative boundary dataset."""
    try:
        return agro_grid_service.get_hierarchy()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load administrative hierarchy: {str(e)}"
        )


@router.post("/initialize", status_code=status.HTTP_200_OK)
async def initialize_grid(
    req: InitGridRequest,
    db: Session = Depends(get_db),
):
    """
    Divides India, a State, or a District into AgroMonitoring-compliant polygons (1 - 3,000 ha),
    caches them in the database, and registers up to batch_limit with AgroMonitoring.
    """
    try:
        result = await agro_monitoring_service.initialize_grid_in_db(
            db=db,
            scope=req.scope,
            state_name=req.state_name,
            district_name=req.district_name,
            register_with_agro=req.register_with_agro,
            batch_limit=req.batch_limit,
        )
        return {"status": "success", "result": result}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Initialization failed: {str(e)}"
        )


@router.post("/initialize-india", status_code=status.HTTP_200_OK)
async def initialize_india(
    register_with_agro: bool = Query(default=True),
    batch_limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Convenience endpoint to initialize India-wide monitoring cells."""
    req = InitGridRequest(
        scope="all",
        register_with_agro=register_with_agro,
        batch_limit=batch_limit,
    )
    return await initialize_grid(req, db)


@router.get("/polygons", response_model=List[MonitoringPolygonOut])
def list_polygons(
    state: Optional[str] = None,
    district: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Lists monitoring polygons with latest soil moisture readings."""
    query = db.query(MonitoringPolygon)
    if state:
        query = query.filter(MonitoringPolygon.state.ilike(f"%{state}%"))
    if district:
        query = query.filter(MonitoringPolygon.district.ilike(f"%{district}%"))
    if status_filter:
        query = query.filter(MonitoringPolygon.status == status_filter.upper())

    polys = query.offset(offset).limit(limit).all()

    results = []
    for p in polys:
        latest_obs = p.observations[0] if p.observations else None
        moisture = latest_obs.soil_moisture if latest_obs else None
        tier = classify_soil_moisture_tier(moisture)

        # Convert Kelvin to Celsius if present
        soil_temp_c = (latest_obs.soil_temperature - 273.15) if (latest_obs and latest_obs.soil_temperature) else None
        surf_temp_c = (latest_obs.surface_temperature - 273.15) if (latest_obs and latest_obs.surface_temperature) else None

        results.append(
            MonitoringPolygonOut(
                id=p.id,
                agro_polygon_id=p.agro_polygon_id,
                name=p.name,
                country=p.country,
                state=p.state,
                district=p.district,
                area_hectares=p.area_hectares,
                centroid_lat=p.centroid_lat,
                centroid_lon=p.centroid_lon,
                status=p.status,
                error_message=p.error_message,
                last_soil_update=p.last_soil_update,
                latest_moisture=moisture,
                moisture_tier=tier,
                latest_soil_temp=round(soil_temp_c, 2) if soil_temp_c else None,
                latest_surface_temp=round(surf_temp_c, 2) if surf_temp_c else None,
            )
        )

    return results


@router.get("/soil", response_model=SoilGeoJSONFeatureCollection)
def get_soil_geojson(
    state: Optional[str] = None,
    district: Optional[str] = None,
    only_registered: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    """
    Returns GeoJSON FeatureCollection of monitoring polygons enriched with
    real satellite soil moisture data, temperatures, and risk classification tiers.
    Directly pluggable into Leaflet map.
    """
    query = db.query(MonitoringPolygon)
    if state:
        query = query.filter(MonitoringPolygon.state.ilike(f"%{state}%"))
    if district:
        query = query.filter(MonitoringPolygon.district.ilike(f"%{district}%"))
    if only_registered:
        query = query.filter(MonitoringPolygon.status == "REGISTERED")

    polys = query.all()

    features: List[SoilGeoJSONFeature] = []
    for p in polys:
        try:
            geom = json.loads(p.geometry_geojson)
        except Exception:
            continue

        latest_obs = p.observations[0] if p.observations else None
        moisture = latest_obs.soil_moisture if latest_obs else None
        tier = classify_soil_moisture_tier(moisture)

        soil_temp_c = (latest_obs.soil_temperature - 273.15) if (latest_obs and latest_obs.soil_temperature) else None
        surf_temp_c = (latest_obs.surface_temperature - 273.15) if (latest_obs and latest_obs.surface_temperature) else None

        properties = {
            "id": p.id,
            "agro_polygon_id": p.agro_polygon_id,
            "name": p.name,
            "country": p.country,
            "state": p.state,
            "district": p.district,
            "area_ha": p.area_hectares,
            "status": p.status,
            "centroid": [p.centroid_lat, p.centroid_lon],
            "soil_moisture": moisture,
            "moisture_tier": tier,
            "soil_temp_c": round(soil_temp_c, 1) if soil_temp_c is not None else None,
            "surface_temp_c": round(surf_temp_c, 1) if surf_temp_c is not None else None,
            "last_observation_dt": latest_obs.observation_timestamp.isoformat() if latest_obs else None,
        }

        features.append(
            SoilGeoJSONFeature(
                type="Feature",
                id=p.id,
                geometry=geom,
                properties=properties,
            )
        )

    return SoilGeoJSONFeatureCollection(
        type="FeatureCollection",
        features=features,
        metadata={
            "total_polygons": len(features),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "AgroMonitoring Soil Moisture API via FlowShield",
            "units": {
                "soil_moisture": "m3/m3",
                "temperature": "Celsius",
                "area": "Hectares",
            },
        },
    )


@router.get("/soil/{polygon_id}", response_model=List[SoilObservationOut])
def get_polygon_soil_history(polygon_id: str, db: Session = Depends(get_db)):
    """Returns historical time-series observations for a specific monitoring polygon."""
    poly = db.query(MonitoringPolygon).filter(MonitoringPolygon.id == polygon_id).first()
    if not poly:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitoring polygon not found")

    return poly.observations


@router.post("/sync", status_code=status.HTTP_200_OK)
async def sync_soil_data(db: Session = Depends(get_db)):
    """Triggers an on-demand satellite telemetry sync for all registered polygons."""
    if not agro_monitoring_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AGRO_API_KEY is not configured in the server environment."
        )

    updated = await agro_monitoring_service.sync_soil_observations(db)
    return {"status": "success", "updated_polygons": updated}
