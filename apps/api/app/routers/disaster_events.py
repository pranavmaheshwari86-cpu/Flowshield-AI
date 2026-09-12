"""
apps/api/app/routers/disaster_events.py
Flowshield — Real-Time Disaster Event Intelligence Endpoints
Exposes active disaster events, affected perimeters, and interactive demo simulation controls.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.disaster_event import DisasterEventResponse, DisasterSimulationRequest
from ..services.disaster_event_service import disaster_event_service

router = APIRouter(prefix="/disaster-events", tags=["Disaster Event Intelligence"])


@router.get("", response_model=List[DisasterEventResponse])
def list_disaster_events(
    state: Optional[str] = Query(None, description="State name (e.g. Uttarakhand, Himachal Pradesh)"),
    district: Optional[str] = Query(None, description="District name (e.g. Rudraprayag, Mandi)"),
    active_only: bool = Query(True, description="Filter only ACTIVE and MONITORING events"),
    db: Session = Depends(get_db),
):
    """
    Returns active disaster events (Landslides, Flash Floods, Heavy Rainfall, Road Blockages)
    for the selected district jurisdiction.
    """
    events = disaster_event_service.get_events(db, state=state, district=district, active_only=active_only)
    return [DisasterEventResponse(**e) for e in events]


@router.get("/active", response_model=List[DisasterEventResponse])
def get_active_disaster_events(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Alias for active disaster events."""
    events = disaster_event_service.get_events(db, state=state, district=district, active_only=True)
    return [DisasterEventResponse(**e) for e in events]


@router.post("/simulate-demo", response_model=DisasterEventResponse)
def trigger_demo_disaster_scenario(
    req: DisasterSimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Triggers an interactive realistic demonstration disaster scenario:
    Heavy Rainfall anomaly -> Landslide triggered -> NH-107 corridor severed ->
    Alternate route generated -> Safe haven recommended.
    """
    event = disaster_event_service.trigger_demo_disaster(
        db=db,
        state=req.state,
        district=req.district,
    )
    return DisasterEventResponse(**event)


@router.post("/reset-demo")
def reset_demo_disaster_scenario(
    req: DisasterSimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Clears demonstration disaster events and restores all mountain corridors to OPEN.
    """
    return disaster_event_service.reset_demo_disaster(
        db=db,
        state=req.state,
        district=req.district,
    )
