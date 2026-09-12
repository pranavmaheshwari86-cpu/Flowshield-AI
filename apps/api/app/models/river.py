import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, JSON
from ..database import Base


class River(Base):
    __tablename__ = "rivers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    danger_level_meters = Column(Float, nullable=False)
    warning_level_meters = Column(Float, nullable=False)
    gauge_station = Column(String(100), nullable=True)
    basin = Column(String(100), nullable=True)

    geometry = Column(JSON, nullable=False)  # GeoJSON LineString
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
