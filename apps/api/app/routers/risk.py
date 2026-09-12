from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.village import Village
from ..models.risk_snapshot import RiskSnapshot
from ..models.alert import Alert
from ..models.shelter import Shelter
from ..schemas.risk import RegionalRiskSummary, RiskCalculationRequest, RiskCalculationResponse
from ..services.risk_engine import risk_engine

router = APIRouter(prefix="/risk", tags=["Risk Engine"])


@router.get("/summary", response_model=RegionalRiskSummary)
def get_regional_summary(db: Session = Depends(get_db)):
    total_villages = db.query(Village).count()

    # Get the latest snapshot per village
    subq = (
        db.query(
            RiskSnapshot.village_id,
            func.max(RiskSnapshot.timestamp).label("max_time"),
        )
        .group_by(RiskSnapshot.village_id)
        .subquery()
    )

    latest_snaps = (
        db.query(RiskSnapshot)
        .join(
            subq,
            (RiskSnapshot.village_id == subq.c.village_id)
            & (RiskSnapshot.timestamp == subq.c.max_time),
        )
        .all()
    )

    critical_count = sum(1 for s in latest_snaps if s.risk_level == "CRITICAL")
    high_count = sum(1 for s in latest_snaps if s.risk_level == "HIGH")
    mod_count = sum(1 for s in latest_snaps if s.risk_level == "MODERATE")
    low_count = sum(1 for s in latest_snaps if s.risk_level == "LOW")

    active_alerts = db.query(Alert).filter(Alert.status == "ACTIVE").count()
    avail_shelters = db.query(Shelter).filter(Shelter.status != "CLOSED").count()

    return RegionalRiskSummary(
        total_villages=total_villages,
        critical_count=critical_count,
        high_count=high_count,
        moderate_count=mod_count,
        low_count=low_count,
        active_alerts_count=active_alerts,
        available_shelters_count=avail_shelters,
        system_status="OPERATIONAL",
        last_updated=datetime.now(timezone.utc),
    )


@router.post("/calculate", response_model=RiskCalculationResponse)
def calculate_risk(req: RiskCalculationRequest):
    score, level, color, is_capped = risk_engine.compute_operational_risk(
        flood_probability=req.flood_probability,
        trend_factor=req.trend_factor,
        vulnerability_index=req.vulnerability_index,
        data_quality_score=req.data_quality_score,
        freshness_seconds=req.freshness_seconds,
    )
    headline = f"Operational Risk Tier: {level} ({score}/100)"
    if is_capped:
        headline += " [Capped due to data quality/freshness]"

    return RiskCalculationResponse(
        risk_score=score,
        risk_level=level,
        color_hex=color,
        headline=headline,
        is_capped_by_quality=is_capped,
    )
