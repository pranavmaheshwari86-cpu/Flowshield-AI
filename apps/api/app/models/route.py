import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class Route(Base):
    __tablename__ = "routes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), nullable=False)
    state = Column(String(100), nullable=False, default="Uttarakhand")
    district = Column(String(100), nullable=False, default="Rudraprayag")
    origin_village_id = Column(String(36), ForeignKey("villages.id", ondelete="CASCADE"), nullable=False)
    destination_shelter_id = Column(String(36), ForeignKey("shelters.id", ondelete="CASCADE"), nullable=False)

    distance_km = Column(Float, nullable=False)
    assessed_risk_score = Column(Integer, nullable=False, default=10)  # 0 to 100
    is_blocked = Column(Boolean, nullable=False, default=False)
    blockage_reason = Column(String(255), nullable=True)

    is_river_crossing = Column(Boolean, nullable=False, default=False)
    crossing_coordinates = Column(JSON, nullable=True)
    hazard_cost_multiplier = Column(Float, nullable=True, default=1.0)
    notes = Column(String(255), nullable=True)

    geometry = Column(JSON, nullable=False)  # GeoJSON LineString
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    origin_village = relationship("Village")
    destination_shelter = relationship("Shelter")
