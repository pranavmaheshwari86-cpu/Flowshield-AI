"""
apps/api/app/services/route_service.py
Flowshield — Hazard-Weighted Evacuation Routing Engine (v2.4)
Enforces RECOMMENDED LOWER-RISK ROUTE labeling, 1.5 km off-network snap guards,
hazard-weighted cost penalization, and NO_SAFE_ROUTE_FOUND safety fallback.
"""

import math
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..models.route import Route
from ..models.village import Village
from ..models.shelter import Shelter
from ..schemas.route import RouteResponse, RouteAssessmentReport, RouteEvaluationResult


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

    @staticmethod
    def get_routes_for_village(db: Session, village_id: str) -> List[Route]:
        return db.query(Route).filter(Route.origin_village_id == village_id).all()

    @staticmethod
    def get_all_routes(db: Session) -> List[Route]:
        return db.query(Route).all()

    @classmethod
    def evaluate_route(
        cls,
        db: Session,
        origin_lat: float,
        origin_lon: float,
        village_id: Optional[str] = None,
        destination_shelter_id: Optional[str] = None,
    ) -> RouteEvaluationResult:
        """
        Evaluates nearest evacuation route with off-network guard and blockage detection.
        """
        # 1. Resolve origin village
        target_village = None
        if village_id:
            target_village = db.query(Village).filter(Village.id == village_id).first()

        all_villages = db.query(Village).all()
        min_snap_dist = float("inf")
        nearest_village = None

        for v in all_villages:
            dist = cls.haversine_distance_km(origin_lat, origin_lon, v.latitude, v.longitude)
            if dist < min_snap_dist:
                min_snap_dist = dist
                nearest_village = v

        if not target_village:
            target_village = nearest_village

        # 2. Check 1.5 km off-network snap threshold
        if min_snap_dist > cls.OFF_NETWORK_THRESHOLD_KM:
            return RouteEvaluationResult(
                status="ROUTING_UNAVAILABLE_OFF_GRID",
                route_label="OFF-GRID COORDINATES",
                requires_authority_coordination=True,
                selected_route=None,
                alternate_routes=[],
                snap_distance_km=round(min_snap_dist, 2),
                message=(
                    f"Coordinates are {min_snap_dist:.2f} km from the nearest road corridor "
                    f"(limit: {cls.OFF_NETWORK_THRESHOLD_KM} km). Standard road routing unavailable. "
                    "Requires immediate direct coordination with local DDMA / disaster authorities."
                ),
            )

        # 3. Retrieve available candidate routes
        if not target_village:
            return RouteEvaluationResult(
                status="NO_SAFE_ROUTE_FOUND",
                route_label="NO SAFE ROUTE FOUND",
                requires_authority_coordination=True,
                selected_route=None,
                alternate_routes=[],
                snap_distance_km=round(min_snap_dist, 2),
                message="No settlements mapped within search radius.",
            )

        query = db.query(Route).filter(Route.origin_village_id == target_village.id)
        if destination_shelter_id:
            query = query.filter(Route.destination_shelter_id == destination_shelter_id)
        routes = query.all()

        if not routes:
            return RouteEvaluationResult(
                status="NO_SAFE_ROUTE_FOUND",
                route_label="NO SAFE ROUTE FOUND",
                requires_authority_coordination=True,
                selected_route=None,
                alternate_routes=[],
                snap_distance_km=round(min_snap_dist, 2),
                message=f"No evacuation corridors defined from {target_village.name}.",
            )

        # 4. Rank candidate routes by hazard-weighted traversal cost
        ranked: List[Tuple[Route, float]] = []
        for r in routes:
            cost = cls.compute_route_cost(r)
            ranked.append((r, cost))

        # Sort: lowest cost first
        ranked.sort(key=lambda item: item[1])

        # Check if all routes are severed / blocked
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

        # Build RouteResponse objects
        route_responses = []
        for r, cost in ranked:
            s = db.query(Shelter).filter(Shelter.id == r.destination_shelter_id).first()
            route_responses.append(
                RouteResponse(
                    id=r.id,
                    name=r.name,
                    origin_village_id=r.origin_village_id,
                    origin_village_name=target_village.name,
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

    @staticmethod
    def update_route_blockages_for_simulation(db: Session, stage: int, substep: int):
        """Dynamically flags routes crossing river causeways as blocked during flood escalation."""
        routes = db.query(Route).all()
        for r in routes:
            if stage >= 3 and r.is_river_crossing:
                r.is_blocked = True
                r.blockage_reason = "Submerged low-level causeway — flash flood inundation"
                r.assessed_risk_score = 90
                r.hazard_cost_multiplier = 10.0
            elif stage >= 2:
                r.is_blocked = False
                r.blockage_reason = None
                r.assessed_risk_score = 55 if r.is_river_crossing else 25
                r.hazard_cost_multiplier = 2.5 if r.is_river_crossing else 1.2
            else:
                r.is_blocked = False
                r.blockage_reason = None
                r.assessed_risk_score = 15 if r.is_river_crossing else 5
                r.hazard_cost_multiplier = 1.0
        db.commit()


route_service = RouteService()
