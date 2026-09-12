from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SimulationStartRequest(BaseModel):
    scenario: str = "GRADUAL_MONSOON"  # GRADUAL_MONSOON, CLOUDBURST, MULTI_DAY
    seed: int = 26192


class SimulationStatusResponse(BaseModel):
    simulation_id: str
    scenario_name: str
    status: str  # IDLE, RUNNING, PAUSED, COMPLETED
    current_stage: int  # 0 to 4
    stage_name: str
    current_substep: int  # 0 to 19
    total_steps: int
    progress_percentage: float
    seed: int


class SimulationStepResponse(BaseModel):
    simulation_id: str
    stage: int
    stage_name: str
    substep: int
    total_steps: int
    progress_percentage: float
    villages_updated: int
    new_alerts_triggered: int
    system_summary: Dict[str, Any]
    active_alerts: List[Dict[str, Any]]
