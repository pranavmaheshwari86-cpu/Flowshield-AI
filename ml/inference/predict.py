"""
ml/inference/predict.py
Flowshield — Real Baseline Inference & Explainable Risk Service (V2)
Smart India Hackathon 2026 (PS ID: 26192)

Loads the frozen V2 decision pipeline:
- Selected Model: Logistic Regression (highest composite safety score on spatial holdout)
- Calibration: Isotonic Regression (Platt scaling / Isotonic calibrated on Pandoh & Dharampur)
- Operational Threshold: 0.08 (minimizes FNR, achieves >= 88.4% catastrophe recall)
- Data Quality Safety State: INSUFFICIENT_DATA when physical telemetry is corrupt or missing
- 5 Operational Risk Levels: LOW, WATCH, HIGH, CRITICAL, INSUFFICIENT_DATA
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
import joblib
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("flowshield.inference.predict")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES, FEATURE_METADATA
from ml.inference.explain import ModelExplainer

MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")
V2_PIPELINE_PATH = os.path.join(MODELS_DIR, "v2_decision_pipeline.json")

# Module-level cached instances
_MODEL = None
_CALIBRATOR = None
_PREPROCESSOR = None
_EXPLAINER = None
_PIPELINE_INFO = None
_SCHEMA = None


def load_inference_artifacts() -> Tuple[Any, Any, Any, Dict[str, Any]]:
    """
    Loads and caches the V2 decision pipeline artifacts:
    - Base trained model
    - Probability calibrator (Isotonic / Platt)
    - StandardScaler preprocessor
    - Decision pipeline manifest (threshold, operational metrics)
    """
    global _MODEL, _CALIBRATOR, _PREPROCESSOR, _EXPLAINER, _PIPELINE_INFO, _SCHEMA
    
    if _PIPELINE_INFO is None:
        if os.path.exists(V2_PIPELINE_PATH):
            with open(V2_PIPELINE_PATH, "r") as f:
                _PIPELINE_INFO = json.load(f)
        else:
            _PIPELINE_INFO = {
                "pipeline_version": "flowshield-flood-risk-v2",
                "selected_model": "logistic_regression",
                "calibration_method": "isotonic",
                "threshold": 0.08,
                "model_artifact": "v2_selected_model.joblib",
                "calibrator_artifact": "v2_calibrator.joblib",
                "preprocessor_artifact": "v2_preprocessor.joblib",
            }
            
    if _PREPROCESSOR is None:
        prep_file = _PIPELINE_INFO.get("preprocessor_artifact", "v2_preprocessor.joblib")
        prep_path = os.path.join(MODELS_DIR, prep_file)
        if not os.path.exists(prep_path):
            prep_path = os.path.join(MODELS_DIR, "preprocessor.joblib")
        if not os.path.exists(prep_path):
            raise FileNotFoundError(f"Preprocessor not found at {prep_path}")
        _PREPROCESSOR = joblib.load(prep_path)
        
    if _MODEL is None:
        model_file = _PIPELINE_INFO.get("model_artifact", "v2_selected_model.joblib")
        model_path = os.path.join(MODELS_DIR, model_file)
        if not os.path.exists(model_path):
            model_path = os.path.join(MODELS_DIR, "lr_real_flood_model.joblib")
        if not os.path.exists(model_path):
            model_path = os.path.join(MODELS_DIR, "xgb_real_flood_model.joblib")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model artifact not found at {model_path}")
        _MODEL = joblib.load(model_path)
        
    if _CALIBRATOR is None:
        calib_file = _PIPELINE_INFO.get("calibrator_artifact")
        if calib_file:
            calib_path = os.path.join(MODELS_DIR, calib_file)
            if os.path.exists(calib_path):
                _CALIBRATOR = joblib.load(calib_path)

    if _EXPLAINER is None and _MODEL is not None:
        _EXPLAINER = ModelExplainer(model=_MODEL, preprocessor=_PREPROCESSOR)

    return _MODEL, _CALIBRATOR, _PREPROCESSOR, _PIPELINE_INFO


def get_explainer() -> ModelExplainer:
    """Returns the cached authentic ModelExplainer instance."""
    global _EXPLAINER
    if _EXPLAINER is None:
        load_inference_artifacts()
    return _EXPLAINER


def compute_topographic_factor(elevation_m: float, slope_deg: float, dist_to_river_m: float) -> float:
    """Computes normalized topographic susceptibility T in [0, 1]."""
    slope_norm = min(1.0, max(0.0, slope_deg / 45.0))
    river_norm = max(0.0, 1.0 - (dist_to_river_m / 500.0))
    elev_norm = max(0.0, 1.0 - (elevation_m / 2500.0))
    return float(np.clip(0.40 * slope_norm + 0.40 * river_norm + 0.20 * elev_norm, 0.0, 1.0))


def validate_physical_telemetry(input_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates physical feasibility of input features.
    Guards against NaN, corruption, or physically impossible readings.
    """
    errors = []
    
    if input_data.get("insufficient_data") is True:
        return False, ["Explicit insufficient_data flag requested by client or upstream feeder."]
        
    # Check physical ranges if provided
    ranges = {
        "rainfall_1h_mm": (0.0, 1000.0),
        "rainfall_3h_mm": (0.0, 1500.0),
        "rainfall_6h_mm": (0.0, 2000.0),
        "rainfall_24h_mm": (0.0, 3000.0),
        "rainfall_72h_mm": (0.0, 5000.0),
        "soil_saturation_pct": (0.0, 100.0),
        "deep_soil_saturation_pct": (0.0, 100.0),
        "temperature_c": (-50.0, 60.0),
        "relative_humidity_pct": (0.0, 100.0),
        "surface_pressure_hpa": (500.0, 1100.0),
        "wind_speed_kmh": (0.0, 300.0),
        "elevation_m": (0.0, 9000.0),
        "catchment_slope_deg": (0.0, 90.0),
        "dist_to_river_m": (0.0, 100000.0),
    }
    
    for feat, (min_v, max_v) in ranges.items():
        if feat in input_data and input_data[feat] is not None:
            val = input_data[feat]
            try:
                val_f = float(val)
                if np.isnan(val_f) or np.isinf(val_f):
                    errors.append(f"Feature '{feat}' contains NaN or infinite value.")
                elif val_f < min_v or val_f > max_v:
                    errors.append(f"Feature '{feat}' value {val_f} is outside physical range [{min_v}, {max_v}].")
            except (ValueError, TypeError):
                errors.append(f"Feature '{feat}' cannot be parsed as a float.")
                
    if errors:
        return False, errors
    return True, []


