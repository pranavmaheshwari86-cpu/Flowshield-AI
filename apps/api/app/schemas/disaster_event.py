from typing import List, Optional, Any
from pydantic import BaseModel


class DisasterEventBase(BaseModel):
    event_id: str
    disaster_type: str
    severity: str
    status: str
    state: str
    district: str
    location_name: str
    latitude: float
    longitude: float
    affected_radius_km: float
    affected_population: int
    affected_villages: Optional[List[str]] = []
    affected_corridors: Optional[List[str]] = []
    confidence: int
    source: str
    description: Optional[str] = None
    recommended_action: Optional[str] = "IMMEDIATE EVACUATION"
    is_demo: int = 0


class DisasterEventResponse(DisasterEventBase):
    id: str
    start_time: Optional[str] = None
    detected_at: Optional[str] = None
    last_updated: Optional[str] = None

    class Config:
        from_attributes = True


class DisasterSimulationRequest(BaseModel):
    state: str = "Uttarakhand"
    district: str = "Rudraprayag"
    disaster_type: str = "MULTI_HAZARD"
    severity: str = "CRITICAL"
