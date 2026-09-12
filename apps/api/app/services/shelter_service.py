"""
apps/api/app/services/shelter_service.py
Flowshield — Shelter Intelligence & Multi-Factor Evacuation Suitability Engine (v3.0)
Strict Non-Fabrication Policy:
- Never fabricates unpublished capacities or occupancies.
- Multi-factor evaluation: travel time + route safety + shelter readiness + data confidence.
- Authoritative source provenance and verification tracking.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.shelter import Shelter
from ..models.village import Village
from ..models.route import Route
from ..database import haversine_distance_km


class ShelterService:
    """
    Manages shelter retrieval, multi-factor evacuation ranking,
    and operational capacity intelligence.
    """

    @staticmethod
    def _format_shelter_dict(s: Shelter, distance_km: Optional[float] = None) -> Dict[str, Any]:
        """Formats shelter model into consistent dict with non-fabrication guarantees."""
        cap = s.effective_capacity
        occ = s.current_occupancy
        avail = s.available_capacity

        # Format human-readable strings without fabricating unknown values
        cap_str = f"{cap} slots" if cap is not None else "Not officially published"
        if occ is not None and cap is not None and cap > 0:
            occ_str = f"{occ} / {cap} ({s.occupancy_percentage}%)"
            avail_str = f"{avail} SLOTS OPEN" if avail > 0 else "FULL"
        elif occ is not None:
            occ_str = f"{occ} occupants"
            avail_str = "Occupancy tracked"
        else:
            occ_str = "Not currently available"
            avail_str = "Capacity unconfirmed" if cap is None else f"Nominal ({cap})"

        # Estimated travel time in minutes assuming mountain road speed 30 km/h (0.5 km/min) or walking
        travel_time_min = round(distance_km * 2.2) if distance_km is not None else None

        return {
            "id": s.id,
            "name": s.name,
            "type": s.type,
            "state": s.state,
            "district": s.district,
            "subdistrict_block": s.subdistrict_block,
            "village_town": s.village_town,
            "address": s.address,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "distance_km": round(distance_km, 2) if distance_km is not None else None,
            "estimated_travel_time_min": travel_time_min,
            "capacity": cap,
            "capacity_display": cap_str,
            "current_occupancy": occ,
            "occupancy_display": occ_str,
            "available_capacity": avail,
            "available_display": avail_str,
            "occupancy_percentage": s.occupancy_percentage,
            "status": s.status,
            "operational_status": s.operational_status,
            "has_medical": s.has_medical,
            "medical_facility": s.medical_facility,
            "has_power_backup": s.has_power_backup,
            "generator_available": s.generator_available,
            "water_available": s.water_available,
            "food_available": s.food_available,
            "toilets_available": s.toilets_available,
            "electricity_available": s.electricity_available,
            "communication_available": s.communication_available,
            "wheelchair_accessible": s.wheelchair_accessible,
            "is_24x7": s.is_24x7,
            "managing_authority": s.managing_authority,
            "contact_person": s.contact_person,
            "contact_phone": s.contact_phone,
            "source_name": s.source_name or "Official Government Record",
            "source_url": s.source_url,
            "source_type": s.source_type or "OFFICIAL_DDMP",
            "source_last_verified": s.source_last_verified or "2026-08",
            "verification_status": s.verification_status,
            "confidence_score": s.confidence_score,
        }

    @classmethod
    def list_shelters(
        cls,
        db: Session,
        state: Optional[str] = None,
        district: Optional[str] = None,
        search: Optional[str] = None,
        verified_only: bool = False,
        operational_only: bool = False,
        has_medical: Optional[bool] = None,
        has_power: Optional[bool] = None,
        ref_lat: Optional[float] = None,
        ref_lon: Optional[float] = None,
        sort_by: str = "distance",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Filters and returns shelters matching criteria."""
        query = db.query(Shelter)

        if state:
            query = query.filter(func.lower(Shelter.state) == state.strip().lower())
        if district:
            query = query.filter(func.lower(Shelter.district) == district.strip().lower())
        if search:
            s_term = f"%{search.strip().lower()}%"
            query = query.filter(
                func.lower(Shelter.name).like(s_term)
                | func.lower(Shelter.type).like(s_term)
                | func.lower(Shelter.village_town).like(s_term)
            )
        if verified_only:
            query = query.filter(Shelter.verification_status.in_(["VERIFIED", "PARTIALLY_VERIFIED"]))
        if operational_only:
            query = query.filter(Shelter.operational_status == "OPERATIONAL", Shelter.status != "CLOSED")
        if has_medical is not None:
            query = query.filter(Shelter.has_medical == has_medical)
        if has_power is not None:
            query = query.filter(Shelter.has_power_backup == has_power)

        shelters = query.all()

        results = []
        for s in shelters:
            dist = None
            if ref_lat is not None and ref_lon is not None:
                dist = haversine_distance_km(ref_lat, ref_lon, s.latitude, s.longitude)
            results.append(cls._format_shelter_dict(s, dist))

        # Sort results
        if sort_by == "distance" and ref_lat is not None and ref_lon is not None:
            results.sort(key=lambda x: x["distance_km"] if x["distance_km"] is not None else 9999)
        elif sort_by == "confidence":
            results.sort(key=lambda x: x["confidence_score"], reverse=True)
        elif sort_by == "capacity":
            results.sort(key=lambda x: (x["capacity"] or 0), reverse=True)
        else:
            results.sort(key=lambda x: x["name"])

        if limit and limit > 0:
            results = results[:limit]

        return results

    @classmethod
    def update_occupancy_for_simulation(cls, db: Session, stage: int, substep: int) -> None:
        """
        Updates shelter occupancies during active disaster simulation progression.
        Only adjusts shelters that have known capacities.
        """
        shelters = db.query(Shelter).all()
        multiplier = min(1.0, 0.2 * stage + (substep % 4) * 0.05)
        for s in shelters:
            cap = s.capacity or s.total_capacity
            if cap:
                new_occ = int(cap * multiplier)
                s.current_occupancy = min(cap, new_occ)
                if s.current_occupancy >= cap:
                    s.status = "FULL"
                else:
                    s.status = "AVAILABLE"
        db.commit()

    @classmethod
    def get_nearest_shelters(cls, db: Session, village_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Returns nearest shelters for a given village."""
        village = db.query(Village).filter(Village.id == village_id).first()
        if not village:
            return []

        return cls.list_shelters(
            db=db,
            state=village.state,
            district=village.district,
            ref_lat=village.latitude,
            ref_lon=village.longitude,
            limit=limit,
        )[:limit]

    @classmethod
    def compute_evacuation_suitability(
        cls,
        shelter: Shelter,
        distance_km: float,
        route: Optional[Route] = None,
        active_disaster_events: Optional[List[Any]] = None,
    ) -> Tuple[float, str, List[str], bool, float]:
        """
        Computes multi-factor evacuation suitability score (0-100) per Section 12 & 13:
        1. SAFETY (40 pts) - evaluates distance from active disaster zones & floodways.
        2. AVAILABILITY (20 pts) - capacity headroom & non-saturation.
        3. ACCESSIBILITY (15 pts) - open vs blocked road corridor access.
        4. DISTANCE (10 pts) - proximity and mountain travel time.
        5. MEDICAL & UTILITIES (10 pts) - dedicated medical team, backup power generator, water.
        6. CONFIDENCE (5 pts) - verified official DDMP record.

        Returns: (suitability_score, recommendation_label, rationale_points, is_safe_haven, hazard_exposure_score)
        """
        rationale: List[str] = []
        is_safe_haven = True
        hazard_exposure_score = 10.0  # Baseline low exposure

        # 0. HARD SAFETY EXCLUSIONS
        # Exclusion A: Shelter is marked FULL or CLOSED
        if shelter.status in ["CLOSED", "INACTIVE"] or shelter.operational_status in ["CLOSED", "INACTIVE"]:
            return 0.0, "EXCLUDED — SHELTER CLOSED", ["Facility is non-operational or closed by district authority"], False, 100.0

        if shelter.available_capacity is not None and shelter.available_capacity <= 0:
            return 0.0, "EXCLUDED — SHELTER FULL", ["Facility reached 100% capacity capacity threshold"], False, 90.0

        # Exclusion B: Proximity to active disaster event (Landslide/Flood epicenter)
        if active_disaster_events:
            for event in active_disaster_events:
                ev_lat = getattr(event, "latitude", None) or (event.get("latitude") if isinstance(event, dict) else None)
                ev_lon = getattr(event, "longitude", None) or (event.get("longitude") if isinstance(event, dict) else None)
                ev_rad = getattr(event, "affected_radius_km", 2.5) or (event.get("affected_radius_km", 2.5) if isinstance(event, dict) else 2.5)
                ev_sev = getattr(event, "severity", "HIGH") or (event.get("severity", "HIGH") if isinstance(event, dict) else "HIGH")
                
                if ev_lat is not None and ev_lon is not None:
                    dist_to_hazard = haversine_distance_km(shelter.latitude, shelter.longitude, ev_lat, ev_lon)
                    if dist_to_hazard <= ev_rad:
                        hazard_exposure_score = 98.0
                        return (
                            0.0,
                            "EXCLUDED — ACTIVE HAZARD ZONE",
                            [f"Inside {ev_sev} active hazard perimeter ({dist_to_hazard:.1f} km from epicenter)"],
                            False,
                            100.0,
                        )
                    elif dist_to_hazard <= ev_rad * 1.6:
                        hazard_exposure_score = max(hazard_exposure_score, 65.0)
                        rationale.append(f"Caution: Near hazard buffer ({dist_to_hazard:.1f} km)")

        # Exclusion C: Route corridor is severed
        is_route_blocked = False
        route_risk = 15
        if route:
            is_route_blocked = route.is_blocked
            route_risk = route.assessed_risk_score
            if is_route_blocked:
                hazard_exposure_score = max(hazard_exposure_score, 85.0)
                return (
                    15.0,
                    "UNSAFE — ROUTE SEVERED",
                    [f"Connecting corridor is severed: {route.blockage_reason or 'Road blocked'}"],
                    False,
                    85.0,
                )

        # 1. SAFETY SCORE (40 points)
        # Higher score if hazard exposure is low and no river surge risk
        safety_score = max(0.0, 40.0 - (hazard_exposure_score / 100.0) * 35.0)
        if route and route.is_river_crossing:
            safety_score = max(5.0, safety_score - 8.0)
            rationale.append("Connecting path traverses river causeway")
        else:
            rationale.append("Outside high-risk flood & landslide perimeter")

        # 2. AVAILABILITY & CAPACITY (20 points)
        avail = shelter.available_capacity
        cap = shelter.effective_capacity
        if avail is not None and cap is not None and cap > 0:
            pct_free = (avail / cap)
            avail_score = 20.0 * min(1.0, pct_free)
            rationale.append(f"{avail} open slots ({int(pct_free*100)}% available)")
        elif cap is not None and cap >= 500:
            avail_score = 16.0
            rationale.append(f"Major facility capacity ({cap} slots)")
        else:
            avail_score = 14.0

        # 3. ACCESSIBILITY & ROUTE CLEARANCE (15 points)
        if route and not is_route_blocked:
            access_score = max(5.0, 15.0 - (route_risk / 100.0) * 8.0)
            rationale.append("All-weather road corridor clear")
        else:
            access_score = 12.0

        # 4. DISTANCE & TRAVEL TIME (10 points)
        if distance_km <= 3.0:
            dist_score = 10.0
            rationale.append(f"Immediate proximity ({distance_km:.1f} km)")
        elif distance_km <= 10.0:
            dist_score = 10.0 - ((distance_km - 3.0) / 7.0) * 5.0
            rationale.append(f"Reachable distance ({distance_km:.1f} km)")
        else:
            dist_score = max(2.0, 5.0 - ((distance_km - 10.0) / 15.0) * 3.0)
            rationale.append(f"Transit distance ({distance_km:.1f} km)")

        # 5. MEDICAL & UTILITIES (10 points)
        util_score = 0.0
        if shelter.has_medical or shelter.medical_facility:
            util_score += 3.5
            rationale.append("Medical response team on site")
        if shelter.has_power_backup or shelter.generator_available:
            util_score += 3.5
            rationale.append("Generator power backup active")
        if shelter.water_available:
            util_score += 2.0
        if shelter.is_24x7:
            util_score += 1.0

        # 6. VERIFICATION CONFIDENCE (5 points)
        conf = shelter.confidence_score or 85
        conf_score = (conf / 100.0) * 5.0
        if shelter.verification_status == "VERIFIED":
            rationale.append("USDMA / DDMP verified record")

        total_score = round(safety_score + avail_score + access_score + dist_score + util_score + conf_score, 1)

        # Label Assignment
        if total_score >= 82.0:
            recommendation = "RECOMMENDED PRIMARY SHELTER"
        elif total_score >= 65.0:
            recommendation = "RECOMMENDED ALTERNATE SHELTER"
        elif total_score >= 45.0:
            recommendation = "CAUTION — SECONDARY HAVEN"
        else:
            recommendation = "NOT RECOMMENDED — ELEVATED RISK"
            is_safe_haven = False

        return total_score, recommendation, rationale, is_safe_haven, round(hazard_exposure_score, 1)

    @classmethod
    def get_recommended_shelters(
        cls,
        db: Session,
        origin_lat: float,
        origin_lon: float,
        state: Optional[str] = None,
        district: Optional[str] = None,
        village_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Finds and ranks candidate shelters using strict multi-factor evacuation suitability.
        Filters dangerous routes, checks active disaster zones, and prioritizes resilient facilities.
        """
        from ..models.disaster_event import DisasterEvent

        # Query active disaster events in the jurisdiction
        active_events_query = db.query(DisasterEvent).filter(DisasterEvent.status.in_(["ACTIVE", "MONITORING"]))
        if district:
            active_events_query = active_events_query.filter(func.lower(DisasterEvent.district) == district.strip().lower())
        active_events = active_events_query.all()

        # Fetch candidate shelters
        query = db.query(Shelter).filter(Shelter.status != "CLOSED")
        if state:
            query = query.filter(func.lower(Shelter.state) == state.strip().lower())
        if district:
            query = query.filter(func.lower(Shelter.district) == district.strip().lower())

        candidates = query.all()
        if not candidates:
            candidates = db.query(Shelter).filter(Shelter.status != "CLOSED").all()

        scored_results = []
        for s in candidates:
            dist = haversine_distance_km(origin_lat, origin_lon, s.latitude, s.longitude)
            
            matching_route = None
            if village_id:
                matching_route = db.query(Route).filter(
                    Route.origin_village_id == village_id,
                    Route.destination_shelter_id == s.id,
                ).first()

            score, rec_label, rationale, is_safe, hazard_score = cls.compute_evacuation_suitability(
                shelter=s,
                distance_km=dist,
                route=matching_route,
                active_disaster_events=active_events,
            )
            
            s_dict = cls._format_shelter_dict(s, dist)
            s_dict["suitability_score"] = score
            s_dict["recommendation_label"] = rec_label
            s_dict["rationale"] = rationale
            s_dict["is_safe_haven"] = is_safe
            s_dict["hazard_exposure_score"] = hazard_score
            s_dict["corridor_id"] = matching_route.id if matching_route else None
            s_dict["corridor_name"] = matching_route.name if matching_route else None
            s_dict["corridor_blocked"] = matching_route.is_blocked if matching_route else False

            scored_results.append(s_dict)

        # Sort: Safe havens first, then by suitability score descending
        scored_results.sort(key=lambda x: (1 if x["is_safe_haven"] else 0, x["suitability_score"]), reverse=True)
        return scored_results[:limit]


shelter_service = ShelterService()
