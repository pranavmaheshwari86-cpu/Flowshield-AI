from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal, Any
from datetime import datetime

from .location_capability import LocationCapability
from .precipitation import PrecipitationForecastResponse


class TemporalProvenance(BaseModel):
    """Guarantees auditable temporal tracking for all telemetry."""
    source_name: str = Field(..., description="Provider or station name")
    source_id: Optional[str] = Field(None, description="Station identifier or sensor ID")
    observed_at: Optional[datetime] = Field(None, description="Physical observation measurement time")
    valid_at: datetime = Field(..., description="Target time for which this metric is applicable")
    generated_at: datetime = Field(..., description="Time this forecast or model inference was computed")
    fetched_at: datetime = Field(..., description="Time FlowShield ingested this record from external provider")
    quality_status: Literal["GOOD", "DEGRADED", "STALE", "MISSING"]
    is_synthetic: bool = Field(False, description="Flag declaring if record is from demo fixtures")


class ObservationSnapshot(BaseModel):
    rainfall_rate_mm_hr: float
    rainfall_1h_mm: float
    rainfall_3h_mm: float
    rainfall_6h_mm: float
    rainfall_12h_mm: float = 0.0
    rainfall_24h_mm: float
    river_stage_meters: Optional[float] = None
    river_danger_mark_meters: Optional[float] = None
    river_surge_rate_m_hr: Optional[float] = None
    soil_moisture_m3_m3: float
    soil_saturation_pct: float
    # Live atmospheric telemetry (OWM / Open-Meteo)
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    provenance: TemporalProvenance


class HistoricalSeriesPoint(BaseModel):
    relative_hour: int = Field(..., description="Negative relative hour e.g. -6, -3, -1, 0")
    timestamp: datetime
    observed_rainfall_rate: Optional[float] = None
    observed_river_stage: Optional[float] = None
    observed_soil_saturation: Optional[float] = None
    operational_risk_score: float
    is_forecast: bool = Field(False, description="Ground truth observed status")
    units: Dict[str, str] = Field(default_factory=lambda: {
        "rainfall": "mm/h",
        "river_stage": "m MSL",
        "soil_saturation": "%",
        "risk_score": "0-100 index"
    })
    source_attribution: str = Field("Synoptic Weather Observations & CWC Bulletin Telemetry", description="Telemetry origin")
    data_state: str = Field("OBSERVED", description="Data state flag")


class ForecastHorizonPoint(BaseModel):
    horizon_hours: int = Field(..., description="Projection horizon: 1, 3, 6, 12, 24, 48")
    forecast_timestamp: datetime
    projected_rainfall_rate_mm_hr: Optional[float] = None
    cumulative_precipitation_mm: Optional[float] = None
    projected_river_stage_meters: Optional[float] = None
    projected_soil_saturation_pct: Optional[float] = None
    raw_flood_probability: Optional[float] = None
    calibrated_flood_probability: Optional[float] = None
    operational_risk_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    risk_tier: Literal["LOW", "WATCH", "HIGH", "CRITICAL", "UNSUPPORTED"] = "LOW"
    uncertainty_band: Optional[Dict[str, Optional[float]]] = Field(None, description="Keys: p10, p50, p90")
    primary_risk_driver: str
    is_forecast: bool = Field(True, description="Forecast status flag")
    units: Dict[str, str] = Field(default_factory=lambda: {
        "rainfall_rate": "mm/h",
        "cumulative_rainfall": "mm",
        "river_stage": "m MSL",
        "soil_saturation": "%",
        "risk_score": "0-100 index",
        "probability": "0.0-1.0 ratio"
    })
    source_attribution: str = Field("Open-Meteo ECMWF Integrated Forecasting System (0.1° Grid) & Production ML Model", description="Source attribution")
    data_state: str = Field("NUMERICAL_PROJECTION", description="Projection status")


