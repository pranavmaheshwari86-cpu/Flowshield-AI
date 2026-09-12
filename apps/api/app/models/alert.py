import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Index, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from ..database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(36), ForeignKey("villages.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_id = Column(String(36), ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True)

    severity = Column(String(20), nullable=False)  # HIGH, CRITICAL
    status = Column(String(20), nullable=False, default="ACTIVE")  # ACTIVE, ACKNOWLEDGED, RESOLVED

    headline = Column(String(255), nullable=False)
    trigger_reason = Column(String(500), nullable=False)
    top_contributors = Column(JSON, nullable=False)
    recommended_actions = Column(JSON, nullable=False)

    dedup_key = Column(String(180), nullable=False, index=True)
    is_advisory = Column(Boolean, default=True, nullable=True)
    policy_version = Column(String(30), default="2.4.0", nullable=True)
    requires_authority_coordination = Column(Boolean, default=False, nullable=True)

    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    village = relationship("Village", back_populates="alerts")
    prediction = relationship("Prediction", back_populates="alerts")

    __table_args__ = (
        Index(
            "uq_alerts_village_dedup_active",
            "village_id",
            "dedup_key",
            unique=True,
            sqlite_where=Column("status") == "ACTIVE",
        ),
        Index("idx_alert_status_severity", "status", "severity"),
    )
