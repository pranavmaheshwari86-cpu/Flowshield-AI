from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.shelter import Shelter
from ..models.village import Village
from ..database import haversine_distance_km


class ShelterService:
    """
    Computes spatial proximity between settlements and emergency shelters,
    manages real-time capacities and evacuation intake flows.
    """

    @staticmethod
    def get_nearest_shelters(db: Session, village_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        village = db.query(Village).filter(Village.id == village_id).first()
        if not village:
            return []

        all_shelters = db.query(Shelter).filter(Shelter.status != "CLOSED").all()

        results = []
        for s in all_shelters:
            dist = haversine_distance_km(village.latitude, village.longitude, s.latitude, s.longitude)
            results.append(
                {
                    "id": s.id,
                    "name": s.name,
                    "type": s.type,
                    "total_capacity": s.total_capacity,
                    "current_occupancy": s.current_occupancy,
                    "available_capacity": s.available_capacity,
                    "occupancy_percentage": s.occupancy_percentage,
                    "status": s.status,
                    "has_medical": s.has_medical,
                    "has_power_backup": s.has_power_backup,
                    "contact_person": s.contact_person,
                    "contact_phone": s.contact_phone,
                    "distance_km": dist,
                    "latitude": s.latitude,
                    "longitude": s.longitude,
                }
            )

        results.sort(key=lambda x: x["distance_km"])
        return results[:limit]

    @staticmethod
    def update_occupancy_for_simulation(db: Session, stage: int, substep: int):
        """
        Dynamically adjusts shelter occupancies during higher simulation stages (simulating evacuation intake).
        """
        shelters = db.query(Shelter).all()
        # Stage 0: 5-15% occupancy
        # Stage 1: 15-25%
        # Stage 2: 25-45%
        # Stage 3: 45-70%
        # Stage 4: 70-90%
        intake_factors = {0: 0.10, 1: 0.20, 2: 0.35, 3: 0.60, 4: 0.85}
        base_intake = intake_factors.get(stage, 0.10)

        for s in shelters:
            target = int(s.total_capacity * base_intake)
            s.current_occupancy = min(s.total_capacity, target)
            if s.current_occupancy >= s.total_capacity:
                s.status = "FULL"
            elif s.current_occupancy >= s.total_capacity * 0.8:
                s.status = "NEAR_CAPACITY"
            else:
                s.status = "AVAILABLE"

        db.commit()


shelter_service = ShelterService()
