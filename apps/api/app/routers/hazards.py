"""
apps/api/app/routers/hazards.py
Flowshield — Multi-Hazard & Forecasting Endpoints (v2.4)
Exposes Landslide Screening Prototype, Precipitation Forecasting, and Soil Moisture Baselines.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.village import Village
from ..schemas.hazard import (
    LandslideAssessmentResponse,
    MultiHorizonForecastResponse,
    SoilMoistureForecastResponse,
)
from ..services.landslide_service import landslide_service
from ..services.forecast_service import forecast_service
from ..services.soil_forecast_service import soil_moisture_forecast_service

router = APIRouter(prefix="/hazards", tags=["Multi-Hazard & Forecasting"])


@router.get("/landslide/{village_id}", response_model=LandslideAssessmentResponse)
def get_landslide_assessment(village_id: str, db: Session = Depends(get_db)):
    """
    Returns empirical landslide susceptibility assessment for a settlement based on
    slope incline and antecedent precipitation. Tagged as PROTOTYPE_EMPIRICAL_THRESHOLD.
    """
    village = db.query(Village).filter(Village.id == village_id).first()
    if not village:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settlement with id '{village_id}' not found."
        )

    return landslide_service.assess_village_landslide_hazard(village, db=db)


@router.get("/forecast/{village_id}", response_model=MultiHorizonForecastResponse)
def get_weather_forecast(village_id: str, db: Session = Depends(get_db)):
    """
    Returns multi-horizon (+1h, +3h, +6h, +12h, +24h, +48h) precipitation forecast.
    Enforces honest uncertainty semantics (UNCERTAINTY_UNAVAILABLE when variance is absent).
    """
    village = db.query(Village).filter(Village.id == village_id).first()
    if not village:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settlement with id '{village_id}' not found."
        )

    return forecast_service.get_multi_horizon_forecast(village, db=db)


@router.get("/soil-moisture-forecast/{village_id}", response_model=SoilMoistureForecastResponse)
def get_soil_moisture_forecast(village_id: str, db: Session = Depends(get_db)):
    """
    Returns 1D water-balance soil saturation forecast (+1h to +48h).
    Decoupled from weather model; strictly tagged as PROTOTYPE_BASELINE.
    """
    village = db.query(Village).filter(Village.id == village_id).first()
    if not village:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settlement with id '{village_id}' not found."
        )

    return soil_moisture_forecast_service.get_soil_moisture_forecast(village, db=db)
