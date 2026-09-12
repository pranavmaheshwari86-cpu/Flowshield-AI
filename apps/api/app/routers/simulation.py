from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.simulation import (
    SimulationStartRequest,
    SimulationStatusResponse,
    SimulationStepResponse,
)
from ..services.simulation_engine import simulation_engine, STAGE_NAMES

router = APIRouter(prefix="/simulation", tags=["Simulation Engine"])


@router.post("/start", response_model=SimulationStatusResponse)
def start_simulation(req: SimulationStartRequest, db: Session = Depends(get_db)):
    sim = simulation_engine.start_simulation(db, scenario=req.scenario, seed=req.seed)
    return SimulationStatusResponse(
        simulation_id=sim.id,
        scenario_name=sim.scenario_name,
        status=sim.status,
        current_stage=sim.current_stage,
        stage_name=STAGE_NAMES[sim.current_stage],
        current_substep=sim.current_substep,
        total_steps=sim.total_steps,
        progress_percentage=round((sim.current_substep / 19.0) * 100.0, 1),
        seed=sim.seed,
    )


@router.post("/step", response_model=SimulationStepResponse)
def step_simulation(db: Session = Depends(get_db)):
    result = simulation_engine.step_simulation(db)
    return SimulationStepResponse(**result)


@router.post("/pause", response_model=SimulationStatusResponse)
def pause_simulation(db: Session = Depends(get_db)):
    sim = simulation_engine.pause_simulation(db)
    return SimulationStatusResponse(
        simulation_id=sim.id,
        scenario_name=sim.scenario_name,
        status=sim.status,
        current_stage=sim.current_stage,
        stage_name=STAGE_NAMES[sim.current_stage],
        current_substep=sim.current_substep,
        total_steps=sim.total_steps,
        progress_percentage=round((sim.current_substep / 19.0) * 100.0, 1),
        seed=sim.seed,
    )


@router.post("/reset")
def reset_simulation(db: Session = Depends(get_db)):
    return simulation_engine.reset_simulation(db)


@router.get("/state", response_model=SimulationStatusResponse)
@router.get("/status", response_model=SimulationStatusResponse)
def get_simulation_state(db: Session = Depends(get_db)):
    sim = simulation_engine.get_or_create_simulation(db)
    return SimulationStatusResponse(
        simulation_id=sim.id,
        scenario_name=sim.scenario_name,
        status=sim.status,
        current_stage=sim.current_stage,
        stage_name=STAGE_NAMES[sim.current_stage],
        current_substep=sim.current_substep,
        total_steps=sim.total_steps,
        progress_percentage=round((sim.current_substep / 19.0) * 100.0, 1),
        seed=sim.seed,
    )
