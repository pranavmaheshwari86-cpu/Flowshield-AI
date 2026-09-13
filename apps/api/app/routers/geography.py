"""
apps/api/app/routers/geography.py
Flowshield — Centralized Geographic Authority Endpoints (v3.0)
Exposes supported states, dependent districts, and settlements
synchronized with ML model coverage.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.geography_service import geography_service

router = APIRouter(prefix="/geography", tags=["Geographic Intelligence"])


@router.get("/states")
def get_supported_states(db: Session = Depends(get_db)):
    """
    Returns list of states supported by Flowshield ML models and disaster pipelines.
    No unsupported states are returned.
    """
    return geography_service.get_supported_states(db)


@router.get("/states/{state}/districts")
def get_districts_by_state(state: str, db: Session = Depends(get_db)):
    """
    Returns valid districts belonging strictly to the selected state.
    Provides map center, zoom, bounds, and shelter counts.
    """
    districts = geography_service.get_districts_by_state(db, state)
    if not districts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active districts found for state '{state}'. Ensure state is supported.",
        )
    return districts


@router.get("/districts/{district}/settlements")
def get_settlements_by_district(
    district: str,
    state: Optional[str] = "Uttarakhand",
    db: Session = Depends(get_db),
):
    """
    Returns settlements / villages for the selected district.
    """
    return geography_service.get_settlements_by_district(db, state, district)


@router.get("/coverage")
def get_coverage_summary(db: Session = Depends(get_db)):
    """
    Returns the comprehensive geographic coverage registry for the platform.
    """
    return geography_service.get_coverage_summary(db)


@router.get("/reverse-geocode")
def reverse_geocode_location(
    lat: float,
    lon: float,
    db: Session = Depends(get_db),
):
    """
    Resolves arbitrary coordinates to administrative region and nearest settlement.
    """
    from ..services.location_service import location_service
    return location_service.resolve_location(db, lat=lat, lon=lon)

