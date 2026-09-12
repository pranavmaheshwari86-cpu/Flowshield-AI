"""
apps/api/app/routers/predictions.py
Flowshield — Prediction & Risk API Endpoints (v2.4)
Exposes calibrated V2 inference, decision thresholds, and operational policy scores.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.prediction import Prediction
from ..models.village import Village
from ..schemas.prediction import PredictionRequest, PredictionResponse, FeatureContribution
from ..services.prediction_service import prediction_service
from ..services.risk_engine import risk_engine
from ..services.model_integrity import model_integrity_checker, ModelIntegrityState
from ..services.live_inference_service import live_inference_service

router = APIRouter(prefix="/predictions", tags=["Predictions & ML"])


@router.post("", response_model=PredictionResponse)
@router.post("/predict", response_model=PredictionResponse)
def run_prediction(req: PredictionRequest, db: Session = Depends(get_db)):
    if req.region is not None:
        from ml.registry.region_resolver import region_resolver
        if not region_resolver.is_valid_region(req.region):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "UNSUPPORTED_REGION", "message": f"Region '{req.region}' is not supported."},
            )

    feature_dict = req.model_dump(exclude_unset=False)
    village_id = feature_dict.pop("village_id", None)

    village = None
    vulnerability = 0.50
    if village_id:
        village = db.query(Village).filter(Village.id == village_id).first()
        if village:
            vulnerability = village.vulnerability_index

    # 1. Run V2 ML inference & calibration
    full_pred = prediction_service.predict_full(
        feature_dict=feature_dict,
        data_quality_score=1.0,
        freshness_seconds=0,
    )

    prob = full_pred["flood_probability"]
    calibrated_prob = full_pred["calibrated_probability"]
    threshold = full_pred["decision_threshold"]
    threshold_exceeded = full_pred["threshold_exceeded"]
    quality = full_pred["prediction_quality"]
    top_contribs = full_pred["top_contributing_factors"]
    explanations = full_pred["physical_explanations"]

    # 2. Run Operational Policy Risk Engine
    if full_pred.get("status") == "insufficient_data" or full_pred.get("risk_level") == "INSUFFICIENT_DATA":
        risk_score = 0
        risk_lvl = "INSUFFICIENT_DATA"
        color_hex = "#6b7280"
        is_capped = True
    else:
        risk_score, risk_lvl, color_hex, is_capped = risk_engine.compute_operational_risk(
            flood_probability=calibrated_prob,
            trend_factor=1.0,
            vulnerability_index=vulnerability,
            data_quality_score=quality,
            freshness_seconds=0,
        )

    now = datetime.now(timezone.utc)
    pred_id = str(uuid.uuid4())

    model_ver = prediction_service.metadata.get("model_version", "flowshield-flood-risk-v2")

    # Persist record in database if village_id is known
    try:
        db_pred = Prediction(
            id=pred_id,
            village_id=village_id,
            flood_probability=prob,
            calibrated_probability=calibrated_prob,
            decision_threshold=threshold,
            threshold_exceeded=threshold_exceeded,
            model_integrity_status=full_pred["model_integrity_status"],
            prediction_quality=quality,
            model_version=model_ver,
            feature_contributions=top_contribs,
            created_at=now,
        )
        if village_id:
            db.add(db_pred)
            db.commit()
    except Exception:
        db.rollback()

    factors = [FeatureContribution(**c) for c in top_contribs]

    return PredictionResponse(
        prediction_id=pred_id,
        village_id=village_id,
        flood_probability=prob,
        calibrated_probability=calibrated_prob,
        raw_probability=full_pred.get("raw_probability", calibrated_prob),
        decision_threshold=threshold,
        threshold_exceeded=threshold_exceeded,
        risk_score=risk_score,
        operational_risk_score=risk_score,
        policy_score=risk_score,
        risk_level=risk_lvl,
        operational_risk_level=risk_lvl,
        prediction_quality=quality,
        model_version=model_ver,
        model_integrity_status=full_pred["model_integrity_status"],
        top_contributing_factors=factors,
        top_shap_factors=factors,
        physical_explanations=explanations,
        data_provenance={
            "source": "On-Demand Diagnostic API Request",
            "is_simulated": False,
            "quality_score": 1.0,
            "freshness_seconds": 0,
            "decision_threshold": threshold,
            "disclosure": "Calibrated Logistic Regression (Isotonic scaling on ERA5-Land reanalysis).",
        },
        timestamp=now,
    )


@router.post("/evaluate-all")
def evaluate_all_settlements(db: Session = Depends(get_db)):
    """
    Batch evaluates calibrated flood risk across all monitored basin settlements.
    Persists predictions, updates risk snapshots, and triggers alerts where thresholds are breached.
    """
    try:
        return live_inference_service.evaluate_all_villages(db, persist=True)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Batch evaluation failed: {e}")

