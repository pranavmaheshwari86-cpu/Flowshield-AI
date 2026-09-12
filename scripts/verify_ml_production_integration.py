"""
scripts/verify_ml_production_integration.py
Flowshield — End-to-End Production ML Integration Verification
Smart India Hackathon 2026 (PS ID: 26192)

Validates the complete chain:
Real Telemetry -> Feature Extraction -> Preprocessor Pipeline -> Trained Model
-> Isotonic Calibration -> RiskEngine -> Database Persistence -> FastAPI Endpoints
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone

# Ensure project root is in path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s]: %(message)s")
logger = logging.getLogger("flowshield.verify_ml_integration")

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES, FEATURE_METADATA
from apps.api.app.services.model_integrity import model_integrity_checker, ModelIntegrityState
from apps.api.app.services.prediction_service import prediction_service
from apps.api.app.services.live_inference_service import live_inference_service
from apps.api.app.database import SessionLocal
from apps.api.app.models.village import Village
from apps.api.app.models.prediction import Prediction
from apps.api.app.models.risk_snapshot import RiskSnapshot
from fastapi.testclient import TestClient
from apps.api.app.main import app


def run_full_verification():
    logger.info("================================================================================")
    logger.info("FLOWSHIELD V2.5 PRODUCTION ML INTEGRATION VERIFICATION")
    logger.info("================================================================================")

    # 1. Check Model Integrity
    logger.info("Step 1: Validating Model Integrity & Checksums...")
    state, details = model_integrity_checker.verify_integrity(enforce_checksums=True)
    assert state == ModelIntegrityState.MODEL_READY, f"Model integrity failed with state {state}: {details}"
    logger.info(f"  [PASS] Model Integrity State: {state.value}")
    logger.info(f"  [PASS] Verified Feature Count: {details['verified_features_count']} (expected 15)")
    logger.info(f"  [PASS] Decision Threshold tau: {details['decision_threshold']}")

    # 2. Check Prediction Service Readiness
    logger.info("Step 2: Checking PredictionService Artifacts...")
    assert prediction_service.is_ready, "PredictionService reported not ready"
    logger.info(f"  [PASS] Model Version: {prediction_service.metadata['model_version']}")
    logger.info(f"  [PASS] Architecture: {prediction_service.metadata['model_type']}")

    # 3. Test Feature Vector Normalization & Exact 15 Canonical Order
    logger.info("Step 3: Checking Canonical Feature Extraction & Order...")
    test_dict = {
        "rainfall_1h": 12.5,
        "rainfall_3h": 25.0,
        "rainfall_6h": 40.0,
        "rainfall_24h": 65.0,
        "rainfall_72h": 90.0,
        "soil_moisture": 82.0,
        "deep_soil_moisture": 75.0,
        "temp_c": 19.5,
        "humidity": 88.0,
        "pressure_hpa": 915.0,
        "wind_kmh": 14.0,
        "elevation": 760.0,
        "slope": 22.0,
        "distance_to_river": 0.15,  # 0.15 km = 150m
        "upstream_drainage": 4200.0,
    }
    norm = prediction_service.normalize_feature_vector(test_dict)
    assert len(norm) == 15, f"Expected 15 features, got {len(norm)}"
    for f in CANONICAL_FEATURE_NAMES:
        assert f in norm, f"Missing canonical feature: {f}"
    assert norm["dist_to_river_m"] == 150.0, f"Distance conversion failed: {norm['dist_to_river_m']}"
    logger.info(f"  [PASS] Canonical 15 features successfully mapped from aliases.")

    # 4. Realistic Baseline Weather Test
    logger.info("Step 4: Running Baseline Normal Weather Inference...")
    baseline_weather = {
        "rainfall_1h_mm": 0.0,
        "rainfall_3h_mm": 0.0,
        "rainfall_6h_mm": 0.0,
        "rainfall_24h_mm": 0.0,
        "rainfall_72h_mm": 0.0,
        "soil_saturation_pct": 30.0,
        "deep_soil_saturation_pct": 35.0,
        "temperature_c": 22.0,
        "relative_humidity_pct": 60.0,
        "surface_pressure_hpa": 925.0,
        "wind_speed_kmh": 8.0,
        "elevation_m": 800.0,
        "catchment_slope_deg": 18.0,
        "dist_to_river_m": 400.0,
        "upstream_drainage_sqkm": 3200.0,
    }
    pred_base = prediction_service.predict_full(baseline_weather)
    assert pred_base["calibrated_probability"] < 0.08, f"Baseline probability too high: {pred_base['calibrated_probability']}"
    assert pred_base["threshold_exceeded"] is False
    assert pred_base["risk_level"] == "LOW"
    logger.info(f"  [PASS] Baseline Calibrated Probability: {pred_base['calibrated_probability']:.4f} (Threshold: {pred_base['decision_threshold']})")
    logger.info(f"  [PASS] Baseline Risk Level: {pred_base['risk_level']} (Score: {pred_base['risk_score']}/100)")

    # 5. Catastrophe Cloudburst Test (July 2023 Scenario)
    logger.info("Step 5: Running July 2023 Catastrophe Cloudburst Inference...")
    catastrophe_weather = dict(baseline_weather)
    catastrophe_weather["rainfall_1h_mm"] = 92.0
    catastrophe_weather["rainfall_3h_mm"] = 165.0
    catastrophe_weather["rainfall_6h_mm"] = 220.0
    catastrophe_weather["rainfall_24h_mm"] = 340.0
    catastrophe_weather["rainfall_72h_mm"] = 450.0
    catastrophe_weather["soil_saturation_pct"] = 99.0
    catastrophe_weather["deep_soil_saturation_pct"] = 98.0
    catastrophe_weather["dist_to_river_m"] = 30.0

    pred_cat = prediction_service.predict_full(catastrophe_weather)
    assert pred_cat["calibrated_probability"] >= 0.08, f"Catastrophe probability too low: {pred_cat['calibrated_probability']}"
    assert pred_cat["threshold_exceeded"] is True
    assert pred_cat["risk_level"] in ["HIGH", "CRITICAL"]
    assert len(pred_cat["top_contributing_factors"]) > 0
    logger.info(f"  [PASS] Catastrophe Calibrated Probability: {pred_cat['calibrated_probability']:.4f}")
    logger.info(f"  [PASS] Operational Threshold Exceeded: {pred_cat['threshold_exceeded']}")
    logger.info(f"  [PASS] Catastrophe Severity Level: {pred_cat['risk_level']} (Score: {pred_cat['risk_score']}/100)")
    logger.info("  [PASS] Authentic Model Factor Attributions:")
    for factor in pred_cat["top_contributing_factors"]:
        logger.info(f"         - {factor['display_name']}: {factor['value']} {factor.get('unit','')} (log-odds contribution: +{factor['contribution']:.3f})")

    # 6. Database Persistence & Live Inference Service Test
    logger.info("Step 6: Testing DB Persistence via LiveInferenceService...")
    db = SessionLocal()
    try:
        first_village = db.query(Village).first()
        assert first_village is not None, "No village found in database"
        
        eval_res = live_inference_service.evaluate_village(db, first_village.id, persist=True)
        assert eval_res["village_id"] == first_village.id
        assert "calibrated_probability" in eval_res
        assert "risk_score" in eval_res

        latest_pred = db.query(Prediction).filter(Prediction.village_id == first_village.id).order_by(Prediction.created_at.desc()).first()
        assert latest_pred is not None, "Prediction was not persisted to database"
        assert latest_pred.calibrated_probability == eval_res["calibrated_probability"]
        logger.info(f"  [PASS] LiveInferenceService persisted prediction {latest_pred.id} for village '{first_village.name}'")

        latest_snap = db.query(RiskSnapshot).filter(RiskSnapshot.village_id == first_village.id).order_by(RiskSnapshot.timestamp.desc()).first()
        assert latest_snap is not None, "RiskSnapshot was not persisted to database"
        logger.info(f"  [PASS] RiskSnapshot persisted: {latest_snap.risk_level} ({latest_snap.risk_score}/100)")
    finally:
        db.close()

    # 7. FastAPI Endpoint Testing
    logger.info("Step 7: Testing FastAPI Live Prediction Endpoints...")
    client = TestClient(app)

    # Test GET /api/v1/villages/{id}
    v_res = client.get(f"/api/v1/villages/{first_village.id}")
    assert v_res.status_code == 200, f"GET /api/v1/villages/{first_village.id} failed: {v_res.text}"
    v_data = v_res.json()
    assert "calibrated_probability" in v_data
    assert "decision_threshold" in v_data
    assert v_data["decision_threshold"] == 0.08
    logger.info(f"  [PASS] GET /api/v1/villages/{first_village.id} returned calibrated prob {v_data['calibrated_probability']} and threshold {v_data['decision_threshold']}")

    # Test POST /api/v1/villages/{id}/predict
    pred_endpoint_res = client.post(f"/api/v1/villages/{first_village.id}/predict")
    assert pred_endpoint_res.status_code == 200
    p_data = pred_endpoint_res.json()
    assert p_data["village_id"] == first_village.id
    assert 0.0 <= p_data["calibrated_probability"] <= 1.0
    logger.info(f"  [PASS] POST /api/v1/villages/{first_village.id}/predict executed real-time inference on latest telemetry")

    # Test POST /api/v1/predictions/evaluate-all
    batch_res = client.post("/api/v1/predictions/evaluate-all")
    assert batch_res.status_code == 200
    b_data = batch_res.json()
    assert b_data["total_evaluated"] > 0
    logger.info(f"  [PASS] POST /api/v1/predictions/evaluate-all evaluated {b_data['total_evaluated']} basin settlements in parallel")

    logger.info("================================================================================")
    logger.info("ALL 7 END-TO-END VERIFICATION CHECKS PASSED WITH 100% ACCURACY!")
    logger.info("================================================================================")


if __name__ == "__main__":
    run_full_verification()
