"""
apps/api/app/schemas/agro_monitoring.py
Flowshield — AgroMonitoring Soil Moisture Integration Pydantic Schemas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class InitGridRequest(BaseModel):
    scope: str = Field(
        default="district",
        description="Scope of grid creation: 'district', 'state', or 'all'"
    )
    state_name: Optional[str] = Field(
        default="Himachal Pradesh",
        description="Target State if scope is 'state' or 'district'"
    )
    district_name: Optional[str] = Field(
        default="Mandi",
        description="Target District if scope is 'district'"
    )
    register_with_agro: bool = Field(
        default=True,
        description="Whether to register generated grid cells with AgroMonitoring API immediately"
    )
    batch_limit: int = Field(
        default=5,
        ge=1,
        le=500,
        description="Maximum number of polygons to register in this call (preserves free-tier quota)"
    )


class MonitoringPolygonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agro_polygon_id: Optional[str] = None
    name: str
    country: str = "India"
    state: Optional[str] = None
    district: Optional[str] = None
    area_hectares: float
    centroid_lat: float
    centroid_lon: float
    status: str  # PENDING, REGISTERED, FAILED, LIMIT_EXCEEDED
    error_message: Optional[str] = None
    last_soil_update: Optional[datetime] = None
    latest_moisture: Optional[float] = None
    moisture_tier: Optional[str] = None  # LOW, MODERATE, HIGH, VERY_HIGH
    latest_soil_temp: Optional[float] = None
    latest_surface_temp: Optional[float] = None


class SoilObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    polygon_id: str
    agro_polygon_id: Optional[str] = None
    soil_moisture: float
    soil_temperature: Optional[float] = None
    surface_temperature: Optional[float] = None
    observation_timestamp: datetime
    created_at: datetime


class AgroStatusResponse(BaseModel):
    api_configured: bool
    total_cells_generated: int
    registered_polygons: int
    pending_polygons: int
    failed_polygons: int
    limit_exceeded_polygons: int
    last_soil_sync: Optional[datetime] = None
    plan_notice: Optional[str] = None
    active_states: List[str] = []
    active_districts: List[str] = []


class SoilGeoJSONFeature(BaseModel):
    type: str = "Feature"
    id: str
    geometry: Dict[str, Any]
    properties: Dict[str, Any]


class SoilGeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[SoilGeoJSONFeature]
    metadata: Dict[str, Any]
