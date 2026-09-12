import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from ..database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(36), ForeignKey("villages.id", ondelete="CASCADE"), nullable=False, index=True)
    observation_id = Column(String(36), ForeignKey("environmental_observations.id", ondelete="SET NULL"), nullable=True)

    flood_probability = Column(Float, nullable=False)  # Calibrated probability in [0, 1]
    calibrated_probability = Column(Float, nullable=True)  # Strictly isotonically calibrated probability
    decision_threshold = Column(Float, default=0.08, nullable=True)  # Frozen operational threshold tau = 0.08
    threshold_exceeded = Column(Boolean, default=False, nullable=True)  # True when calibrated_prob >= decision_threshold
    model_integrity_status = Column(String(40), default="MODEL_READY", nullable=True)  # Verification state
    prediction_quality = Column(Float, nullable=False)  # Composite quality index
    model_version = Column(String(60), nullable=False)

    # Local SHAP attributions: [{"feature": str, "value": float, "contribution": float, "direction": str}]
    feature_contributions = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    village = relationship("Village", back_populates="predictions")
    observation = relationship("EnvironmentalObservation", back_populates="predictions")
    risk_snapshots = relationship("RiskSnapshot", back_populates="prediction", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="prediction")
