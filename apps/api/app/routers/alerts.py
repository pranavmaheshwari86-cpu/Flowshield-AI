from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.alert import Alert
from ..models.village import Village
from ..schemas.alert import AlertResponse, AcknowledgeRequest
from ..services.alert_engine import alert_engine
from ..auth.dependencies import RoleChecker

router = APIRouter(prefix="/alerts", tags=["Alert Engine"])


@router.get("", response_model=List[AlertResponse])
def list_alerts(
    status_filter: Optional[str] = Query(None, alias="status"),
    severity_filter: Optional[str] = Query(None, alias="severity"),
    state_filter: Optional[str] = Query(None, alias="state"),
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Alert, Village.name.label("village_name")).join(
        Village, Alert.village_id == Village.id
    )
    if status_filter:
        query = query.filter(Alert.status == status_filter.upper())
    if severity_filter:
        query = query.filter(Alert.severity == severity_filter.upper())
    if state_filter and state_filter.upper() != "ALL":
        query = query.filter(Village.state.ilike(f"%{state_filter}%"))

    results = query.order_by(Alert.created_at.desc()).limit(limit).all()

    alert_responses = []
    for alert, v_name in results:
        alert_responses.append(
            AlertResponse(
                id=alert.id,
                village_id=alert.village_id,
                village_name=v_name,
                severity=alert.severity,
                status=alert.status,
                headline=alert.headline,
                trigger_reason=alert.trigger_reason,
                top_contributors=alert.top_contributors,
                recommended_actions=alert.recommended_actions,
                acknowledged_by=alert.acknowledged_by,
                acknowledged_at=alert.acknowledged_at,
                created_at=alert.created_at,
            )
        )
    return alert_responses


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
@router.post("/acknowledge/{alert_id}", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: str,
    req: AcknowledgeRequest,
    db: Session = Depends(get_db),
    _user=Depends(RoleChecker(["AUTHORITY", "RESPONDER", "ADMIN"])),
):
    alert = alert_engine.acknowledge_alert(db, alert_id, req.acknowledged_by)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    v = db.query(Village).filter(Village.id == alert.village_id).first()
    return AlertResponse(
        id=alert.id,
        village_id=alert.village_id,
        village_name=v.name if v else None,
        severity=alert.severity,
        status=alert.status,
        headline=alert.headline,
        trigger_reason=alert.trigger_reason,
        top_contributors=alert.top_contributors,
        recommended_actions=alert.recommended_actions,
        acknowledged_by=alert.acknowledged_by,
        acknowledged_at=alert.acknowledged_at,
        created_at=alert.created_at,
    )
