"""
apps/api/app/routers/regional_predictions.py
Flowshield — Regional Multi-Region Flood Prediction & Governance Endpoints

Exposes:
- GET /api/v1/regions — Catalog of all 10 supported Himalayan and NE regions with model status
- GET /api/v1/regions/{region_slug} — Regional boundary, climate, stations, and terrain details
- GET /api/v1/regions/{region_slug}/model-info — Regional model architecture, calibration, and holdout metrics
- POST /api/v1/predict/{region_slug} — Dedicated regional flood inference endpoint
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ml.registry.region_resolver import region_resolver, SUPPORTED_REGIONS
from ml.registry.model_registry import model_registry
from ml.inference.regional_predictor import regional_predictor

router = APIRouter(tags=["Multi-Region Flood Intelligence"])


class RegionalPredictionRequest(BaseModel):
    # Optional village ID
    village_id: Optional[str] = None

    # Canonical 15 Features
    rainfall_1h_mm: Optional[float] = Field(None, description="Precipitation accumulation in last 1 hour (mm)")
    rainfall_3h_mm: Optional[float] = Field(None, description="Precipitation accumulation in last 3 hours (mm)")
    rainfall_6h_mm: Optional[float] = Field(None, description="Precipitation accumulation in last 6 hours (mm)")
    rainfall_24h_mm: Optional[float] = Field(None, description="Precipitation accumulation in last 24 hours (mm)")
    rainfall_72h_mm: Optional[float] = Field(None, description="Precipitation accumulation in last 72 hours (mm)")
    soil_saturation_pct: Optional[float] = Field(None, description="Topsoil saturation 0-7cm (% field capacity)")
    deep_soil_saturation_pct: Optional[float] = Field(None, description="Deep soil saturation 7-28cm (% field capacity)")
    temperature_c: Optional[float] = Field(None, description="Ambient 2m air temperature (°C)")
    relative_humidity_pct: Optional[float] = Field(None, description="Relative humidity (%)")
    surface_pressure_hpa: Optional[float] = Field(None, description="Barometric surface pressure (hPa)")
    wind_speed_kmh: Optional[float] = Field(None, description="10m surface wind speed (km/h)")
    elevation_m: Optional[float] = Field(None, description="Station/village elevation (m)")
    catchment_slope_deg: Optional[float] = Field(None, description="Catchment slope incline (degrees)")
    dist_to_river_m: Optional[float] = Field(None, description="Distance to active river channel (m)")
    upstream_drainage_sqkm: Optional[float] = Field(None, description="Upstream contributing drainage area (km²)")

    # Contextual Modifiers
    vulnerability_index: Optional[float] = Field(0.50, description="Social/physical vulnerability [0.0, 1.0]")
    preparedness_factor: Optional[float] = Field(0.50, description="Evacuation preparedness index [0.0, 1.0]")


@router.get("/regions")
def list_regions():
    """
    Returns full catalog of all 10 supported flood regions with real-time model status.
    """
    regions_status = model_registry.list_all_status()
    results = []

    for slug in SUPPORTED_REGIONS:
        config = region_resolver.load_config(slug)
        reg_info = config.get("region", {})
        st = regions_status.get(slug, {})

        results.append({
            "slug": slug,
            "display_name": region_resolver.get_display_name(slug),
            "state": reg_info.get("state", slug.replace("_", " ").title()),
            "primary_basin": reg_info.get("primary_basin", "Himalayan Basin"),
            "climate_zone": reg_info.get("climate_zone", "Montane"),
            "station_count": len(config.get("stations", {})),
            "model_available": st.get("available", False),
            "production_status": st.get("production_status", "NOT_TRAINED"),
            "model_version": st.get("model_version", "unknown"),
            "calibration_method": st.get("calibration_method", "none"),
        })

    return {
        "count": len(results),
        "regions": results,
    }


@router.get("/regions/{region_slug}")
def get_region_details(region_slug: str):
    """
    Returns geographical boundary, climate profile, and monitoring stations for a region.
    """
    if not region_resolver.is_valid_region(region_slug):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region '{region_slug}' is not supported. Supported: {SUPPORTED_REGIONS}",
        )

    config = region_resolver.load_config(region_slug)
    model_st = model_registry.get_status(region_slug)

    return {
        "region_slug": region_slug,
        "display_name": region_resolver.get_display_name(region_slug),
        "region": config.get("region", {}),
        "boundary": config.get("boundary", {}),
        "stations": config.get("stations", {}),
        "reference_events": config.get("reference_events", []),
        "model_status": model_st,
    }


@router.get("/regions/{region_slug}/model-info")
def get_region_model_info(region_slug: str):
    """
    Returns trained model architecture, calibration metrics, holdout scores, and decision thresholds.
    """
    if not region_resolver.is_valid_region(region_slug):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region '{region_slug}' not supported.",
        )

    try:
        bundle = model_registry.get(hazard="flood", region=region_slug)
        eval_metrics = bundle.metadata.get("evaluation", {}).get("test", {})
        if not eval_metrics and "evaluation" in bundle.metadata:
            eval_metrics = bundle.metadata["evaluation"]

        return {
            "region": region_slug,
            "display_name": region_resolver.get_display_name(region_slug),
            "model_version": bundle.model_version,
            "model_type": bundle.metadata.get("model_type", type(bundle.model).__name__),
            "model_family": type(bundle.model).__name__,
            "status": bundle.production_status,
            "production_status": bundle.production_status,
            "calibration_method": bundle.calibration_method,
            "selected_threshold": bundle.threshold,
            "thresholds": bundle.thresholds,
            "metrics": eval_metrics,
            "metadata": bundle.metadata,
            "feature_schema": bundle.feature_schema,
        }
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve model info: {str(e)}",
        )


@router.post("/predict/{region_slug}")
def predict_regional_flood(region_slug: str, req: RegionalPredictionRequest):
    """
    Executes real-time explainable flood prediction for a specific region using its dedicated ML model.
    """
    if not region_resolver.is_valid_region(region_slug):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region '{region_slug}' not supported. Supported: {SUPPORTED_REGIONS}",
        )

    feature_dict = req.model_dump(exclude_unset=True)
    res = regional_predictor.predict(region_slug=region_slug, input_data=feature_dict)

    if res.get("status") == "model_unavailable":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=res.get("error", "Model artifact unavailable."),
        )

    return res
