import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON
from ..database import Base


class Shelter(Base):
    __tablename__ = "shelters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), nullable=False)
    type = Column(String(60), nullable=False)  # Educational Complex, Stadium, Community Center
    total_capacity = Column(Integer, nullable=False)
    current_occupancy = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="AVAILABLE")  # AVAILABLE, NEAR_CAPACITY, FULL, CLOSED

    has_medical = Column(Boolean, nullable=False, default=True)
    has_power_backup = Column(Boolean, nullable=False, default=True)
    contact_person = Column(String(100), nullable=False)
    contact_phone = Column(String(30), nullable=False)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geometry = Column(JSON, nullable=True)  # GeoJSON Point

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def available_capacity(self) -> int:
        return max(0, self.total_capacity - self.current_occupancy)

    @property
    def occupancy_percentage(self) -> float:
        if self.total_capacity == 0:
            return 0.0
        return round((self.current_occupancy / self.total_capacity) * 100.0, 1)
