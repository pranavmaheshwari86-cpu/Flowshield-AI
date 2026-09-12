from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ShelterResponse(BaseModel):
    id: str
    name: str
    type: str
    total_capacity: int
    current_occupancy: int
    available_capacity: int
    occupancy_percentage: float
    status: str
    has_medical: bool
    has_power_backup: bool
    contact_person: str
    contact_phone: str
    distance_km: Optional[float] = None
    latitude: float
    longitude: float

    class Config:
        from_attributes = True
