"""
apps/api/app/routers/forecast_risk.py
Flowshield — Future Flood Risk Prediction Timeline Router (v3.0)
Smart India Hackathon 2026 (PS ID: 26192)

Serves predictive flood risk timelines (+1h to +48h) computed by passing
future multi-horizon precipitation forecasts through calibrated ML inference.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from ..database import get_db
from ..models.village import Village
from ..schemas.hazard import FutureRiskTimelineResponse
from ..schemas.timeline import TimelineDetailedResponse, TimelineLocationHierarchy
from ..services.future_risk_service import future_risk_service
from ..services.timeline_service import timeline_service

router = APIRouter(prefix="/risk/forecast", tags=["Future Risk Forecasting"])


@router.get("", response_model=FutureRiskTimelineResponse)
def get_village_future_risk_timeline(
    village_id: str = Query(..., description="Target village ID (e.g. mandi_sadar)"),
    horizons: Optional[str] = Query(None, description="Comma-separated horizons e.g. 1,3,6,12,24,48"),
    db: Session = Depends(get_db)
):
    """
    Returns +1h to +48h machine learning flood-risk forecast timeline for a village.
    Computes time-series probabilities, uncertainty intervals, and anticipated peak risk window.
    """
    village = db.query(Village).filter(Village.id == village_id).first()
    if not village:
        # Check if fallback/default Mandi Sadar can be used
        village = db.query(Village).first()
        if not village:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Village '{village_id}' not found in database."
            )

    horizon_list = None
    if horizons:
        try:
            horizon_list = [int(h.strip()) for h in horizons.split(",") if h.strip()]
        except ValueError:
            horizon_list = None

    result = future_risk_service.predict_future_risk_timeline(village, db, horizon_list)
    return FutureRiskTimelineResponse(**result)


@router.get("/summary")
def get_regional_forecast_risk_summary(db: Session = Depends(get_db)):
    """
    Returns an aggregated future peak-risk overview across all monitored settlements.
    Used by emergency command centers for pre-positioning rescue assets.
    """
    villages = db.query(Village).all()
    if not villages:
        return {"total_monitored": 0, "high_risk_settlements": [], "peak_regional_window": "None"}

    summaries = []
    critical_count = 0
    high_count = 0

    for v in villages:
        timeline_res = future_risk_service.predict_future_risk_timeline(
            v, db, horizons_hours=[1, 3, 6, 12, 24]
        )
        peak_score = timeline_res["peak_risk_score"]
        peak_horizon = timeline_res["peak_risk_horizon_hours"]

        # Find worst level in timeline
        max_level = "LOW"
        levels = [t["risk_level"] for t in timeline_res["timeline"]]
        if "CRITICAL" in levels:
            max_level = "CRITICAL"
            critical_count += 1
        elif "HIGH" in levels:
            max_level = "HIGH"
            high_count += 1
        elif "WATCH" in levels:
            max_level = "WATCH"

        summaries.append({
            "village_id": v.id,
            "village_name": v.name,
            "latitude": v.latitude,
            "longitude": v.longitude,
            "peak_risk_score": peak_score,
            "peak_risk_horizon_hours": peak_horizon,
            "projected_risk_level": max_level,
            "near_term_prob_3h": next((t["flood_probability"] for t in timeline_res["timeline"] if t["horizon_hours"] == 3), 0.0),
        })

    # Sort descending by peak risk score
    summaries.sort(key=lambda x: x["peak_risk_score"], reverse=True)

    return {
        "total_monitored": len(villages),
        "critical_count": critical_count,
        "high_count": high_count,
        "settlements": summaries,
        "top_threat": summaries[0] if summaries else None,
    }


@router.get("/detailed", response_model=TimelineDetailedResponse)
def get_detailed_timeline_intelligence(
    village_id: str = Query(..., description="Target village ID or slug (e.g. bh-01-patna)"),
    force_refresh: bool = Query(False, description="Bypass cache and force upstream refresh"),
    db: Session = Depends(get_db)
):
    """
    Delivers comprehensive, real-time, analytical flood & hydro-meteorological decision support:
    - Multi-stream peak timing (rainfall, river crest, risk).
    - Piecewise continuous lead-time solver with P90 early crossing discovery.
    - Additive explainable risk driver attribution.
    - Verified infrastructure, safe shelter capacity, and route clearance status.
    - Auditable stream-by-stream SLA data quality.
    """
    try:
        return timeline_service.get_detailed_timeline(village_id, db, force_refresh=force_refresh)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Telemetry synthesis error: {str(e)}"
        )


@router.get("/locations", response_model=TimelineLocationHierarchy)
def get_timeline_location_hierarchy(db: Session = Depends(get_db)):
    """
    Returns nested geographic hierarchy: State -> District -> Settlements
    for dynamic navigation across monitored river basins and mountain catchments.
    """
    return timeline_service.get_location_hierarchy(db)
