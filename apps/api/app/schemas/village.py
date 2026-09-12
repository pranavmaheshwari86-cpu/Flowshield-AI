from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class VillageBase(BaseModel):
    name: str
    tehsil: str
    district: str
    state: str = "Uttarakhand"
    population: int
    elevation: float
    slope: float
    distance_to_river: float
    historical_flood_frequency: float
    vulnerability_index: float
    latitude: float
    longitude: float


class VillageResponse(VillageBase):
    id: str
    risk_score: Optional[float] = 10.0
    risk_level: Optional[str] = "LOW"
    trend: Optional[str] = "STABLE"
    has_active_alert: Optional[bool] = False
    latest_observation_time: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VillageDetailResponse(VillageResponse):
    current_conditions: Optional[Dict[str, Any]] = None
    top_contributors: Optional[List[Dict[str, Any]]] = None
    historical_risk_trend: Optional[List[Dict[str, Any]]] = None
    active_alerts: Optional[List[Dict[str, Any]]] = None
    recommended_actions: Optional[List[str]] = None
    nearest_shelter: Optional[Dict[str, Any]] = None
    evacuation_route: Optional[Dict[str, Any]] = None
    latest_prediction: Optional[Dict[str, Any]] = None
    calibrated_probability: Optional[float] = None
    decision_threshold: Optional[float] = 0.08
    threshold_exceeded: Optional[bool] = False
    model_version: Optional[str] = None
