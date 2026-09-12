"""
apps/api/app/models/verified_outcome.py
Flowshield — Ground-Truth Verified Disaster Outcomes (v3.0)
Smart India Hackathon 2026 (PS ID: 26192)

Tracks post-event physical flood ground truth submitted by field responders,
SDRF battalions, municipal authorities, or satellite radar validations to power
continuous model evaluation and retraining feedback loops.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from ..database import Base


class VerifiedOutcome(Base):
    __tablename__ = "verified_outcomes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prediction_id = Column(String(36), ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True, index=True)
    village_id = Column(String(36), ForeignKey("villages.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    actual_flood_occurred = Column(Boolean, nullable=False)
    severity_observed = Column(String(40), default="NONE", nullable=True)  # NONE, MINOR, MODERATE, SEVERE, CATASTROPHIC
    flood_depth_cm = Column(Float, nullable=True)
    verification_source = Column(String(80), nullable=False)  # SDRF_DISPATCH, FIELD_OFFICER, SATELLITE_SAR, CITIZEN_CONSENSUS
    
    features_snapshot = Column(JSON, nullable=True)  # Captured 15 features at prediction time
    prediction_probability = Column(Float, nullable=True)
    model_version = Column(String(60), nullable=True)
    
    verified_by = Column(String(100), nullable=True)
    notes = Column(String(500), nullable=True)
    used_for_retraining = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    village = relationship("Village")
    prediction = relationship("Prediction")
