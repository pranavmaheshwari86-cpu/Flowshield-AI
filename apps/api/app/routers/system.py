from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.village import Village
from ..models.observation import EnvironmentalObservation
from ..models.simulation import Simulation
from ..services.prediction_service import prediction_service
from ..services.drift_monitor import drift_monitor

router = APIRouter(prefix="/system", tags=["System Status & Observability"])


@router.get("/status")
def get_system_status(db: Session = Depends(get_db)):
    village_count = db.query(Village).count()
    latest_obs = (
        db.query(EnvironmentalObservation)
        .order_by(EnvironmentalObservation.timestamp.desc())
        .first()
    )
    obs_count = db.query(EnvironmentalObservation).count()
    sim = db.query(Simulation).first()

    model_ready = prediction_service.is_ready
    model_version = (
        prediction_service.metadata.get("model_version", "flowshield-flood-risk-v2")
        if prediction_service.metadata
        else "flowshield-flood-risk-v2"
    )

    # Compute live drift summary
    drift_summary = drift_monitor.compute_drift_metrics(db, window_hours=48)

    return {
        "api": "online",
        "database": "online",
        "model": {
            "status": "loaded" if model_ready else "offline",
            "version": model_version,
            "feature_count": 15,
            "drift_level": drift_summary.get("drift_level", "HEALTHY"),
            "drift_score": drift_summary.get("overall_drift_score", 0.0),
        },
        "telemetry": {
            "villages_monitored": village_count,
            "total_observations": obs_count,
            "latest_observation_time": latest_obs.timestamp.isoformat() if latest_obs else None,
            "source_type": "Real ECMWF ERA5-Land Reanalysis & Open-Meteo",
            "data_provenance": "Copernicus ECMWF ERA5-Land + SRTM 30m Digital Elevation Model",
        },
        "simulation": {
            "status": sim.status if sim else "IDLE",
            "scenario": sim.scenario_name if sim else "GRADUAL_MONSOON",
            "stage": sim.current_stage if sim else 0,
            "substep": sim.current_substep if sim else 0,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/drift")
def get_detailed_drift_report(db: Session = Depends(get_db)):
    """Returns granular covariate and prediction drift analytics."""
    return drift_monitor.compute_drift_metrics(db, window_hours=48)
