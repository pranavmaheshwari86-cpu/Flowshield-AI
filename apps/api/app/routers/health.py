from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..services.prediction_service import prediction_service

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    db_status = "unhealthy"
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"

    model_ready = prediction_service.is_ready
    model_version = (
        prediction_service.metadata.get("model_version", "unknown")
        if prediction_service.metadata
        else "not_loaded"
    )

    return {
        "status": "healthy" if db_status == "healthy" and model_ready else "degraded",
        "database": db_status,
        "model": {
            "loaded": model_ready,
            "version": model_version,
        },
        "system": "Flowshield Environmental Intelligence Core",
    }
