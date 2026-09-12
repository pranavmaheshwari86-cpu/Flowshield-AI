from .health import router as health_router
from .auth import router as auth_router
from .villages import router as villages_router
from .predictions import router as predictions_router
from .risk import router as risk_router
from .alerts import router as alerts_router
from .shelters import router as shelters_router
from .routes import router as routes_router
from .map_data import router as map_data_router
from .simulation import router as simulation_router
from .system import router as system_router
from .ai import router as ai_router
from .telemetry import router as telemetry_router
from .national import router as national_router
from .historical import router as historical_router
from .hazards import router as hazards_router
from .forecast_risk import router as forecast_risk_router
from .realtime import router as realtime_router
from .model_admin import router as model_admin_router
from .models import router as models_router
from .rainfall import router as rainfall_router
from .regional_predictions import router as regional_predictions_router
from .geography import router as geography_router
from .data_sources import router as data_sources_router

__all__ = [
    "health_router",
    "auth_router",
    "villages_router",
    "predictions_router",
    "risk_router",
    "alerts_router",
    "shelters_router",
    "routes_router",
    "map_data_router",
    "simulation_router",
    "system_router",
    "ai_router",
    "telemetry_router",
    "national_router",
    "historical_router",
    "hazards_router",
    "forecast_risk_router",
    "realtime_router",
    "model_admin_router",
    "models_router",
    "rainfall_router",
    "regional_predictions_router",
    "geography_router",
    "data_sources_router",
]

