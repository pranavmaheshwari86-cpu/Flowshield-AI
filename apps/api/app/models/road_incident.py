import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from ..database import Base


class RoadIncident(Base):
    __tablename__ = "road_incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    route_id = Column(String(36), ForeignKey("routes.id", ondelete="SET NULL"), nullable=True)
    corridor_name = Column(String(150), nullable=False)
    state = Column(String(100), nullable=False, default="Uttarakhand")
    district = Column(String(100), nullable=False, default="Rudraprayag")
    
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    blockage_type = Column(String(50), nullable=False, default="Landslide")  # Landslide, Flooding, Bridge Collapse, Debris, Fallen Trees, Road Damage, Unknown
    severity = Column(String(20), nullable=False, default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(String(500), nullable=True)
    
    reported_by = Column(String(100), nullable=False, default="Field Responder")
    status = Column(String(30), nullable=False, default="ACTIVE")  # REPORTED, UNDER_REVIEW, VERIFIED, ACTIVE, CLEARED
    verification_status = Column(String(30), nullable=False, default="VERIFIED")
    
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
