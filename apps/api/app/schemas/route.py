"""
apps/api/app/schemas/route.py
Flowshield — Evacuation Corridor & Routing Schemas (v3.0)
Enforces RECOMMENDED LOWER-RISK ROUTE labeling, off-network guards,
travel time, hazard exposure, and incident reporting.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class RouteResponse(BaseModel):
    id: str
    name: str
    state: Optional[str] = "Uttarakhand"
    district: Optional[str] = "Rudraprayag"
    origin_village_id: str
    origin_village_name: Optional[str] = None
    destination_shelter_id: str
    destination_shelter_name: Optional[str] = None
    distance_km: float
    estimated_travel_time_min: Optional[int] = None
    assessed_risk_score: int
    is_blocked: bool
    blockage_reason: Optional[str] = None
    is_river_crossing: bool
    hazard_cost_multiplier: Optional[float] = 1.0
    hazard_exposure: Optional[str] = "LOW"
    route_confidence: Optional[int] = 92
    last_verified: Optional[str] = "2026-09"
    route_label: str = "RECOMMENDED LOWER-RISK ROUTE"
    recommendation: Optional[str] = "CLEAR FOR TRANSIT"
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
    state: Optional[str] = None
    district: Optional[str] = None


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


class BlockageReportCreate(BaseModel):
    corridor_name: str
    route_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    blockage_type: str = Field("Landslide", description="Landslide, Flooding, Bridge Collapse, Debris, Fallen Trees, Road Damage, Unknown")
    severity: str = Field("HIGH", description="LOW, MEDIUM, HIGH, CRITICAL")
    description: Optional[str] = None
    reported_by: Optional[str] = "Field Responder"


class RoadIncidentResponse(BaseModel):
    id: str
    route_id: Optional[str] = None
    corridor_name: str
    state: str
    district: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    blockage_type: str
    severity: str
    description: Optional[str] = None
    reported_by: str
    status: str  # REPORTED, UNDER_REVIEW, VERIFIED, ACTIVE, CLEARED
    verification_status: str
    created_at: str
    updated_at: str
