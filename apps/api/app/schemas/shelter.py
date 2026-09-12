from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel


class ShelterResponse(BaseModel):
    id: str
    name: str
    type: str
    state: Optional[str] = "Uttarakhand"
    district: Optional[str] = "Rudraprayag"
    subdistrict_block: Optional[str] = None
    village_town: Optional[str] = None
    address: Optional[str] = None

    # Capacity & Occupancy (Nullable if not officially published)
    capacity: Optional[int] = None
    total_capacity: Optional[int] = None
    current_occupancy: Optional[int] = None
    available_capacity: Optional[int] = None
    occupancy_percentage: Optional[float] = None
    capacity_display: Optional[str] = "Not officially published"
    occupancy_display: Optional[str] = "Not currently available"
    available_display: Optional[str] = "Capacity unconfirmed"

    # Status & Operations
    status: str = "AVAILABLE"
    operational_status: Optional[str] = "OPERATIONAL"

    # Readiness Flags
    has_medical: bool = True
    medical_facility: bool = True
    has_power_backup: bool = True
    generator_available: bool = True
    water_available: bool = True
    food_available: bool = True
    toilets_available: bool = True
    electricity_available: bool = True
    communication_available: bool = True
    wheelchair_accessible: bool = False
    is_24x7: bool = True

    # Contact & Authority
    managing_authority: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None

    # Location & Distance
    latitude: float
    longitude: float
    distance_km: Optional[float] = None
    estimated_travel_time_min: Optional[int] = None

    # Source Provenance & Trust
    source_name: Optional[str] = "Official Government Source"
    source_url: Optional[str] = None
    source_type: Optional[str] = "OFFICIAL_DDMP"
    source_last_verified: Optional[str] = None
    verification_status: str = "VERIFIED"
    confidence_score: int = 85

    # Multi-factor Evaluation (When ranked)
    suitability_score: Optional[float] = None
    recommendation_label: Optional[str] = None
    rationale: Optional[List[str]] = None
    is_safe_haven: Optional[bool] = True
    hazard_exposure_score: Optional[float] = 10.0
    corridor_id: Optional[str] = None
    corridor_name: Optional[str] = None
    corridor_blocked: Optional[bool] = None

    class Config:
        from_attributes = True
