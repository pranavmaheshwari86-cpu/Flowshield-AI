"""Model registry and governance router for FlowShield."""

from fastapi import APIRouter
from ..services.model_registry import model_registry_service

router = APIRouter(prefix="/models", tags=["Model Registry & Governance"])


@router.get("/status")
def get_models_status():
    """Returns complete model registry status, geographic boundaries, and operational models."""
    return model_registry_service.get_status_overview()
