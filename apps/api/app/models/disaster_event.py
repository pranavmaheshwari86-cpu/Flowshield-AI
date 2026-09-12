import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text
from ..database import Base


class DisasterEvent(Base):
    __tablename__ = "disaster_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(50), nullable=False, unique=True, index=True)
    disaster_type = Column(String(50), nullable=False, default="LANDSLIDE")  # LANDSLIDE, FLASH_FLOOD, HEAVY_RAINFALL, FLOOD_RISK, ROAD_BLOCKAGE, MULTI_HAZARD
    severity = Column(String(20), nullable=False, default="HIGH")  # LOW, MODERATE, HIGH, CRITICAL
    status = Column(String(30), nullable=False, default="ACTIVE")  # ACTIVE, MONITORING, RESOLVED

    # Geography
    state = Column(String(100), nullable=False, default="Uttarakhand", index=True)
    district = Column(String(100), nullable=False, default="Rudraprayag", index=True)
    location_name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)

    # Impact assessment
    affected_radius_km = Column(Float, nullable=False, default=2.5)
    affected_villages = Column(JSON, nullable=True)  # List of village names/ids
    affected_population = Column(Integer, nullable=False, default=0)
    affected_corridors = Column(JSON, nullable=True)  # List of corridor names/ids

    # Detection & Provenance
    confidence = Column(Integer, nullable=False, default=90)  # 0 to 100
    source = Column(String(100), nullable=False, default="ML Ensemble & Telemetry Sensor")
    start_time = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))
    detected_at = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))
    last_updated = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    description = Column(Text, nullable=True)
    recommended_action = Column(String(255), nullable=True, default="IMMEDIATE EVACUATION")
    is_demo = Column(Integer, nullable=False, default=0)  # 1 if simulated demo event
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
