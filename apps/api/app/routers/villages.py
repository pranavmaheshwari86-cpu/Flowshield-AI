from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.village import Village
from ..models.observation import EnvironmentalObservation
from ..models.prediction import Prediction
from ..models.risk_snapshot import RiskSnapshot
from ..models.alert import Alert
from ..schemas.village import VillageResponse, VillageDetailResponse
from ..services.action_engine import action_engine
from ..services.shelter_service import shelter_service
from ..services.route_service import route_service
from ..services.live_inference_service import live_inference_service

router = APIRouter(prefix="/villages", tags=["Villages & Risk"])


@router.get("", response_model=List[VillageResponse])
def list_villages(
    state: Optional[str] = None,
    district: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Village)
    if state and state.upper() != "ALL":
        query = query.filter(Village.state.ilike(f"%{state}%"))
    if district and district.upper() != "ALL":
        query = query.filter(Village.district.ilike(f"%{district}%"))
    villages = query.order_by(Village.name).all()
    results = []
    for v in villages:
        latest_snap = (
            db.query(RiskSnapshot)
            .filter(RiskSnapshot.village_id == v.id)
            .order_by(RiskSnapshot.timestamp.desc())
            .first()
        )
        active_alert = (
            db.query(Alert)
            .filter(Alert.village_id == v.id, Alert.status == "ACTIVE")
            .first()
        )
        latest_obs = (
            db.query(EnvironmentalObservation)
            .filter(EnvironmentalObservation.village_id == v.id)
            .order_by(EnvironmentalObservation.timestamp.desc())
            .first()
        )

        results.append(
            VillageResponse(
                id=v.id,
                name=v.name,
                tehsil=v.tehsil,
                district=v.district,
                state=v.state,
                population=v.population,
                elevation=v.elevation,
                slope=v.slope,
                distance_to_river=v.distance_to_river,
                historical_flood_frequency=v.historical_flood_frequency,
                vulnerability_index=v.vulnerability_index,
                latitude=v.latitude,
                longitude=v.longitude,
                risk_score=latest_snap.risk_score if latest_snap else 10,
                risk_level=latest_snap.risk_level if latest_snap else "LOW",
                trend=latest_snap.trend if latest_snap else "STABLE",
                has_active_alert=active_alert is not None,
                latest_observation_time=latest_obs.timestamp if latest_obs else None,
                created_at=v.created_at,
            )
        )
    return results


