"""
apps/api/app/routers/rainfall.py
Flowshield — Real-Time Rainfall & Precipitation API Endpoints
Serves live normalized precipitation telemetry for Leaflet GIS visualization.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.rainfall_service import rainfall_service

router = APIRouter(prefix="/rainfall", tags=["Real-Time Rainfall Telemetry"])


@router.get("/current")
def get_current_rainfall(
    active_only: bool = Query(
        True,
        description="When true, returns only locations where rainfall > 0 mm/h. Set false to receive all monitored points.",
    ),
    force_refresh: bool = Query(
        False,
        description="Bypasses in-memory cache and initiates an immediate provider query.",
    ),
    db: Session = Depends(get_db),
):
    """
    Returns real-time precipitation measurements across India.
    Only measurable rainfall (>0 mm/h) is included by default.
    Includes data quality tagging (live | stale | unavailable) and centralized severity tiers.
    """
    return rainfall_service.get_live_rainfall(
        db=db,
        active_only=active_only,
        force_refresh=force_refresh,
    )


@router.get("/status")
def get_rainfall_status():
    """
    Returns the operational health, cache status, and provenance of the rainfall provider.
    """
    return rainfall_service.get_status()
