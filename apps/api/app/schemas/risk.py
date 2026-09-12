from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class RiskCalculationRequest(BaseModel):
    flood_probability: float
    trend_factor: float = 1.0
    data_quality_score: float = 1.0
    freshness_seconds: int = 0
    vulnerability_index: float = 0.5


class RiskCalculationResponse(BaseModel):
    risk_score: int  # 0 to 100
    risk_level: str  # LOW, MODERATE, HIGH, CRITICAL
    color_hex: str
    headline: str
    is_capped_by_quality: bool


class RegionalRiskSummary(BaseModel):
    total_villages: int
    critical_count: int
    high_count: int
    moderate_count: int
    low_count: int
    active_alerts_count: int
    available_shelters_count: int
    system_status: str
    last_updated: datetime