@router.get("/{village_id}", response_model=VillageDetailResponse)
def get_village_detail(village_id: str, db: Session = Depends(get_db)):
    v = db.query(Village).filter(Village.id == village_id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Village not found")

    latest_obs = (
        db.query(EnvironmentalObservation)
        .filter(EnvironmentalObservation.village_id == v.id)
        .order_by(EnvironmentalObservation.timestamp.desc())
        .first()
    )
    latest_pred = (
        db.query(Prediction)
        .filter(Prediction.village_id == v.id)
        .order_by(Prediction.created_at.desc())
        .first()
    )
    if not latest_pred and latest_obs:
        try:
            live_inference_service.evaluate_village(db, v.id, persist=True)
            latest_pred = (
                db.query(Prediction)
                .filter(Prediction.village_id == v.id)
                .order_by(Prediction.created_at.desc())
                .first()
            )
        except Exception:
            pass

    latest_snap = (
        db.query(RiskSnapshot)
        .filter(RiskSnapshot.village_id == v.id)
        .order_by(RiskSnapshot.timestamp.desc())
        .first()
    )
    active_alerts = (
        db.query(Alert)
        .filter(Alert.village_id == v.id, Alert.status.in_(["ACTIVE", "ACKNOWLEDGED"]))
        .order_by(Alert.created_at.desc())
        .all()
    )
    historical_snaps = (
        db.query(RiskSnapshot)
        .filter(RiskSnapshot.village_id == v.id)
        .order_by(RiskSnapshot.timestamp.desc())
        .limit(10)
        .all()
    )

    current_conditions = {}
    if latest_obs:
        current_conditions = {
            "rainfall_1h": latest_obs.rainfall_1h,
            "rainfall_3h": latest_obs.rainfall_3h,
            "rainfall_6h": latest_obs.rainfall_6h,
            "rainfall_24h": latest_obs.rainfall_24h,
            "rainfall_intensity": latest_obs.rainfall_intensity,
            "soil_moisture": latest_obs.soil_moisture,
            "river_level": latest_obs.river_level,
            "river_level_change": latest_obs.river_level_change,
            "source": latest_obs.source,
            "quality_score": latest_obs.quality_score,
            "freshness_seconds": latest_obs.freshness_seconds,
            "timestamp": latest_obs.timestamp.isoformat(),
        }

    top_contributors = latest_pred.feature_contributions if latest_pred else []
    risk_level = latest_snap.risk_level if latest_snap else "LOW"
    risk_score = latest_snap.risk_score if latest_snap else 10
    trend = latest_snap.trend if latest_snap else "STABLE"

    recommended_actions = action_engine.get_recommended_actions(risk_level)

    # Nearest shelter
    nearest_shelters = shelter_service.get_nearest_shelters(db, v.id, limit=1)
    primary_shelter = nearest_shelters[0] if nearest_shelters else None

    # Designated route
    routes = route_service.get_routes_for_village(db, v.id)
    primary_route = None
    if routes:
        r = routes[0]
        primary_route = {
            "id": r.id,
            "name": r.name,
            "distance_km": r.distance_km,
            "assessed_risk_score": r.assessed_risk_score,
            "is_blocked": r.is_blocked,
            "blockage_reason": r.blockage_reason,
            "is_river_crossing": r.is_river_crossing,
            "notes": r.notes,
        }

    # Trend list formatted for Recharts
    trend_data = [
        {
            "time": s.timestamp.strftime("%H:%M:%S"),
            "risk_score": s.risk_score,
            "risk_level": s.risk_level,
        }
        for s in reversed(historical_snaps)
    ]

    return VillageDetailResponse(
        id=v.id,
        name=v.name,
        tehsil=v.tehsil,
        district=v.district,
        state=v.state,
        population=v.population,
        elevation=v.elevation,
        slope=v.slope,
        distance_to_river=v.distance_to_river,
        historical_flood_frequency=v.historical_flood_frequency,
        vulnerability_index=v.vulnerability_index,
        latitude=v.latitude,
        longitude=v.longitude,
        risk_score=risk_score,
        risk_level=risk_level,
        trend=trend,
        has_active_alert=len(active_alerts) > 0,
        latest_observation_time=latest_obs.timestamp if latest_obs else None,
        created_at=v.created_at,
        current_conditions=current_conditions,
        top_contributors=top_contributors,
        historical_risk_trend=trend_data,
        active_alerts=[
            {
                "id": a.id,
                "severity": a.severity,
                "status": a.status,
                "headline": a.headline,
                "trigger_reason": a.trigger_reason,
                "created_at": a.created_at.isoformat(),
            }
            for a in active_alerts
        ],
        recommended_actions=recommended_actions,
        nearest_shelter=primary_shelter,
        evacuation_route=primary_route,
        latest_prediction={
            "id": latest_pred.id,
            "flood_probability": latest_pred.flood_probability,
            "calibrated_probability": latest_pred.calibrated_probability,
            "decision_threshold": latest_pred.decision_threshold,
            "threshold_exceeded": latest_pred.threshold_exceeded,
            "prediction_quality": latest_pred.prediction_quality,
            "model_version": latest_pred.model_version,
            "feature_contributions": latest_pred.feature_contributions,
            "created_at": latest_pred.created_at.isoformat() if latest_pred.created_at else None,
        } if latest_pred else None,
        calibrated_probability=latest_pred.calibrated_probability if latest_pred and latest_pred.calibrated_probability is not None else (latest_pred.flood_probability if latest_pred else 0.0),
        decision_threshold=latest_pred.decision_threshold if latest_pred and latest_pred.decision_threshold is not None else 0.08,
        threshold_exceeded=latest_pred.threshold_exceeded if latest_pred and latest_pred.threshold_exceeded is not None else False,
        model_version=latest_pred.model_version if latest_pred else "flowshield-flood-risk-v2",
    )


@router.post("/{village_id}/predict")
def trigger_village_prediction(village_id: str, db: Session = Depends(get_db)):
    """
    On-demand real-time model inference endpoint for a settlement.
    Forces feature extraction from latest telemetry, evaluates V2 calibrated model,
    persists prediction & risk snapshot, checks alerts, and returns fresh inference results.
    """
    try:
        result = live_inference_service.evaluate_village(db, village_id, persist=True)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Inference failed: {e}")