class RiskDriverContribution(BaseModel):
    driver_name: str
    contribution_points: float = Field(..., description="Score points contributed to risk (sum = risk_score)")
    metric_value_observed: str
    physical_impact_description: str


class ThresholdCrossingAnalysis(BaseModel):
    threshold_name: Literal["WATCH", "HIGH", "CRITICAL"]
    threshold_value: float
    is_crossed: bool
    earliest_crossing_hour: Optional[float] = None
    most_likely_crossing_hour: Optional[float] = None
    latest_crossing_hour: Optional[float] = None
    lead_time_hours: Optional[float] = None
    human_status_message: str


class HydrologicalAnalysis(BaseModel):
    river_name: str
    gauge_station_name: str
    current_stage_meters: Optional[float] = None
    danger_mark_meters: Optional[float] = None
    warning_mark_meters: Optional[float] = None
    hfl_meters: Optional[float] = None
    margin_to_danger_meters: Optional[float] = None
    rate_of_rise_m_per_hr: Optional[float] = None
    hydraulic_trend: Literal["RISING", "STEADY", "FALLING", "UNKNOWN"]
    upstream_dam_discharge_cumec: Optional[float] = None
    dam_name: Optional[str] = None
    telemetry_source: Optional[str] = None
    bulletin_timestamp: Optional[str] = None
    data_state: Optional[str] = None


class ExposureAnalysis(BaseModel):
    village_population: int
    vulnerable_demographic_pct: float
    critical_infrastructure: Dict[str, int] = Field(..., description="Counts of schools, hospitals, bridges, road_segments")
    nearest_safe_shelter_name: Optional[str] = None
    shelter_distance_km: Optional[float] = None
    shelter_capacity_remaining: Optional[int] = None
    shelter_elevation_advantage_m: Optional[float] = None
    evacuation_route_status: Literal["CLEAR", "BLOCKED", "DATA_UNAVAILABLE"]
    active_hazard_blockage_description: Optional[str] = None


class DataStreamQuality(BaseModel):
    stream_name: str
    status: Literal["GOOD", "DEGRADED", "STALE", "MISSING"]
    last_updated_at: Optional[datetime] = None
    staleness_seconds: Optional[int] = None
    source_attribution: str


class DataQualityMatrix(BaseModel):
    overall_health: Literal["OPTIMAL", "ACCEPTABLE", "DEGRADED", "COMPROMISED"]
    active_mode: Literal["LIVE", "DEMO"]
    streams: List[DataStreamQuality]


class SettlementInfo(BaseModel):
    id: str
    name: str
    district: str
    state: str
    latitude: float
    longitude: float
    elevation_meters: float
    river_basin: str


class TimelineDetailedResponse(BaseModel):
    settlement: SettlementInfo
    generated_at: datetime
    current_situation: ObservationSnapshot
    historical_series: List[HistoricalSeriesPoint]
    forecast_horizons: List[ForecastHorizonPoint]
    situation_summary: Dict[str, str]
    risk_drivers: List[RiskDriverContribution]
    threshold_analysis: ThresholdCrossingAnalysis
    peak_analysis: Dict[str, Optional[float]]
    hydrology: HydrologicalAnalysis
    exposure: ExposureAnalysis
    data_quality: DataQualityMatrix
    model_metadata: Dict[str, str]
    flood_outlook: Optional[Dict[str, Any]] = None
    location_capabilities: Optional[LocationCapability] = None
    precipitation_forecast: Optional[PrecipitationForecastResponse] = None


class SettlementHierarchyItem(BaseModel):
    id: str
    name: str
    basin: str
    latitude: float
    longitude: float
    elevation_m: float


class DistrictHierarchyItem(BaseModel):
    name: str
    settlements: List[SettlementHierarchyItem]


class StateHierarchyItem(BaseModel):
    name: str
    districts: List[DistrictHierarchyItem]


class TimelineLocationHierarchy(BaseModel):
    states: List[StateHierarchyItem]
