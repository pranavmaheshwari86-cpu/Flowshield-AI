import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from ..database import Base


class ModelCoverage(Base):
    __tablename__ = "model_coverage"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    is_supported = Column(Boolean, nullable=False, default=True)
    has_training_data = Column(Boolean, nullable=False, default=True)
    has_prediction = Column(Boolean, nullable=False, default=True)
    has_shelter_data = Column(Boolean, nullable=False, default=True)
    has_route_data = Column(Boolean, nullable=False, default=True)
    description = Column(String(255), nullable=True)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))
