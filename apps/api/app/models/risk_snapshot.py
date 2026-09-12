import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from ..database import Base


class RiskSnapshot(Base):
    __tablename__ = "risk_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(36), ForeignKey("villages.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_id = Column(String(36), ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False)

    risk_score = Column(Integer, nullable=False)  # 0 to 100 operational risk
    risk_level = Column(String(20), nullable=False)  # LOW, MODERATE, HIGH, CRITICAL
    trend = Column(String(20), nullable=False, default="STABLE")  # RISING, FALLING, STABLE

    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    village = relationship("Village", back_populates="risk_snapshots")
    prediction = relationship("Prediction", back_populates="risk_snapshots")


Index("idx_snapshot_village_time", RiskSnapshot.village_id, RiskSnapshot.timestamp.desc())