def compute_composite_risk(
    calibrated_prob: float,
    threshold: float,
    topographic_factor: float,
    vulnerability_index: float = 0.50,
    preparedness_factor: float = 0.50,
) -> Tuple[float, str]:
    """
    @deprecated: Operational disaster policy scoring is formally delegated to
    apps.api.app.services.risk_engine:RiskEngine. This function is maintained
    strictly as a compatibility bridge for standalone ML testing.
    """
    if calibrated_prob < threshold:
        prob_hazard_ratio = (calibrated_prob / max(1e-4, threshold)) * 0.50
    else:
        prob_hazard_ratio = 0.50 + 0.50 * ((calibrated_prob - threshold) / max(1e-4, 1.0 - threshold))
    prob_hazard_ratio = float(np.clip(prob_hazard_ratio, 0.0, 1.0))
    
    raw_risk = (
        (0.45 * prob_hazard_ratio)
        + (0.25 * topographic_factor)
        + (0.20 * vulnerability_index)
        - (0.05 * preparedness_factor)
        + (0.15 * prob_hazard_ratio * topographic_factor)
    )
    risk_score = float(np.clip(raw_risk * 100.0, 0.0, 100.0))
    
    if calibrated_prob >= 0.50 or risk_score >= 75.0:
        risk_level = "CRITICAL"
    elif calibrated_prob >= threshold or risk_score >= 50.0:
        risk_level = "HIGH"
    elif (calibrated_prob >= threshold * 0.5) or risk_score >= 25.0:
        risk_level = "WATCH"
    else:
        risk_level = "LOW"
        
    return risk_score, risk_level


