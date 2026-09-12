import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from ..database import Base


class MonitoringPolygon(Base):
    __tablename__ = "monitoring_polygons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agro_polygon_id = Column(String(64), unique=True, nullable=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    country = Column(String(60), nullable=False, default="India")
    state = Column(String(100), nullable=True, index=True)
    district = Column(String(100), nullable=True, index=True)
    area_hectares = Column(Float, nullable=False)
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    geometry_geojson = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="PENDING", index=True)  # PENDING, REGISTERED, FAILED, LIMIT_EXCEEDED
    error_message = Column(Text, nullable=True)
    last_soil_update = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    observations = relationship(
        "SoilObservation",
        back_populates="polygon",
        cascade="all, delete-orphan",
        order_by="desc(SoilObservation.observation_timestamp)",
    )


class SoilObservation(Base):
    __tablename__ = "soil_observations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    polygon_id = Column(String(36), ForeignKey("monitoring_polygons.id", ondelete="CASCADE"), nullable=False, index=True)
    agro_polygon_id = Column(String(64), nullable=True, index=True)

    # Official AgroMonitoring soil endpoint metrics
    soil_moisture = Column(Float, nullable=False)  # m3/m3 (e.g. 0.173)
    soil_temperature = Column(Float, nullable=True)  # 10cm depth temp in Kelvin (t10)
    surface_temperature = Column(Float, nullable=True)  # Surface temp in Kelvin (t0)

    observation_timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    polygon = relationship("MonitoringPolygon", back_populates="observations")
