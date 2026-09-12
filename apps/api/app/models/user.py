import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="AUTHORITY", index=True)  # AUTHORITY, RESPONDER, CITIZEN, ADMIN
    full_name = Column(String(120), nullable=False, default="Disaster Response Officer")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