def predict_flood_risk_regional(region: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Routes flood prediction to the designated regional model bundle.
    """
    from ml.inference.regional_predictor import regional_predictor
    return regional_predictor.predict(region_slug=region, input_data=input_data)


def predict_flood_risk(input_data: Dict[str, Any], region: Optional[str] = None) -> Dict[str, Any]:
    """
    Evaluates physical features under the scientifically verified Flowshield V2 pipeline.
    """
    # If a specific region is requested, route to regional predictor
    target_region = region or input_data.get("region")
    if target_region:
        from ml.registry.region_resolver import region_resolver
        if not region_resolver.is_valid_region(target_region):
            raise ValueError(f"UNSUPPORTED_REGION: '{target_region}' is not a valid or supported Flowshield region.")
        if target_region != "himachal_pradesh":
            return predict_flood_risk_regional(target_region, input_data)

    model, calibrator, preprocessor, pipeline_info = load_inference_artifacts()
    explainer = get_explainer()
    
    threshold = float(pipeline_info.get("threshold", 0.08))
    calibration_method = pipeline_info.get("calibration_method", "isotonic")
    model_version = pipeline_info.get("pipeline_version", "flowshield-flood-risk-v2")
    selected_model_name = pipeline_info.get("selected_model", "logistic_regression")
    
    model_display_names = {
        "logistic_regression": "Calibrated Logistic Regression (Isotonic scaling on ERA5-Land)",
        "random_forest": "Calibrated Random Forest (Isotonic scaling on ERA5-Land)",
        "xgboost": "Calibrated XGBoost (Isotonic scaling on ERA5-Land)",
    }
    model_type = model_display_names.get(selected_model_name, f"Calibrated {selected_model_name}")

    # 1. Telemetry Data Quality Verification
    is_valid, quality_errors = validate_physical_telemetry(input_data)
    if not is_valid:
        return {
            "raw_probability": 0.0,
            "calibrated_probability": 0.0,
            "flood_probability": 0.0,
            "confidence": 0.0,
            "threshold": threshold,
            "decision_threshold": threshold,
            "threshold_exceeded": False,
            "calibration_method": calibration_method,
            "model_version": model_version,
            "model_type": model_type,
            "top_contributing_factors": [],
            "explanation": [f"Data quality safety guardrail tripped: {err}" for err in quality_errors],
            "physical_explanations": [f"Data quality safety guardrail tripped: {err}" for err in quality_errors],
            "status": "insufficient_data",
            "region": "himachal_pradesh",
            "region_display_name": "Himachal Pradesh",
            "topographic_factor": 0.0,
            "risk_score": 0.0,
            "risk_level": "INSUFFICIENT_DATA",
        }

    # 2. Build Canonical Feature Vector
    feature_row = {}
    for feat in CANONICAL_FEATURE_NAMES:
        val = input_data.get(feat)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            val = np.nan
        else:
            try:
                val = float(val)
            except (ValueError, TypeError):
                val = np.nan
        feature_row[feat] = val
        
    df_single = pd.DataFrame([[feature_row[f] for f in CANONICAL_FEATURE_NAMES]], columns=CANONICAL_FEATURE_NAMES)
    
    # 3. Model Raw & Calibrated Inference
    X_scaled = None
    if hasattr(model, "named_steps"):
        raw_prob = float(model.predict_proba(df_single)[0, 1])
    else:
        X_scaled = preprocessor.transform(df_single)
        raw_prob = float(model.predict_proba(X_scaled)[0, 1])
    raw_prob = float(np.clip(raw_prob, 0.0, 1.0))

    if calibrator is not None:
        est = getattr(calibrator, "estimator", None)
        if hasattr(est, "estimator"):
            est = est.estimator
        if hasattr(est, "named_steps"):
            calibrated_prob = float(calibrator.predict_proba(df_single)[0, 1])
        else:
            if X_scaled is None:
                X_scaled = preprocessor.transform(df_single)
            calibrated_prob = float(calibrator.predict_proba(X_scaled)[0, 1])
    else:
        calibrated_prob = raw_prob
        
    calibrated_prob = float(np.clip(calibrated_prob, 0.0, 1.0))
    threshold_exceeded = bool(calibrated_prob >= threshold)
    
    # 4. Authentic Feature Attributions via ModelExplainer
    top_factors = explainer.explain_prediction(feature_row, calibrated_prob, top_k=4)
    
    # 5. Topographic Factor
    elev = feature_row.get("elevation_m", 1000.0)
    slope = feature_row.get("catchment_slope_deg", 25.0)
    dist = feature_row.get("dist_to_river_m", 100.0)
    T = compute_topographic_factor(elev, slope, dist)
    V = float(np.clip(input_data.get("vulnerability_index", 0.50), 0.0, 1.0))
    P = float(np.clip(input_data.get("preparedness_factor", 0.50), 0.0, 1.0))
    
    # 6. Operational Risk Score Bridge (Backward Compatibility)
    risk_score, risk_level = compute_composite_risk(
        calibrated_prob=calibrated_prob,
        threshold=threshold,
        topographic_factor=T,
        vulnerability_index=V,
        preparedness_factor=P,
    )
        
    # 7. Statistical Classification Certainty (Max Calibrated Posterior Probability)
    # Grounded in Platt/Isotonic calibrated probability, eliminating arbitrary threshold-distance scaling
    confidence = float(np.clip(max(calibrated_prob, 1.0 - calibrated_prob), 0.50, 1.0))
    
    # 8. Physical Factor Attributions / Explanations
    explanations = []
    if threshold_exceeded:
        explanations.append(
            f"Calibrated flood probability ({calibrated_prob*100:.1f}%) exceeds operational threshold ({threshold*100:.1f}%)."
        )
    for factor in top_factors:
        if factor.get("direction") == "increases_risk":
            feat_name = factor.get("feature_name", factor.get("feature", ""))
            disp = factor.get("display_name", feat_name)
            val = factor.get("value", 0.0)
            unit = factor.get("unit", "")
            contrib = factor.get("contribution", 0.0)
            pct = factor.get("percentage_impact", 0.0)
            explanations.append(f"{disp} ({val} {unit}) adds +{contrib:.3f} log-odds margin ({pct:.0f}% factor weight).")
            
    if not explanations:
        explanations.append("Hydrological and meteorological parameters currently within baseline seasonal range.")
        
    return {
        "raw_probability": round(raw_prob, 4),
        "calibrated_probability": round(calibrated_prob, 4),
        "flood_probability": round(calibrated_prob, 4),
        "threshold": round(threshold, 4),
        "decision_threshold": round(threshold, 4),
        "threshold_exceeded": threshold_exceeded,
        "confidence": round(confidence, 2),
        "top_contributing_factors": top_factors,
        "explanation": explanations,
        "physical_explanations": explanations,
        "calibration_method": calibration_method,
        "model_version": model_version,
        "model_type": model_type,
        "status": "operational_v2_validated",
        "region": "himachal_pradesh",
        "region_display_name": "Himachal Pradesh",
        "topographic_factor": round(T, 3),
        "risk_score": round(risk_score, 1),
        "risk_level": risk_level,
    }


if __name__ == "__main__":
    print("Testing Flowshield V2 ML inference pipeline...")
    sample_hazard = {
        "rainfall_1h_mm": 45.0,
        "rainfall_3h_mm": 98.0,
        "rainfall_6h_mm": 140.0,
        "rainfall_24h_mm": 210.0,
        "rainfall_72h_mm": 320.0,
        "soil_saturation_pct": 88.5,
        "deep_soil_saturation_pct": 82.0,
        "temperature_c": 18.2,
        "relative_humidity_pct": 98.0,
        "surface_pressure_hpa": 915.0,
        "wind_speed_kmh": 32.0,
        "elevation_m": 760.0,
        "catchment_slope_deg": 28.0,
        "dist_to_river_m": 45.0,
        "upstream_drainage_sqkm": 8900.0,
        "vulnerability_index": 0.75,
    }
    res = predict_flood_risk(sample_hazard)
    print("\nHigh-hazard scenario output:")
    print(json.dumps(res, indent=2))
    
    # Test INSUFFICIENT_DATA guardrail
    invalid_sample = {
        "rainfall_1h_mm": -25.0, # Impossible negative rainfall
        "soil_saturation_pct": 150.0 # Impossible > 100%
    }
    res_invalid = predict_flood_risk(invalid_sample)
    print("\nCorrupted telemetry scenario (Safety Guardrail):")
    print(json.dumps(res_invalid, indent=2))
