"""
apps/api/app/models/landslide_assessment.py
Flowshield — Empirical Landslide Susceptibility Model (v2.4)
Records empirical rainfall-slope assessments tagged strictly as PROTOTYPE_EMPIRICAL_THRESHOLD.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


class LandslideAssessment(Base):
    __tablename__ = "landslide_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(36), ForeignKey("villages.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    trigger_index = Column(Float, nullable=False)  # Empirical index in [0.0, 1.0]
    susceptibility_level = Column(String(30), nullable=False)  # LOW, MODERATE, HIGH, CRITICAL, SUSCEPTIBILITY_UNAVAILABLE
    methodology = Column(String(100), default="Empirical Rainfall-Slope Threshold (GSI / Caine 1980)")
    status = Column(String(50), default="PROTOTYPE_EMPIRICAL_THRESHOLD")
    is_ml_model = Column(Boolean, default=False)
    advisory_notice = Column(Text, nullable=True)

    village = relationship("Village")
