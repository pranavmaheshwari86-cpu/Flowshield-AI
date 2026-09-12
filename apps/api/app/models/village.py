import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class Village(Base):
    __tablename__ = "villages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(120), nullable=False, index=True)
    tehsil = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False, default="Uttarakhand")
    population = Column(Integer, nullable=False)
    elevation = Column(Float, nullable=False)  # meters
    slope = Column(Float, nullable=False)  # degrees
    distance_to_river = Column(Float, nullable=False)  # km
    historical_flood_frequency = Column(Float, nullable=False)  # 0 to 1
    vulnerability_index = Column(Float, nullable=False)  # 0 to 1
    
    # Coordinates in WGS84
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # GeoJSON geometry payload (Point)
    geometry = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    observations = relationship("EnvironmentalObservation", back_populates="village", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="village", cascade="all, delete-orphan")
    risk_snapshots = relationship("RiskSnapshot", back_populates="village", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="village", cascade="all, delete-orphan")
    risk_zone = relationship("RiskZone", back_populates="village", uselist=False, cascade="all, delete-orphan")


class RiskZone(Base):
    __tablename__ = "risk_zones"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(36), ForeignKey("villages.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Precomputed Voronoi catchment polygon (GeoJSON Polygon dict)
    geometry = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    village = relationship("Village", back_populates="risk_zone")
