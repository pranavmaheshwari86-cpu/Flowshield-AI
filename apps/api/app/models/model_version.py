"""
apps/api/app/models/model_version.py
Flowshield — Model Version Registry & Champion Tracking (v3.0)
Smart India Hackathon 2026 (PS ID: 26192)

Tracks production and candidate ML models, validation metrics,
decision thresholds, calibration parameters, and retraining lineages.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, JSON, Boolean, Integer
from ..database import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version_tag = Column(String(60), unique=True, nullable=False, index=True)
    algorithm = Column(String(80), nullable=False)  # Calibrated Logistic Regression, XGBoost, etc.
    is_active_champion = Column(Boolean, default=False, nullable=False)
    
    # Core performance metrics
    recall = Column(Float, nullable=False)
    roc_auc = Column(Float, nullable=False)
    pr_auc = Column(Float, nullable=False)
    brier_score = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    threshold = Column(Float, default=0.08, nullable=False)
    
    training_sample_count = Column(Integer, nullable=False)
    features_used = Column(JSON, nullable=False)
    metrics_breakdown = Column(JSON, nullable=True)
    artifact_path = Column(String(255), nullable=True)
    
    deployed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
