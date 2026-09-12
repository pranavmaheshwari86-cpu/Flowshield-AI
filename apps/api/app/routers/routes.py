"""
apps/api/app/routers/routes.py
Flowshield — Evacuation Corridor & Routing Endpoints (v2.4)
Exposes route listing, village corridors, dynamic hazard evaluation, and blockage toggling.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.route import Route
from ..models.village import Village
from ..models.shelter import Shelter
from ..schemas.route import (
    RouteResponse,
    RouteAssessmentReport,
    RouteEvaluateRequest,
    RouteEvaluationResult,
)
from ..services.route_service import route_service
from ..auth.dependencies import RoleChecker

router = APIRouter(prefix="/routes", tags=["Route Assessment"])


class BlockageReportRequest(BaseModel):
    is_blocked: bool
    blockage_reason: Optional[str] = None
    hazard_cost_multiplier: Optional[float] = 10.0


@router.get("", response_model=List[RouteResponse])
def list_routes(db: Session = Depends(get_db)):
    routes = route_service.get_all_routes(db)
    results = []
    for r in routes:
        v = db.query(Village).filter(Village.id == r.origin_village_id).first()
        s = db.query(Shelter).filter(Shelter.id == r.destination_shelter_id).first()
        results.append(
            RouteResponse(
                id=r.id,
                name=r.name,
                origin_village_id=r.origin_village_id,
                origin_village_name=v.name if v else None,
                destination_shelter_id=r.destination_shelter_id,
                destination_shelter_name=s.name if s else None,
                distance_km=r.distance_km,
                assessed_risk_score=r.assessed_risk_score,
                is_blocked=r.is_blocked,
                blockage_reason=r.blockage_reason,
                is_river_crossing=r.is_river_crossing,
                hazard_cost_multiplier=r.hazard_cost_multiplier,
                route_label="RECOMMENDED LOWER-RISK ROUTE",
                notes=r.notes,
                geometry=r.geometry,
            )
        )
    return results


@router.get("/village/{village_id}", response_model=RouteAssessmentReport)
def get_routes_for_village(village_id: str, db: Session = Depends(get_db)):
    routes = route_service.get_routes_for_village(db, village_id)
    if not routes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No precomputed evacuation routes found for this settlement",
        )

    v = db.query(Village).filter(Village.id == village_id).first()

    route_objs = []
    for r in routes:
        s = db.query(Shelter).filter(Shelter.id == r.destination_shelter_id).first()
        cost = route_service.compute_route_cost(r)
        route_objs.append((
            RouteResponse(
                id=r.id,
                name=r.name,
                origin_village_id=r.origin_village_id,
                origin_village_name=v.name if v else None,
                destination_shelter_id=r.destination_shelter_id,
                destination_shelter_name=s.name if s else None,
                distance_km=r.distance_km,
                assessed_risk_score=r.assessed_risk_score,
                is_blocked=r.is_blocked,
                blockage_reason=r.blockage_reason,
                is_river_crossing=r.is_river_crossing,
                hazard_cost_multiplier=r.hazard_cost_multiplier,
                route_label="RECOMMENDED LOWER-RISK ROUTE",
                notes=r.notes,
                geometry=r.geometry,
            ),
            cost
        ))

    # Sort by cost ascending
    route_objs.sort(key=lambda x: x[1])
    sorted_routes = [item[0] for item in route_objs]

    # Check if all routes are blocked
    all_blocked = all(r.is_blocked for r in sorted_routes)
    if all_blocked:
        return RouteAssessmentReport(
            selected_route=None,
            alternate_routes=sorted_routes,
            status="NO_SAFE_ROUTE_FOUND",
            requires_authority_coordination=True,
            disclaimer="All evacuation corridors are severed. Mandatory emergency authority coordination required.",
        )

    return RouteAssessmentReport(
        selected_route=sorted_routes[0],
        alternate_routes=sorted_routes[1:],
        status="RECOMMENDED_LOWER_RISK_ROUTE",
        requires_authority_coordination=False,
    )


@router.post("/evaluate", response_model=RouteEvaluationResult)
def evaluate_evacuation_route(req: RouteEvaluateRequest, db: Session = Depends(get_db)):
    """
    Evaluates dynamic route safety from given coordinates.
    Enforces 1.5 km off-network snap limits and hazard cost penalization.
    """
    return route_service.evaluate_route(
        db=db,
        origin_lat=req.origin_latitude,
        origin_lon=req.origin_longitude,
        village_id=req.village_id,
        destination_shelter_id=req.destination_shelter_id,
    )


@router.post("/blockage/{route_id}", response_model=RouteResponse)
def report_route_blockage(
    route_id: str,
    req: BlockageReportRequest,
    db: Session = Depends(get_db),
    _user=Depends(RoleChecker(["AUTHORITY", "RESPONDER", "ADMIN"])),
):
    """
    Tactical field endpoint for Responders and Authorities to mark road blockages.
    Immediately severs or restores corridor in graph routing.
    """
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route with id '{route_id}' not found.",
        )

    route.is_blocked = req.is_blocked
    route.blockage_reason = req.blockage_reason if req.is_blocked else None
    if req.is_blocked:
        route.assessed_risk_score = 95
        route.hazard_cost_multiplier = float(req.hazard_cost_multiplier or 10.0)
    else:
        route.assessed_risk_score = 15
        route.hazard_cost_multiplier = 1.0

    db.commit()
    db.refresh(route)

    v = db.query(Village).filter(Village.id == route.origin_village_id).first()
    s = db.query(Shelter).filter(Shelter.id == route.destination_shelter_id).first()

    return RouteResponse(
        id=route.id,
        name=route.name,
        origin_village_id=route.origin_village_id,
        origin_village_name=v.name if v else None,
        destination_shelter_id=route.destination_shelter_id,
        destination_shelter_name=s.name if s else None,
        distance_km=route.distance_km,
        assessed_risk_score=route.assessed_risk_score,
        is_blocked=route.is_blocked,
        blockage_reason=route.blockage_reason,
        is_river_crossing=route.is_river_crossing,
        hazard_cost_multiplier=route.hazard_cost_multiplier,
        route_label="RECOMMENDED LOWER-RISK ROUTE",
        notes=route.notes,
        geometry=route.geometry,
    )
