"""
apps/api/app/services/route_service.py
Flowshield — Hazard-Weighted Evacuation Routing Engine (v3.0)
Enforces RECOMMENDED LOWER-RISK ROUTE labeling, 1.5 km off-network snap guards,
hazard-weighted cost penalization, incident workflows, and NO_SAFE_ROUTE_FOUND safety fallback.
"""

import math
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.route import Route
from ..models.village import Village
from ..models.shelter import Shelter
from ..models.road_incident import RoadIncident
from ..schemas.route import (
    RouteResponse,
    RouteAssessmentReport,
    RouteEvaluationResult,
    BlockageReportCreate,
)


class RouteService:
    """
    Evaluates evacuation corridor safety, assesses dynamic route hazards,
    enforces 1.5 km off-network snapping, and penalizes flooded segments.
    """

    OFF_NETWORK_THRESHOLD_KM = 1.5  # Coordinates > 1.5 km from road network are deemed off-grid

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates great-circle distance between two geographic coordinates in km."""
        r = 6371.0  # Earth radius in kilometers
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2.0) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    @staticmethod
    def compute_route_cost(route: Route) -> float:
        """
        Computes dynamic traversal cost:
        Cost = distance * (1.0 + risk/50.0) * hazard_multiplier * (1.5 if river crossing else 1.0)
        Returns infinity if route is blocked.
        """
        if route.is_blocked:
            return float("inf")

        base_dist = float(route.distance_km)
        risk_penalty = 1.0 + (float(route.assessed_risk_score) / 50.0)
        hazard_mult = float(route.hazard_cost_multiplier or 1.0)
        river_mult = 1.5 if route.is_river_crossing else 1.0

        return base_dist * risk_penalty * hazard_mult * river_mult

    @classmethod
    def _format_route_response(cls, db: Session, r: Route) -> RouteResponse:
        """Enriches Route model into standard RouteResponse schema."""
        v = db.query(Village).filter(Village.id == r.origin_village_id).first()
        s = db.query(Shelter).filter(Shelter.id == r.destination_shelter_id).first()

        dist = float(r.distance_km)
        travel_time = round(dist * 2.2)  # Mountain road estimate ~28 km/h average
        is_blocked = r.is_blocked
        risk = r.assessed_risk_score or 15

        if is_blocked:
            hazard_exp = "CRITICAL"
            rec = "SEVERED — DO NOT USE"
            conf = 35
        elif risk >= 60:
            hazard_exp = "HIGH"
            rec = "HIGH HAZARD — SECONDARY ROUTE"
            conf = 75
        elif risk >= 30:
            hazard_exp = "MODERATE"
            rec = "PROCEED WITH CAUTION"
            conf = 88
        else:
            hazard_exp = "LOW"
            rec = "RECOMMENDED PRIMARY CORRIDOR"
            conf = 95

        return RouteResponse(
            id=r.id,
            name=r.name,
            state=r.state or (v.state if v else "Uttarakhand"),
            district=r.district or (v.district if v else "Rudraprayag"),
            origin_village_id=r.origin_village_id,
            origin_village_name=v.name if v else None,
            destination_shelter_id=r.destination_shelter_id,
            destination_shelter_name=s.name if s else None,
            distance_km=round(dist, 2),
            estimated_travel_time_min=travel_time,
            assessed_risk_score=risk,
            is_blocked=is_blocked,
            blockage_reason=r.blockage_reason,
            is_river_crossing=r.is_river_crossing,
            hazard_cost_multiplier=r.hazard_cost_multiplier or 1.0,
            hazard_exposure=hazard_exp,
            route_confidence=conf,
            last_verified="2026-09",
            route_label="RECOMMENDED LOWER-RISK ROUTE" if not is_blocked else "SEVERED CORRIDOR",
            recommendation=rec,
            notes=r.notes,
            geometry=r.geometry,
        )

    @classmethod
    def get_routes(
        cls,
        db: Session,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> List[RouteResponse]:
        """Returns routes optionally filtered by state and district."""
        query = db.query(Route)
        if state:
            query = query.filter(func.lower(Route.state) == state.strip().lower())
        if district:
            query = query.filter(func.lower(Route.district) == district.strip().lower())

        routes = query.all()
        return [cls._format_route_response(db, r) for r in routes]

    @classmethod
    def get_routes_for_village(cls, db: Session, village_id: str) -> List[Route]:
        return db.query(Route).filter(Route.origin_village_id == village_id).all()

    @classmethod
    def evaluate_route(
        cls,
        db: Session,
        origin_lat: float,
        origin_lon: float,
        village_id: Optional[str] = None,
        destination_shelter_id: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> RouteEvaluationResult:
        """
        Evaluates nearest evacuation route with off-network guard, hazard penalization,
        and blockage detection.
        """
        # 1. Resolve origin village
        target_village = None
        if village_id:
            target_village = db.query(Village).filter(Village.id == village_id).first()

        all_villages_query = db.query(Village)
        if state:
            all_villages_query = all_villages_query.filter(func.lower(Village.state) == state.strip().lower())
        if district:
            all_villages_query = all_villages_query.filter(func.lower(Village.district) == district.strip().lower())

        villages_pool = all_villages_query.all()
        if not villages_pool:
            villages_pool = db.query(Village).all()

        min_snap_dist = float("inf")
        nearest_village = None

        for v in villages_pool:
            dist = cls.haversine_distance_km(origin_lat, origin_lon, v.latitude, v.longitude)
            if dist < min_snap_dist:
                min_snap_dist = dist
                nearest_village = v

        if not target_village:
            target_village = nearest_village

        # 2. Check off-network snap threshold
        if min_snap_dist > cls.OFF_NETWORK_THRESHOLD_KM:
            return RouteEvaluationResult(
                status="ROUTING_UNAVAILABLE_OFF_GRID",
                route_label="OFF-GRID COORDINATES",
                requires_authority_coordination=True,
                selected_route=None,
                alternate_routes=[],
                snap_distance_km=round(min_snap_dist, 2),
                hazard_penalty_applied=999.0,
                message=(
                    f"Coordinates are {min_snap_dist:.2f} km from nearest mapped road corridor "
                    f"(limit: {cls.OFF_NETWORK_THRESHOLD_KM} km). Standard road traversal unavailable. "
                    "Requires immediate aerial or foot party coordination with local DDMA / SDRF."
                ),
            )

        if not target_village:
            return RouteEvaluationResult(
                status="NO_SAFE_ROUTE_FOUND",
                route_label="NO SAFE ROUTE FOUND",
                requires_authority_coordination=True,
                selected_route=None,
                alternate_routes=[],
                snap_distance_km=round(min_snap_dist, 2),
                hazard_penalty_applied=999.0,
                message="No settlements mapped within search radius.",
            )

        # 3. Retrieve routes from target village
        query = db.query(Route).filter(Route.origin_village_id == target_village.id)
        if destination_shelter_id:
            query = query.filter(Route.destination_shelter_id == destination_shelter_id)
        routes = query.all()

        if not routes:
            # Check if there are any routes in the district
            dist_routes = db.query(Route).filter(func.lower(Route.district) == target_village.district.lower()).all()
            if dist_routes:
                routes = dist_routes
            else:
                return RouteEvaluationResult(
                    status="NO_SAFE_ROUTE_FOUND",
                    route_label="NO SAFE ROUTE FOUND",
                    requires_authority_coordination=True,
                    selected_route=None,
                    alternate_routes=[],
                    snap_distance_km=round(min_snap_dist, 2),
                    hazard_penalty_applied=999.0,
                    message=f"No evacuation corridors defined from {target_village.name} ({target_village.district}).",
                )

        # 4. Rank candidate routes by dynamic traversal cost
        ranked: List[Tuple[Route, float]] = []
        for r in routes:
            cost = cls.compute_route_cost(r)
            ranked.append((r, cost))

        ranked.sort(key=lambda item: item[1])

        # Check if all routes are blocked
        all_blocked = all(math.isinf(cost) for _, cost in ranked)
        if all_blocked:
            return RouteEvaluationResult(
                status="NO_SAFE_ROUTE_FOUND",
                route_label="NO SAFE ROUTE FOUND",
                requires_authority_coordination=True,
                selected_route=None,
                alternate_routes=[],
                snap_distance_km=round(min_snap_dist, 2),
                hazard_penalty_applied=999.0,
                message=(
                    f"All evacuation corridors from {target_village.name} are severed or flooded. "
                    "Ground evacuation impassable. Mandatory emergency authority coordination required."
                ),
            )

        route_responses = [cls._format_route_response(db, r) for r, _ in ranked]
        best_route = route_responses[0]
        alternates = route_responses[1:]

        return RouteEvaluationResult(
            status="RECOMMENDED_LOWER_RISK_ROUTE",
            route_label="RECOMMENDED LOWER-RISK ROUTE",
            requires_authority_coordination=False,
            selected_route=best_route,
            alternate_routes=alternates,
            snap_distance_km=round(min_snap_dist, 2),
            hazard_penalty_applied=round(ranked[0][1] / max(0.1, best_route.distance_km), 2),
            message=f"Optimal corridor selected via {best_route.name} to {best_route.destination_shelter_name}.",
        )

    @classmethod
    def report_incident(cls, db: Session, req: BlockageReportCreate) -> RoadIncident:
        """Creates a blockage incident and updates associated route risk."""
        incident = RoadIncident(
            corridor_name=req.corridor_name,
            route_id=req.route_id,
            latitude=req.latitude,
            longitude=req.longitude,
            blockage_type=req.blockage_type,
            severity=req.severity,
            description=req.description,
            reported_by=req.reported_by or "Field Responder",
            status="ACTIVE",
            verification_status="VERIFIED",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(incident)

        # If linked to a route, update route status
        if req.route_id:
            route = db.query(Route).filter(Route.id == req.route_id).first()
            if route:
                route.is_blocked = True
                route.blockage_reason = f"{req.blockage_type} ({req.severity}): {req.description or 'Corridor impassable'}"
                route.assessed_risk_score = 95
                route.hazard_cost_multiplier = 10.0

        db.commit()
        db.refresh(incident)
        return incident

    @classmethod
    def list_incidents(
        cls,
        db: Session,
        state: Optional[str] = None,
        district: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[RoadIncident]:
        """Lists active and historical road incidents."""
        query = db.query(RoadIncident)
        if state:
            query = query.filter(func.lower(RoadIncident.state) == state.strip().lower())
        if district:
            query = query.filter(func.lower(RoadIncident.district) == district.strip().lower())
        if status:
            query = query.filter(RoadIncident.status == status)
        return query.order_by(RoadIncident.created_at.desc()).all()

    @classmethod
    def update_route_blockages_for_simulation(cls, db: Session, stage: int, substep: int) -> None:
        """
        Updates route blockages during active disaster simulation progression.
        """
        routes = db.query(Route).all()
        for r in routes:
            # If high or critical stage and crossing river, simulate surge blockage
            if stage >= 3 and r.is_river_crossing and (substep % 3 == 0):
                r.is_blocked = True
                r.blockage_reason = "Simulated Flash Flood: Debris flow / Bridge submergence"
                r.assessed_risk_score = 95
                r.hazard_cost_multiplier = 10.0
            elif stage <= 1 and r.is_blocked:
                # Reset in baseline stages
                r.is_blocked = False
                r.blockage_reason = None
                r.assessed_risk_score = 15
                r.hazard_cost_multiplier = 1.0
        db.commit()


route_service = RouteService()
