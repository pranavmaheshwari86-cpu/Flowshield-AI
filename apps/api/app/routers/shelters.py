from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.shelter import Shelter
from ..schemas.shelter import ShelterResponse
from ..services.shelter_service import shelter_service

router = APIRouter(prefix="/shelters", tags=["Shelter Intelligence"])


@router.get("", response_model=List[ShelterResponse])
def list_shelters(db: Session = Depends(get_db)):
    shelters = db.query(Shelter).all()
    return [
        ShelterResponse(
            id=s.id,
            name=s.name,
            type=s.type,
            total_capacity=s.total_capacity,
            current_occupancy=s.current_occupancy,
            available_capacity=s.available_capacity,
            occupancy_percentage=s.occupancy_percentage,
            status=s.status,
            has_medical=s.has_medical,
            has_power_backup=s.has_power_backup,
            contact_person=s.contact_person,
            contact_phone=s.contact_phone,
            latitude=s.latitude,
            longitude=s.longitude,
        )
        for s in shelters
    ]


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
            detail="No shelters found for the specified village",
        )
    return [ShelterResponse(**r) for r in results]


@router.get("/nearest/{village_id}", response_model=List[ShelterResponse])
def get_nearest_shelters_path(
    village_id: str,
    limit: int = 3,
    db: Session = Depends(get_db),
):
    results = shelter_service.get_nearest_shelters(db, village_id, limit=limit)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shelters found for the specified village",
        )
    return [ShelterResponse(**r) for r in results]
