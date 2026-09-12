"""
apps/api/app/routers/telemetry.py
Flowshield — Telemetry API Endpoints (Live Feed, Real-Time Sync & Degraded Mode Status) (v2.4)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.live_telemetry_service import live_telemetry_service
from ..services.freshness_service import freshness_service

router = APIRouter(prefix="/telemetry", tags=["Live Real-Time Telemetry"])


@router.post("/sync-live")
def sync_live_telemetry(db: Session = Depends(get_db)):
    """
    Acquires real-time weather and precipitation telemetry from Open-Meteo & CWC gauges
    for all monitored settlements, feeds into V2 model, and updates risk.
    Falls back gracefully to cached observations if upstream network fails.
    """
    result = live_telemetry_service.sync_live_telemetry(db)
    return result


@router.post("/ingest")
def ingest_custom_telemetry(
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    Ingests live telemetry from an external IoT sensor, rain gauge, or weather station.
    Saves observation, executes V2 flood prediction, computes risk, and fires alerts.
    """
    from datetime import datetime, timezone
    from ..models.village import Village
    from ..models.observation import EnvironmentalObservation
    from ..models.prediction import Prediction
    from ..models.risk_snapshot import RiskSnapshot
    from ..services.prediction_service import prediction_service
    from ..services.risk_engine import risk_engine
    from ..services.alert_engine import alert_engine
    from ..services.event_bus import event_bus

    village_ref = payload.get("village_id") or payload.get("village_name") or payload.get("location")
    if not village_ref:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required field 'village_id' or 'village_name'",
        )

    village = db.query(Village).filter(Village.id == str(village_ref)).first()
    if not village:
        village = db.query(Village).filter(Village.name.ilike(f"%{village_ref}%")).first()
    if not village:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Village with ID or name '{village_ref}' not found",
        )

    from datetime import datetime, timezone, timedelta
    from ..services.rainfall_accumulator import rainfall_accumulator

    now = datetime.now(timezone.utc)
    rain_1h = float(payload.get("rainfall_1h", payload.get("rainfall_1h_mm", 0.0)))
    
    # Check if explicit accumulations were supplied
    has_explicit_3h = "rainfall_3h" in payload or "rainfall_3h_mm" in payload
    has_explicit_6h = "rainfall_6h" in payload or "rainfall_6h_mm" in payload
    has_explicit_12h = "rainfall_12h" in payload or "rainfall_12h_mm" in payload
    has_explicit_24h = "rainfall_24h" in payload or "rainfall_24h_mm" in payload
    has_explicit_72h = "rainfall_72h" in payload or "rainfall_72h_mm" in payload
    
    if not (has_explicit_3h and has_explicit_6h and has_explicit_12h and has_explicit_24h and has_explicit_72h):
        # Query real historical observations to calculate honest rolling accumulations
        prior_obs = (
            db.query(EnvironmentalObservation)
            .filter(
                EnvironmentalObservation.village_id == village.id,
                EnvironmentalObservation.timestamp >= now - timedelta(hours=72)
            )
            .order_by(EnvironmentalObservation.timestamp.asc())
            .all()
        )
        obs_list = [
            {
                "timestamp": o.timestamp,
                "rainfall_mm": float(o.rainfall_1h or 0.0),
                "rainfall_rate_mm_hr": float(o.rainfall_intensity if o.rainfall_intensity is not None else (o.rainfall_1h or 0.0)),
            }
            for o in prior_obs
        ]
        obs_list.append({
            "timestamp": now,
            "rainfall_mm": rain_1h,
            "rainfall_rate_mm_hr": rain_1h,
        })
        accums = rainfall_accumulator.calculate_rolling_accumulations(obs_list, now, current_rate=rain_1h)
        calc_3h = accums["3h"]
        calc_6h = accums["6h"]
        calc_12h = accums["12h"]
        calc_24h = accums["24h"]
        calc_72h = accums["72h"]
    else:
        calc_3h = calc_6h = calc_12h = calc_24h = calc_72h = None

    rain_3h = float(payload.get("rainfall_3h", payload.get("rainfall_3h_mm", calc_3h if calc_3h is not None else rain_1h)))
    rain_6h = float(payload.get("rainfall_6h", payload.get("rainfall_6h_mm", calc_6h if calc_6h is not None else rain_3h)))
    rain_12h = float(payload.get("rainfall_12h", payload.get("rainfall_12h_mm", calc_12h if calc_12h is not None else rain_6h)))
    rain_24h = float(payload.get("rainfall_24h", payload.get("rainfall_24h_mm", calc_24h if calc_24h is not None else rain_12h)))
    rain_72h = float(payload.get("rainfall_72h", payload.get("rainfall_72h_mm", calc_72h if calc_72h is not None else rain_24h)))

    if "soil_moisture" in payload or "soil_saturation_pct" in payload:
        soil_moist = float(payload.get("soil_moisture", payload.get("soil_saturation_pct")))
    else:
        soil_moist = min(95.0, max(20.0, 48.0 + (rain_24h * 0.35)))

    deep_soil = float(payload.get("deep_soil_moisture", payload.get("deep_soil_saturation_pct", soil_moist)))
    river_lvl = float(payload.get("river_level", payload.get("river_level_m", 0.0)))
    river_chg = float(payload.get("river_level_change", payload.get("river_level_change_m", 0.0)))
    
    temp_c = float(payload["temperature"]) if "temperature" in payload else (float(payload["temperature_c"]) if "temperature_c" in payload else None)
    humidity = float(payload["humidity"]) if "humidity" in payload else (float(payload["relative_humidity_pct"]) if "relative_humidity_pct" in payload else None)
    pressure = float(payload["surface_pressure"]) if "surface_pressure" in payload else (float(payload["surface_pressure_hpa"]) if "surface_pressure_hpa" in payload else None)
    wind = float(payload["wind_speed"]) if "wind_speed" in payload else (float(payload["wind_speed_kmh"]) if "wind_speed_kmh" in payload else None)

    obs = EnvironmentalObservation(
        village_id=village.id,
        timestamp=now,
        rainfall_1h=rain_1h,
        rainfall_3h=rain_3h,
        rainfall_6h=rain_6h,
        rainfall_24h=rain_24h,
        rainfall_intensity=rain_1h,
        soil_moisture=soil_moist,
        river_level=river_lvl,
        river_level_change=river_chg,
        rainfall_12h=rain_12h,
        rainfall_72h=rain_72h,
        deep_soil_moisture=deep_soil,
        soil_moisture_change=None,
        river_level_change_1h=river_chg,
        river_level_rate=None,
        temperature=temp_c,
        humidity=humidity,
        surface_pressure=pressure,
        wind_speed=wind,
        source=payload.get("source", "Custom IoT Sensor Telemetry"),
        source_type="AUTOMATED_STATION",
        data_state="OBSERVED",
        data_quality_status="VALID",
        data_quality_score=1.0,
        source_timestamp=now,
        retrieved_at=now,
    )
    db.add(obs)
    db.flush()

    feature_dict = {
        "rainfall_1h_mm": rain_1h,
        "rainfall_3h_mm": rain_3h,
        "rainfall_6h_mm": rain_6h,
        "rainfall_24h_mm": rain_24h,
        "rainfall_72h_mm": rain_72h,
        "soil_saturation_pct": soil_moist,
        "deep_soil_saturation_pct": deep_soil,
        "temperature_c": temp_c,
        "relative_humidity_pct": humidity,
        "surface_pressure_hpa": pressure,
        "wind_speed_kmh": wind,
        "elevation_m": village.elevation,
        "catchment_slope_deg": village.slope,
        "dist_to_river_m": village.distance_to_river * 1000.0 if village.distance_to_river <= 20.0 else village.distance_to_river,
        "upstream_drainage_sqkm": 3200.0,
        "vulnerability_index": village.vulnerability_index,
    }

    pred_res = prediction_service.predict_full(feature_dict, data_quality_score=1.0, freshness_seconds=0)

    pred = Prediction(
        village_id=village.id,
        observation_id=obs.id,
        flood_probability=pred_res["flood_probability"],
        calibrated_probability=pred_res["calibrated_probability"],
        decision_threshold=pred_res["decision_threshold"],
        threshold_exceeded=pred_res["threshold_exceeded"],
        model_integrity_status=pred_res["model_integrity_status"],
        prediction_quality=pred_res["prediction_quality"],
        model_version=pred_res["model_version"],
        feature_contributions=pred_res["top_contributing_factors"],
        created_at=now,
    )
    db.add(pred)
    db.flush()

    past_snaps = (
        db.query(RiskSnapshot)
        .filter(RiskSnapshot.village_id == village.id)
        .order_by(RiskSnapshot.timestamp.desc())
        .limit(3)
        .all()
    )
    past_scores = [s.risk_score for s in reversed(past_snaps)] if past_snaps else []
    trend_factor, trend_str = risk_engine.calculate_trend_factor(past_scores)

    risk_score, risk_lvl, color_hex, _ = risk_engine.compute_operational_risk(
        flood_probability=pred_res["calibrated_probability"],
        trend_factor=trend_factor,
        vulnerability_index=village.vulnerability_index,
        data_quality_score=1.0,
        freshness_seconds=0,
    )

    snapshot = RiskSnapshot(
        village_id=village.id,
        prediction_id=pred.id,
        risk_score=risk_score,
        risk_level=risk_lvl,
        trend=trend_str,
        timestamp=now,
    )
    db.add(snapshot)

    alert = alert_engine.evaluate_and_create_alert(
        db=db,
        village=village,
        risk_score=risk_score,
        risk_level=risk_lvl,
        prediction_id=pred.id,
        top_contributors=pred_res["top_contributing_factors"],
    )

    db.commit()

    event_bus.publish_sync(
        "telemetry_update",
        {
            "village_id": village.id,
            "village_name": village.name,
            "risk_score": risk_score,
            "risk_level": risk_lvl,
            "rainfall_1h": rain_1h,
            "river_level": river_lvl,
            "timestamp": now.isoformat(),
        },
    )

    return {
        "status": "success",
        "message": f"Real-time observation ingested for {village.name}",
        "village_id": village.id,
        "village_name": village.name,
        "observation_id": obs.id,
        "risk_score": risk_score,
        "risk_level": risk_lvl,
        "flood_probability": pred_res["calibrated_probability"],
        "alert_triggered": alert is not None,
    }


@router.get("/status")
def get_telemetry_status(db: Session = Depends(get_db)):
    """
    Returns the current status of the live data acquisition pipeline,
    including provider health, freshness state, and 5-tier degradation status.
    """
    sys_status = freshness_service.evaluate_system_status(db)

    return {
        "status": live_telemetry_service.last_sync_status,
        "provider": live_telemetry_service.provider,
        "last_sync_time": (
            live_telemetry_service.last_sync_time.isoformat()
            if live_telemetry_service.last_sync_time
            else None
        ),
        "last_sync_timestamp": (
            live_telemetry_service.last_sync_time.isoformat()
            if live_telemetry_service.last_sync_time
            else None
        ),
        "synced_villages_count": live_telemetry_service.last_synced_count,
        "is_live_active": live_telemetry_service.last_sync_time is not None,
        "provider_health": sys_status["status"],
        "freshness_state": sys_status["freshness_state"],
        "degradation_tier": sys_status["degradation_tier"],
        "degradation_tier_name": sys_status["degradation_tier_name"],
        "degradation_description": sys_status["degradation_description"],
        "total_cached_observations": sys_status["total_cached_observations"],
        "recent_sync_events": sys_status["recent_sync_events"],
        "system_status": sys_status,
    }
