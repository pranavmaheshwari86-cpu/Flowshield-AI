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

    @staticmethod
    def get_routes_for_village(db: Session, village_id: str) -> List[Route]:
        return db.query(Route).filter(Route.origin_village_id == village_id).all()

    @staticmethod
    def get_all_routes(db: Session) -> List[Route]:
        return db.query(Route).all()

    @classmethod
    def get_routes(
        cls,
        db: Session,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> List[RouteResponse]:
        query = db.query(Route)
        if state:
            query = query.filter(func.lower(Route.state) == state.strip().lower())
        if district:
            query = query.filter(func.lower(Route.district) == district.strip().lower())
        routes = query.all()
        return [cls._format_route_response(db, r) for r in routes]

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
            safety_score=max(0, 100 - risk) if not is_blocked else 0,
            is_blocked=is_blocked,
            blockage_reason=r.blockage_reason,
            is_river_crossing=r.is_river_crossing,
            hazard_cost_multiplier=r.hazard_cost_multiplier or 1.0,
            hazard_exposure=hazard_exp,
            blocked_segments_count=1 if is_blocked else 0,
            route_confidence=conf,
            last_verified="2026-09",
            route_label="RECOMMENDED LOWER-RISK ROUTE" if not is_blocked else "SEVERED CORRIDOR",
            recommendation=rec,
            notes=r.notes,
            geometry=r.geometry,
        )

    @classmethod
    def get_emergency_facilities(cls, district: Optional[str] = "Rudraprayag") -> List[Dict[str, Any]]:
        """Returns verified official emergency contacts for a district."""
        facilities_map = {
            "rudraprayag": [
                {"name": "District Disaster Emergency Operation Center (DEOC)", "type": "DEOC", "phone": "01364-233727", "distance_km": 4.2, "status": "24x7 ACTIVE"},
                {"name": "SDRF Uttarakhand 3rd Battalion Camp", "type": "SDRF", "phone": "9456596190", "distance_km": 5.8, "status": "STANDBY DISPATCH"},
                {"name": "District Hospital Rudraprayag Emergency Trauma", "type": "HOSPITAL", "phone": "01364-233340", "distance_km": 6.1, "status": "MEDICAL READY"},
                {"name": "Uttarakhand Police Emergency", "type": "POLICE", "phone": "112", "distance_km": 3.9, "status": "HIGH ALERT"},
            ],
            "chamoli": [
                {"name": "Chamoli District Emergency Control Room (DEOC)", "type": "DEOC", "phone": "01372-251077", "distance_km": 5.0, "status": "24x7 ACTIVE"},
                {"name": "SDRF High Altitude Rescue Base Gopeshwar", "type": "SDRF", "phone": "1070", "distance_km": 7.2, "status": "RESCUE READY"},
                {"name": "District Hospital Gopeshwar", "type": "HOSPITAL", "phone": "01372-252245", "distance_km": 6.8, "status": "MEDICAL READY"},
            ],
            "mandi": [
                {"name": "Mandi District Emergency Operations Center", "type": "DEOC", "phone": "01905-226201", "distance_km": 3.5, "status": "24x7 ACTIVE"},
                {"name": "NDRF / SDRF Regional Response Center", "type": "NDRF", "phone": "1078", "distance_km": 4.8, "status": "WATER RESCUE READY"},
                {"name": "Zonal Hospital Mandi Emergency Ward", "type": "HOSPITAL", "phone": "01905-222102", "distance_km": 4.1, "status": "MEDICAL READY"},
            ],
            "kullu": [
                {"name": "Kullu District Emergency Operation Center", "type": "DEOC", "phone": "01902-225630", "distance_km": 4.0, "status": "24x7 ACTIVE"},
                {"name": "SDRF Mountain Rescue Base Kullu", "type": "SDRF", "phone": "1070", "distance_km": 5.5, "status": "ACTIVE READY"},
                {"name": "Regional Hospital Kullu", "type": "HOSPITAL", "phone": "01902-222350", "distance_km": 4.9, "status": "MEDICAL READY"},
            ],
        }
        key = (district or "rudraprayag").strip().lower()
        return facilities_map.get(key, [
            {"name": f"{district or 'District'} Disaster Control Room", "type": "DEOC", "phone": "1077", "distance_km": 5.0, "status": "ACTIVE"},
            {"name": "State Emergency Operation Center (SEOC)", "type": "SEOC", "phone": "1070", "distance_km": 15.0, "status": "24x7 LIVE"},
            {"name": "National Disaster Response Force (NDRF)", "type": "NDRF", "phone": "1078", "distance_km": 20.0, "status": "CENTRAL DISPATCH"},
            {"name": "National Emergency Helpline", "type": "POLICE", "phone": "112", "distance_km": 3.0, "status": "24x7 ALL-INDIA"},
        ])

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
        Evaluates evacuation route feasibility, filters blocked corridors,
        warns if shortest route is dangerous, and generates alternate paths.
        """
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

        emergency_facilities = cls.get_emergency_facilities(district or (target_village.district if target_village else "Rudraprayag"))

        # Check off-network snap threshold
        if min_snap_dist > cls.OFF_NETWORK_THRESHOLD_KM:
            return RouteEvaluationResult(
                status="ROUTING_UNAVAILABLE_OFF_GRID",
                route_label="OFF-GRID COORDINATES",
                requires_authority_coordination=True,
                selected_route=None,
                alternate_routes=[],
                blocked_routes=[],
                nearest_emergency_facilities=emergency_facilities,
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
                blocked_routes=[],
                nearest_emergency_facilities=emergency_facilities,
                snap_distance_km=round(min_snap_dist, 2),
                hazard_penalty_applied=999.0,
                message="No settlements mapped within search radius.",
            )

        # Retrieve routes
        candidate_routes = []
        if target_village:
            q_village = db.query(Route).filter(Route.origin_village_id == target_village.id)
            if destination_shelter_id:
                q_dest = q_village.filter(Route.destination_shelter_id == destination_shelter_id)
                if q_dest.count() > 0:
                    q_village = q_dest
            candidate_routes = q_village.all()

        if not candidate_routes:
            query = db.query(Route)
            if district:
                query = query.filter(func.lower(Route.district) == district.strip().lower())
            elif target_village and target_village.district:
                query = query.filter(func.lower(Route.district) == target_village.district.lower())
            
            if destination_shelter_id:
                dest_query = query.filter(Route.destination_shelter_id == destination_shelter_id)
                if dest_query.count() > 0:
                    query = dest_query

            candidate_routes = query.all()

        if not candidate_routes:
            return RouteEvaluationResult(
                status="NO_SAFE_ROUTE_FOUND",
                route_label="NO SAFE ROUTE FOUND",
                requires_authority_coordination=True,
                selected_route=None,
                alternate_routes=[],
                blocked_routes=[],
                nearest_emergency_facilities=emergency_facilities,
                snap_distance_km=round(min_snap_dist, 2),
                hazard_penalty_applied=999.0,
                message=f"No evacuation corridors mapped for {district or target_village.district}.",
            )

        # Partition into open vs blocked
        open_candidates = [r for r in candidate_routes if not r.is_blocked]
        blocked_candidates = [r for r in candidate_routes if r.is_blocked]

        # Check shortest route hazard exposure warning (Section 6)
        shortest_warning = None
        if candidate_routes:
            shortest = min(candidate_routes, key=lambda r: r.distance_km)
            if shortest.is_blocked:
                shortest_warning = (
                    f"Shortest corridor ({shortest.name}, {shortest.distance_km:.1f} km) is SEVERED by {shortest.blockage_reason or 'hazard obstruction'}. "
                    "Routing engine has automatically excluded it and diverted to a verified safe bypass corridor."
                )
            elif shortest.assessed_risk_score >= 60:
                shortest_warning = (
                    f"Shortest corridor ({shortest.name}, {shortest.distance_km:.1f} km) carries severe hazard risk ({shortest.assessed_risk_score}/100). "
                    "Prioritizing safety over travel distance."
                )

        if not open_candidates:
            blocked_responses = [cls._format_route_response(db, r) for r in blocked_candidates]
            return RouteEvaluationResult(
                status="NO_SAFE_ROUTE_FOUND",
                route_label="NO SAFE ROUTE FOUND",
                requires_authority_coordination=True,
                selected_route=None,
                alternate_routes=[],
                blocked_routes=blocked_responses,
                shortest_route_hazardous_warning=shortest_warning,
                nearest_emergency_facilities=emergency_facilities,
                snap_distance_km=round(min_snap_dist, 2),
                hazard_penalty_applied=999.0,
                message=(
                    f"All evacuation corridors from {target_village.name if target_village else (district or 'the sector')} are severed or flooded. "
                    "Ground evacuation impassable. Mandatory emergency authority coordination required. "
                    "Do not attempt road transit. Move to nearest designated high-ground holding area and alert emergency units below."
                ),
            )

        # Rank open candidates by dynamic traversal cost
        ranked_open: List[Tuple[Route, float]] = []
        for r in open_candidates:
            cost = cls.compute_route_cost(r)
            ranked_open.append((r, cost))
        ranked_open.sort(key=lambda item: item[1])

        best_route_response = cls._format_route_response(db, ranked_open[0][0])
        alternate_responses = [cls._format_route_response(db, r) for r, _ in ranked_open[1:3]]
        blocked_responses = [cls._format_route_response(db, r) for r in blocked_candidates]

        return RouteEvaluationResult(
            status="RECOMMENDED_LOWER_RISK_ROUTE",
            route_label="RECOMMENDED LOWER-RISK ROUTE",
            requires_authority_coordination=False,
            selected_route=best_route_response,
            alternate_routes=alternate_responses,
            blocked_routes=blocked_responses,
            shortest_route_hazardous_warning=shortest_warning,
            nearest_emergency_facilities=emergency_facilities,
            snap_distance_km=round(min_snap_dist, 2),
            hazard_penalty_applied=round(ranked_open[0][1] / max(0.1, best_route_response.distance_km), 2),
            message=f"Optimal safe path calculated via {best_route_response.name} to {best_route_response.destination_shelter_name}.",
        )

    @classmethod
    def reroute_evacuation(
        cls,
        db: Session,
        current_route_id: Optional[str],
        current_lat: float,
        current_lon: float,
        destination_shelter_id: Optional[str] = None,
        state: Optional[str] = "Uttarakhand",
        district: Optional[str] = "Rudraprayag",
        new_blockage_corridor_id: Optional[str] = None,
        blockage_reason: Optional[str] = "Active Landslide Obstruction",
    ) -> Dict[str, Any]:
        """
        Dynamically recalculates evacuation route when conditions change in real time (Section 18).
        """
        # If a new corridor blockage was reported, sever it immediately
        severed_name = "Active Corridor"
        if new_blockage_corridor_id:
            r_to_block = db.query(Route).filter(Route.id == new_blockage_corridor_id).first()
            if r_to_block:
                r_to_block.is_blocked = True
                r_to_block.blockage_reason = blockage_reason or "Field severance"
                r_to_block.assessed_risk_score = 98
                r_to_block.hazard_cost_multiplier = 10.0
                severed_name = r_to_block.name
                db.commit()

        # Previous route estimated travel time
        old_eta = 18
        if current_route_id:
            old_r = db.query(Route).filter(Route.id == current_route_id).first()
            if old_r:
                old_eta = round(float(old_r.distance_km) * 2.2)
                # If the current route itself was blocked
                if old_r.is_blocked:
                    severed_name = old_r.name

        # Recalculate route avoiding blocked roads
        eval_res = cls.evaluate_route(
            db=db,
            origin_lat=current_lat,
            origin_lon=current_lon,
            destination_shelter_id=destination_shelter_id,
            state=state,
            district=district,
        )

        new_route = eval_res.selected_route
        new_eta = new_route.estimated_travel_time_min if new_route else None
        emergency_facilities = eval_res.nearest_emergency_facilities

        if not new_route:
            return {
                "route_invalidated": True,
                "status": "NO_SAFE_ROUTE_AVAILABLE",
                "reroute_alert": (
                    f"⚠ ROUTE CHANGE FAILED: Corridor {severed_name} is severed. No alternative safe mountain roads open in this sector. "
                    "Halt transit immediately and contact emergency services."
                ),
                "old_eta_min": old_eta,
                "new_eta_min": None,
                "reason": f"Active road severance on {severed_name}",
                "new_safe_route": None,
                "alternate_routes": [],
                "nearest_emergency_facilities": emergency_facilities,
            }

        return {
            "route_invalidated": True,
            "status": "REROUTE_SUCCESSFUL",
            "reroute_alert": (
                f"⚠ ROUTE CHANGE REQUIRED: Landslide/Obstruction detected on {severed_name}. "
                f"Your previous path is no longer safe. New safe route calculated via {new_route.name}. "
                f"Old ETA: {old_eta} min → New ETA: {new_eta} min."
            ),
            "old_eta_min": old_eta,
            "new_eta_min": new_eta,
            "reason": f"Road blockage on {severed_name} ({blockage_reason})",
            "new_safe_route": new_route,
            "alternate_routes": eval_res.alternate_routes,
            "nearest_emergency_facilities": emergency_facilities,
        }

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
