from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: str
    village_id: str
    village_name: Optional[str] = None
    severity: str  # HIGH, CRITICAL
    status: str  # ACTIVE, ACKNOWLEDGED, RESOLVED
    headline: str
    trigger_reason: str
    top_contributors: List[Dict[str, Any]]
    recommended_actions: List[str]
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AcknowledgeRequest(BaseModel):
    acknowledged_by: str = "District Operator"
