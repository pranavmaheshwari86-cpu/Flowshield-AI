import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from ..database import Base


class EnvironmentalObservation(Base):
    __tablename__ = "environmental_observations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(36), ForeignKey("villages.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    rainfall_1h = Column(Float, nullable=False)
    rainfall_3h = Column(Float, nullable=False)
    rainfall_6h = Column(Float, nullable=False)
    rainfall_24h = Column(Float, nullable=False)
    rainfall_intensity = Column(Float, nullable=False)
    soil_moisture = Column(Float, nullable=False)
    river_level = Column(Float, nullable=False)
    river_level_change = Column(Float, nullable=False)

    # Additive physical feature extensions (Phase 1: Canonical 15-Feature Foundation)
    rainfall_12h = Column(Float, nullable=True)
    rainfall_72h = Column(Float, nullable=True)
    deep_soil_moisture = Column(Float, nullable=True)
    soil_moisture_change = Column(Float, nullable=True)
    river_level_change_1h = Column(Float, nullable=True)
    river_level_rate = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    surface_pressure = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)

    # Provenance fields & Orthogonal Semantics (v2.4 Contract)
    source = Column(String(100), nullable=False, default="Demonstration Telemetry Network")
    source_type = Column(String(40), nullable=False, default="AUTOMATED_STATION")
    data_state = Column(String(30), nullable=False, default="OBSERVED")
    data_quality_status = Column(String(30), nullable=False, default="VALID")
    data_quality_score = Column(Float, nullable=True, default=1.0)
    source_timestamp = Column(DateTime, nullable=True)
    retrieved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Backward-compatible legacy attributes
    is_simulated = Column(Boolean, nullable=False, default=False)
    quality_score = Column(Float, nullable=False, default=1.0)
    freshness_seconds = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    village = relationship("Village", back_populates="observations")
    predictions = relationship("Prediction", back_populates="observation", cascade="all, delete-orphan")

    # Canonical 15-Feature Property Accessors
    @property
    def rainfall_1h_mm(self) -> float:
        return self.rainfall_1h

    @property
    def rainfall_3h_mm(self) -> float:
        return self.rainfall_3h

    @property
    def rainfall_6h_mm(self) -> float:
        return self.rainfall_6h

    @property
    def rainfall_24h_mm(self) -> float:
        return self.rainfall_24h

    @property
    def rainfall_72h_mm(self) -> float:
        return self.rainfall_72h if self.rainfall_72h is not None else (self.rainfall_24h * 1.5)

    @property
    def soil_saturation_pct(self) -> float:
        return self.soil_moisture

    @property
    def deep_soil_saturation_pct(self) -> float:
        return self.deep_soil_moisture if self.deep_soil_moisture is not None else self.soil_moisture

    @property
    def temperature_c(self) -> float:
        return self.temperature if self.temperature is not None else 22.0

    @property
    def relative_humidity_pct(self) -> float:
        return self.humidity if self.humidity is not None else 75.0

    @property
    def surface_pressure_hpa(self) -> float:
        return self.surface_pressure if self.surface_pressure is not None else 920.0

    @property
    def wind_speed_kmh(self) -> float:
        return self.wind_speed if self.wind_speed is not None else 10.0


Index("idx_obs_village_timestamp", EnvironmentalObservation.village_id, EnvironmentalObservation.timestamp.desc())
Index("idx_obs_state_quality", EnvironmentalObservation.data_state, EnvironmentalObservation.data_quality_status)
