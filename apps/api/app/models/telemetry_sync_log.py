"""
apps/api/app/models/telemetry_sync_log.py
Flowshield — Telemetry Sync Audit & Provider Health Model (v2.4)
Records every provider sync attempt, records updated, and failure diagnostics.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text
from ..database import Base


class TelemetrySyncLog(Base):
    __tablename__ = "telemetry_sync_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sync_id = Column(String(36), nullable=False, index=True)
    provider = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(String(30), nullable=False)  # SUCCESS, DEGRADED, FAILED
    records_updated = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
