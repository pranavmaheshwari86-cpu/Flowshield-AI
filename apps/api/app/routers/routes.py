"""
apps/api/app/routers/routes.py
Flowshield — Evacuation Corridor & Routing Endpoints (v3.0)
Exposes route listing, village corridors, dynamic hazard evaluation,
incident reporting, and blockage toggling.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.route import Route
from ..models.village import Village
from ..models.shelter import Shelter
from ..models.road_incident import RoadIncident
from ..models.user import User
from ..auth.dependencies import RoleChecker
from ..schemas.route import (
    RouteResponse,
    RouteAssessmentReport,
    RouteEvaluateRequest,
    RouteEvaluationResult,
    BlockageReportCreate,
    RoadIncidentResponse,
)
from ..services.route_service import route_service

router = APIRouter(prefix="/routes", tags=["Route Assessment"])


class BlockageToggleRequest(BaseModel):
    is_blocked: bool
    blockage_reason: Optional[str] = None
    hazard_cost_multiplier: Optional[float] = 10.0


class IncidentStatusUpdate(BaseModel):
    status: str  # REPORTED, UNDER_REVIEW, VERIFIED, ACTIVE, CLEARED
    verified_by: Optional[str] = "Command Center Operator"


@router.get("", response_model=List[RouteResponse])
def list_routes(
    state: Optional[str] = Query(None, description="Filter routes by state"),
    district: Optional[str] = Query(None, description="Filter routes by district"),
    db: Session = Depends(get_db),
):
    """Returns evacuation corridors with travel time, hazard exposure, and risk scores."""
    return route_service.get_routes(db, state=state, district=district)


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
        cost = route_service.compute_route_cost(r)
        route_objs.append((route_service._format_route_response(db, r), cost))

    # Sort by traversal cost ascending
    route_objs.sort(key=lambda x: x[1])
    sorted_routes = [item[0] for item in route_objs]

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
        state=req.state,
        district=req.district,
    )


@router.post("/blockage/{route_id}", response_model=RouteResponse)
def toggle_route_blockage(
    route_id: str,
    req: BlockageToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["AUTHORITY", "RESPONDER", "ADMIN"])),
):
    """
    Tactical field endpoint to mark or clear a road blockage on a route corridor.
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
    return route_service._format_route_response(db, route)


@router.post("/incidents", response_model=RoadIncidentResponse)
def report_road_incident(req: BlockageReportCreate, db: Session = Depends(get_db)):
    """
    Creates a new blockage / obstruction incident report from citizen or field responder.
    """
    incident = route_service.report_incident(db, req)
    return RoadIncidentResponse(
        id=incident.id,
        route_id=incident.route_id,
        corridor_name=incident.corridor_name,
        state=incident.state,
        district=incident.district,
        latitude=incident.latitude,
        longitude=incident.longitude,
        blockage_type=incident.blockage_type,
        severity=incident.severity,
        description=incident.description,
        reported_by=incident.reported_by,
        status=incident.status,
        verification_status=incident.verification_status,
        created_at=incident.created_at.isoformat(),
        updated_at=incident.updated_at.isoformat(),
    )


@router.get("/incidents", response_model=List[RoadIncidentResponse])
def list_road_incidents(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Lists field blockage incidents."""
    incidents = route_service.list_incidents(db, state=state, district=district, status=status)
    return [
        RoadIncidentResponse(
            id=inc.id,
            route_id=inc.route_id,
            corridor_name=inc.corridor_name,
            state=inc.state,
            district=inc.district,
            latitude=inc.latitude,
            longitude=inc.longitude,
            blockage_type=inc.blockage_type,
            severity=inc.severity,
            description=inc.description,
            reported_by=inc.reported_by,
            status=inc.status,
            verification_status=inc.verification_status,
            created_at=inc.created_at.isoformat(),
            updated_at=inc.updated_at.isoformat(),
        )
        for inc in incidents
    ]
