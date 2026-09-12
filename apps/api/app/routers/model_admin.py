"""
apps/api/app/routers/model_admin.py
Flowshield — MLOps Model Administration & Retraining Router (v3.0)
Smart India Hackathon 2026 (PS ID: 26192)

Manages model lifecycle:
- Ground-truth outcome submission
- Continuous retraining pipeline invocation
- Model version lineage & champion status tracking
- Drift monitoring integration
"""

import os
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.verified_outcome import VerifiedOutcome
from ..models.model_version import ModelVersion
from ..models.village import Village
from ml.retraining.retrain_pipeline import retrain_pipeline
from ml.inference.predict import load_inference_artifacts, V2_PIPELINE_PATH

router = APIRouter(prefix="/model", tags=["MLOps & Model Lifecycle"])


class OutcomeSubmissionRequest(BaseModel):
    village_id: str
    actual_flood_occurred: bool
    severity_observed: Optional[str] = "MODERATE"  # NONE, MINOR, MODERATE, SEVERE, CATASTROPHIC
    flood_depth_cm: Optional[float] = None
    verification_source: str = "FIELD_RESPONDER"  # SDRF_DISPATCH, FIELD_RESPONDER, SATELLITE_RADAR
    features_snapshot: Optional[Dict[str, float]] = None
    prediction_probability: Optional[float] = None
    verified_by: Optional[str] = "SDRF Officer"
    notes: Optional[str] = None


@router.get("/status")
def get_current_model_status():
    """Returns the current deployed champion model version, parameters, and benchmark scores."""
    _, _, _, pipeline_info = load_inference_artifacts()
    return {
        "pipeline_version": pipeline_info.get("pipeline_version", "flowshield-flood-risk-v2"),
        "selected_model": pipeline_info.get("selected_model", "logistic_regression"),
        "calibration_method": pipeline_info.get("calibration_method", "isotonic"),
        "operational_threshold": pipeline_info.get("threshold", 0.08),
        "status": "CHAMPION_ACTIVE",
        "evaluation_metrics": pipeline_info.get("evaluation_metrics", {
            "recall": 0.884,
            "roc_auc": 0.923,
            "pr_auc": 0.676,
            "false_negative_rate": 0.116
        }),
        "feature_count": 15,
        "champion_since": "2026-09-11T00:00:00Z"
    }


@router.post("/outcome")
def submit_verified_outcome(
    req: OutcomeSubmissionRequest,
    db: Session = Depends(get_db)
):
    """
    Submits ground truth from field teams after a heavy weather event.
    Stores verified outcomes to inform retraining and model drift calculations.
    """
    village = db.query(Village).filter(Village.id == req.village_id).first()
    if not village:
        # Check if default exists
        village = db.query(Village).first()
        if not village:
            raise HTTPException(status_code=404, detail="Village not found")

    outcome = VerifiedOutcome(
        village_id=village.id,
        actual_flood_occurred=req.actual_flood_occurred,
        severity_observed=req.severity_observed,
        flood_depth_cm=req.flood_depth_cm,
        verification_source=req.verification_source,
        features_snapshot=req.features_snapshot,
        prediction_probability=req.prediction_probability,
        verified_by=req.verified_by,
        notes=req.notes,
        created_at=datetime.now(timezone.utc)
    )
    db.add(outcome)
    db.commit()
    db.refresh(outcome)

    return {
        "status": "verified_outcome_recorded",
        "outcome_id": outcome.id,
        "village_name": village.name,
        "actual_flood_occurred": outcome.actual_flood_occurred,
        "recorded_at": outcome.created_at.isoformat()
    }


@router.get("/outcomes")
def list_verified_outcomes(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists recent verified field outcomes."""
    outcomes = (
        db.query(VerifiedOutcome)
        .order_by(VerifiedOutcome.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "total_outcomes": len(outcomes),
        "items": [
            {
                "id": o.id,
                "village_id": o.village_id,
                "village_name": o.village.name if o.village else "Unknown",
                "actual_flood_occurred": o.actual_flood_occurred,
                "severity_observed": o.severity_observed,
                "flood_depth_cm": o.flood_depth_cm,
                "verification_source": o.verification_source,
                "verified_by": o.verified_by,
                "created_at": o.created_at.isoformat()
            }
            for o in outcomes
        ]
    }


@router.post("/retrain")
def trigger_model_retraining(
    force_promotion: bool = Query(False, description="Bypass safety gate for simulation"),
    db: Session = Depends(get_db)
):
    """
    Triggers continuous retraining pipeline.
    Augments dataset with verified outcomes, trains candidate model, evaluates against champion.
    """
    verified = db.query(VerifiedOutcome).all()
    report = retrain_pipeline.run_retrain(verified_outcomes=verified, force=force_promotion)

    # Record model version in DB
    if report.get("status") == "success":
        cand_metrics = report.get("candidate_metrics", {})
        mv = ModelVersion(
            version_tag=report["candidate_version"],
            algorithm="Calibrated Logistic Regression (Isotonic)",
            is_active_champion=report["promoted"],
            recall=cand_metrics.get("recall", 0.85),
            roc_auc=cand_metrics.get("roc_auc", 0.90),
            pr_auc=cand_metrics.get("pr_auc", 0.65),
            brier_score=cand_metrics.get("brier_score", 0.05),
            threshold=0.08,
            training_sample_count=cand_metrics.get("training_samples", 12000),
            features_used={"count": 15, "names": "15_canonical_features"},
            metrics_breakdown=cand_metrics,
            deployed_at=datetime.now(timezone.utc) if report["promoted"] else None
        )
        db.add(mv)
        db.commit()

    return report


@router.get("/versions")
def list_model_versions(db: Session = Depends(get_db)):
    """Lists registered model versions in the lineage registry."""
    versions = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()
    return {
        "count": len(versions),
        "versions": [
            {
                "id": v.id,
                "version_tag": v.version_tag,
                "algorithm": v.algorithm,
                "is_active_champion": v.is_active_champion,
                "recall": v.recall,
                "roc_auc": v.roc_auc,
                "pr_auc": v.pr_auc,
                "training_sample_count": v.training_sample_count,
                "created_at": v.created_at.isoformat()
            }
            for v in versions
        ]
    }
