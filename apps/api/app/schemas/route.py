"""
apps/api/app/schemas/route.py
Flowshield — Evacuation Corridor & Routing Schemas (v2.4)
Enforces RECOMMENDED LOWER-RISK ROUTE labeling, off-network guards, and NO_SAFE_ROUTE_FOUND states.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class RouteResponse(BaseModel):
    id: str
    name: str
    origin_village_id: str
    origin_village_name: Optional[str] = None
    destination_shelter_id: str
    destination_shelter_name: Optional[str] = None
    distance_km: float
    assessed_risk_score: int
    is_blocked: bool
    blockage_reason: Optional[str] = None
    is_river_crossing: bool
    hazard_cost_multiplier: Optional[float] = 1.0
    route_label: str = "RECOMMENDED LOWER-RISK ROUTE"
    notes: Optional[str] = None
    geometry: Dict[str, Any]

    class Config:
        from_attributes = True


class RouteAssessmentReport(BaseModel):
    selected_route: Optional[RouteResponse] = None
    alternate_routes: List[RouteResponse] = []
    status: str = "RECOMMENDED_LOWER_RISK_ROUTE"
    requires_authority_coordination: bool = False
    disclaimer: str = (
        "Advisory Lower-Risk Route Assessment. Dynamic hazards, flash floods, and debris flow "
        "may alter road viability rapidly. Strictly follow instructions of local DDMA and SDRF."
    )


class RouteEvaluateRequest(BaseModel):
    origin_latitude: float = Field(..., ge=-90.0, le=90.0)
    origin_longitude: float = Field(..., ge=-180.0, le=180.0)
    village_id: Optional[str] = None
    destination_shelter_id: Optional[str] = None


class RouteEvaluationResult(BaseModel):
    status: str  # RECOMMENDED_LOWER_RISK_ROUTE, NO_SAFE_ROUTE_FOUND, ROUTING_UNAVAILABLE_OFF_GRID
    route_label: str
    requires_authority_coordination: bool
    selected_route: Optional[RouteResponse] = None
    alternate_routes: List[RouteResponse] = []
    snap_distance_km: float
    hazard_penalty_applied: float = 1.0
    message: str
    disclaimer: str = (
        "Advisory evacuation routing. Ground conditions can change instantaneously in mountain catchments. "
        "Follow official civil defense directives. Autonomous rescue dispatching is disabled."
    )
