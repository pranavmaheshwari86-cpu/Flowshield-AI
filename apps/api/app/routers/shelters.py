"""
apps/api/app/routers/shelters.py
Flowshield — Shelter Intelligence Endpoints (v3.0)
Exposes shelter listing, multi-factor recommendation, nearest search, and source provenance.
Strict Non-Fabrication Policy:
- Capacities are null when unpublished.
- Multi-factor scoring avoids high-hazard corridors.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.shelter import Shelter
from ..schemas.shelter import ShelterResponse
from ..services.shelter_service import shelter_service

router = APIRouter(prefix="/shelters", tags=["Shelter Intelligence"])


@router.get("", response_model=List[ShelterResponse])
def list_shelters(
    state: Optional[str] = Query(None, description="Filter by state (e.g. Uttarakhand, Himachal Pradesh)"),
    district: Optional[str] = Query(None, description="Filter by district (e.g. Rudraprayag, Mandi, Chamoli)"),
    search: Optional[str] = Query(None, description="Search term in name, type, or locality"),
    verified_only: bool = Query(False, description="Filter only VERIFIED or PARTIALLY_VERIFIED shelters"),
    operational_only: bool = Query(False, description="Filter only OPERATIONAL shelters"),
    has_medical: Optional[bool] = Query(None, description="Filter by medical readiness"),
    has_power: Optional[bool] = Query(None, description="Filter by power generator availability"),
    ref_lat: Optional[float] = Query(None, description="Reference latitude for distance calculation"),
    ref_lon: Optional[float] = Query(None, description="Reference longitude for distance calculation"),
    sort_by: str = Query("distance", description="Sort order: distance, confidence, capacity, name"),
    db: Session = Depends(get_db),
):
    """
    Returns verified disaster shelters with authoritative source provenance.
    """
    results = shelter_service.list_shelters(
        db=db,
        state=state,
        district=district,
        search=search,
        verified_only=verified_only,
        operational_only=operational_only,
        has_medical=has_medical,
        has_power=has_power,
        ref_lat=ref_lat,
        ref_lon=ref_lon,
        sort_by=sort_by,
    )
    return [ShelterResponse(**r) for r in results]


@router.get("/recommended", response_model=List[ShelterResponse])
def get_recommended_shelters(
    lat: float = Query(..., description="Origin latitude"),
    lon: float = Query(..., description="Origin longitude"),
    state: Optional[str] = Query(None, description="State name"),
    district: Optional[str] = Query(None, description="District name"),
    village_id: Optional[str] = Query(None, description="Settlement ID"),
    limit: int = Query(5, ge=1, le=20, description="Max shelters to return"),
    db: Session = Depends(get_db),
):
    """
    Computes multi-factor evacuation suitability score across distance, route safety,
    facility readiness, and source confidence. Ranks optimal options and flags hazard zones.
    """
    results = shelter_service.get_recommended_shelters(
        db=db,
        origin_lat=lat,
        origin_lon=lon,
        state=state,
        district=district,
        village_id=village_id,
        limit=limit,
    )
    return [ShelterResponse(**r) for r in results]


@router.get("/nearest", response_model=List[ShelterResponse])
def get_nearest_shelters(
    village_id: str = Query(..., description="UUID of the settlement"),
    limit: int = 3,
    db: Session = Depends(get_db),
):
    results = shelter_service.get_nearest_shelters(db, village_id, limit=limit)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shelters found for the specified settlement",
        )
    return [ShelterResponse(**r) for r in results]


@router.get("/{shelter_id}", response_model=ShelterResponse)
def get_shelter_by_id(shelter_id: str, db: Session = Depends(get_db)):
    shelter = db.query(Shelter).filter(Shelter.id == shelter_id).first()
    if not shelter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelter with id '{shelter_id}' not found",
        )
    return ShelterResponse(**shelter_service._format_shelter_dict(shelter))
