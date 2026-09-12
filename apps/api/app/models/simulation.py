import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime
from ..database import Base


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_name = Column(String(50), nullable=False, default="GRADUAL_MONSOON")
    status = Column(String(20), nullable=False, default="IDLE")  # IDLE, RUNNING, PAUSED, COMPLETED
    current_stage = Column(Integer, nullable=False, default=0)  # 0 to 4
    current_substep = Column(Integer, nullable=False, default=0)  # 0 to 19 (4 substeps per stage)
    total_steps = Column(Integer, nullable=False, default=20)
    speed_multiplier = Column(Float, nullable=False, default=1.0)
    seed = Column(Integer, nullable=False, default=26192)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
