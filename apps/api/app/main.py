from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .utils.ssl_context import configure_ssl_context
configure_ssl_context()

from .config import settings
from .database import engine, Base, reconcile_sqlite_schema
from .services.prediction_service import prediction_service
from .routers import (
    health_router,
    auth_router,
    villages_router,
    predictions_router,
    risk_router,
    alerts_router,
    shelters_router,
    routes_router,
    map_data_router,
    simulation_router,
    system_router,
    ai_router,
    telemetry_router,
    national_router,
    historical_router,
    hazards_router,
    forecast_risk_router,
    realtime_router,
    model_admin_router,
    models_router,
    rainfall_router,
    regional_predictions_router,
    geography_router,
    data_sources_router,
    disaster_events_router,
    agro_monitoring_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist, reconcile schema & load ML model
    print(f"Starting {settings.PROJECT_NAME} ({settings.ENVIRONMENT})...")
    Base.metadata.create_all(bind=engine)
    reconcile_sqlite_schema(engine, Base)
    
    # Load ML Model & SHAP Explainer
    loaded = prediction_service.load_artifacts()
    if loaded:
        print("ML Model and SHAP Explainer successfully loaded.")
    else:
        print("Warning: ML model not loaded on startup. Ensure train.py has run.")

    yield
    print("Shutting down Flowshield API service...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Operational Flash Flood Decision Support System for Hilly Regions (SIH PS 26192)",
    version="1.0.0",
    lifespan=lifespan,
)

# Set up CORS (supports localhost, Vercel deployments, and wildcard environments with credentials)
cors_origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
allow_all_origins = "*" in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=[] if allow_all_origins else [o for o in cors_origins if o != "*"],
    allow_origin_regex=r"^https?://.*" if allow_all_origins else r"^https?://(localhost|127\.0\.0\.1|.*\.vercel\.app)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level health endpoint
app.include_router(health_router)

# Mount all domain routers under /api/v1
prefix = settings.API_V1_PREFIX
app.include_router(health_router, prefix=prefix)
app.include_router(auth_router, prefix=prefix)
app.include_router(villages_router, prefix=prefix)
app.include_router(predictions_router, prefix=prefix)
app.include_router(risk_router, prefix=prefix)
app.include_router(alerts_router, prefix=prefix)
app.include_router(shelters_router, prefix=prefix)
app.include_router(routes_router, prefix=prefix)
app.include_router(geography_router, prefix=prefix)
app.include_router(data_sources_router, prefix=prefix)
app.include_router(map_data_router, prefix=prefix)
app.include_router(simulation_router, prefix=prefix)
app.include_router(system_router, prefix=prefix)
app.include_router(ai_router, prefix=prefix)
app.include_router(telemetry_router, prefix=prefix)
app.include_router(national_router, prefix=prefix)
app.include_router(historical_router, prefix=prefix)
app.include_router(hazards_router, prefix=prefix)
app.include_router(forecast_risk_router, prefix=prefix)
app.include_router(realtime_router, prefix=prefix)
app.include_router(model_admin_router, prefix=prefix)
app.include_router(models_router, prefix=prefix)
app.include_router(rainfall_router, prefix=prefix)
app.include_router(regional_predictions_router, prefix=prefix)
app.include_router(disaster_events_router, prefix=prefix)
app.include_router(ai_router, prefix="/api")
app.include_router(hazards_router, prefix="/api")
app.include_router(rainfall_router, prefix="/api")
app.include_router(regional_predictions_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(geography_router, prefix="/api")
app.include_router(data_sources_router, prefix="/api")
app.include_router(disaster_events_router, prefix="/api")
app.include_router(agro_monitoring_router, prefix=f"{prefix}/agro-monitoring")
app.include_router(agro_monitoring_router, prefix="/api/agro-monitoring")


@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "tagline": "Predict Early. Act Faster. Save Lives.",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "/api/v1/system/status",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred", "type": str(type(exc).__name__)},
    )
