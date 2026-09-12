"""
ml/src/models/predict.py
Flowshield — Real Baseline Inference & Explainable Risk Service (V2.5)
Smart India Hackathon 2026 (PS ID: 26192)

Loads the frozen V2 decision pipeline:
- Selected Model: Logistic Regression (highest composite safety score)
- Calibration: Isotonic Regression (calibrated on Pandoh & Dharampur)
- Operational Threshold: 0.08 (minimizes FNR, achieves >= 87.6% catastrophe recall)
- Data Quality Safety State: INSUFFICIENT_DATA when physical telemetry is corrupt or missing
- 5 Operational Risk Levels: LOW, WATCH, HIGH, CRITICAL, INSUFFICIENT_DATA
"""

import os
import json
import time
import numpy as np
import pandas as pd
import joblib
from typing import Dict, Any, List, Optional, Tuple

from ..features.feature_definitions import CANONICAL_FEATURE_NAMES, FEATURE_METADATA
from ..utils.paths import MLPaths
from ..utils.logger import get_logger
from .explain import ModelExplainer

logger = get_logger("flowshield.models.predict")

# Cached module instances
_MODEL = None
_CALIBRATOR = None
_PREPROCESSOR = None
_EXPLAINER = None
_PIPELINE_INFO = None


def load_inference_artifacts() -> Tuple[Any, Any, Any, Dict[str, Any]]:
    """Loads and caches production decision pipeline artifacts."""
    global _MODEL, _CALIBRATOR, _PREPROCESSOR, _EXPLAINER, _PIPELINE_INFO
    
    prod_dir = MLPaths.MODELS_PROD_DIR
    models_dir = MLPaths.MODELS_DIR
    
    # Check production directory first, then fallback to models/
    pipeline_path = prod_dir / "v2_decision_pipeline.json"
    if not pipeline_path.exists():
        pipeline_path = models_dir / "v2_decision_pipeline.json"

    if _PIPELINE_INFO is None:
        if pipeline_path.exists():
            with open(pipeline_path, "r") as f:
                _PIPELINE_INFO = json.load(f)
        else:
            _PIPELINE_INFO = {
                "pipeline_version": "flowshield-flood-risk-v2.5",
                "selected_model": "logistic_regression",
                "calibration_method": "isotonic",
                "threshold": 0.08,
                "model_artifact": "v2_selected_model.joblib",
                "calibrator_artifact": "v2_calibrator.joblib",
                "preprocessor_artifact": "v2_preprocessor.joblib",
            }

    if _MODEL is None:
        m_file = _PIPELINE_INFO.get("model_artifact", "v2_selected_model.joblib")
        m_path = prod_dir / m_file
        if not m_path.exists():
            m_path = models_dir / m_file
        if not m_path.exists():
            m_path = prod_dir / "flood_risk_champion.joblib"
        logger.info(f"Loading champion model from: {m_path}")
        _MODEL = joblib.load(m_path)

    if _CALIBRATOR is None:
        c_file = _PIPELINE_INFO.get("calibrator_artifact", "v2_calibrator.joblib")
        c_path = prod_dir / c_file
        if not c_path.exists():
            c_path = models_dir / c_file
        if not c_path.exists():
            c_path = prod_dir / "flood_risk_calibrator.joblib"
        logger.info(f"Loading calibrator from: {c_path}")
        _CALIBRATOR = joblib.load(c_path)

    if _PREPROCESSOR is None:
        p_file = _PIPELINE_INFO.get("preprocessor_artifact", "v2_preprocessor.joblib")
        p_path = prod_dir / p_file
        if not p_path.exists():
            p_path = models_dir / p_file
        if not p_path.exists():
            p_path = prod_dir / "flood_risk_preprocessor.joblib"
        logger.info(f"Loading preprocessor from: {p_path}")
        _PREPROCESSOR = joblib.load(p_path)

    if _EXPLAINER is None and _MODEL is not None:
        _EXPLAINER = ModelExplainer(_MODEL, _PREPROCESSOR)

    return _MODEL, _CALIBRATOR, _PREPROCESSOR, _PIPELINE_INFO


def get_explainer() -> Optional[ModelExplainer]:
    """Retrieves or instantiates cached explainer instance."""
    global _EXPLAINER
    if _EXPLAINER is None:
        load_inference_artifacts()
    return _EXPLAINER


def predict_flood_risk(
    features_dict: Dict[str, Any],
    generate_explanation: bool = True,
) -> Dict[str, Any]:
    """
    Executes the validated 15-feature V2 inference contract with isotonic calibration.
    """
    start_time = time.time()
    model, calibrator, preprocessor, pipeline_info = load_inference_artifacts()
    threshold = float(pipeline_info.get("threshold", 0.08))

    # 1. Physical validation & sanity checks
    missing_feats = []
    vector_vals = []
    for f in CANONICAL_FEATURE_NAMES:
        val = features_dict.get(f)
        if val is None:
            missing_feats.append(f)
            vector_vals.append(0.0)
        else:
            try:
                vector_vals.append(float(val))
            except (ValueError, TypeError):
                missing_feats.append(f)
                vector_vals.append(0.0)

    # If >20% of features missing, enter INSUFFICIENT_DATA safety state
    if len(missing_feats) > 3:
        return {
            "status": "INSUFFICIENT_DATA",
            "is_flood_likely": False,
            "raw_probability": 0.0,
            "calibrated_probability": 0.0,
            "decision_threshold": threshold,
            "risk_level": "INSUFFICIENT_DATA",
            "missing_features": missing_feats,
            "inference_latency_ms": round((time.time() - start_time) * 1000.0, 2),
            "top_drivers": [],
            "message": "Physical telemetry corrupted or incomplete.",
        }

    # 2. DataFrame assembly
    df_in = pd.DataFrame([vector_vals], columns=CANONICAL_FEATURE_NAMES)

    # 3. Transform & predict
    x_scaled = None
    if hasattr(model, "named_steps"):
        raw_prob = float(model.predict_proba(df_in)[0, 1])
    else:
        try:
            x_scaled = preprocessor.transform(df_in)
            raw_prob = float(model.predict_proba(x_scaled)[0, 1])
        except Exception as e:
            logger.warning(f"Preprocessing transform failed: {e}. Passing raw.")
            raw_prob = float(model.predict_proba(df_in.values)[0, 1]) if hasattr(model, "predict_proba") else 0.0

    # Calibrated probability
    if calibrator is not None:
        est = getattr(calibrator, "estimator", None)
        if hasattr(est, "estimator"):
            est = est.estimator
        if hasattr(est, "named_steps"):
            calibrated_prob = float(calibrator.predict_proba(df_in)[0, 1])
        else:
            if x_scaled is None:
                x_scaled = preprocessor.transform(df_in)
            calibrated_prob = float(calibrator.predict_proba(x_scaled)[0, 1])
    else:
        calibrated_prob = raw_prob

    # 4. Decision threshold evaluation
    is_flood = bool(calibrated_prob >= threshold)

    # 5. Risk Level Mapping
    if calibrated_prob < 0.08:
        risk_level = "LOW"
    elif calibrated_prob < 0.20:
        risk_level = "WATCH"
    elif calibrated_prob < 0.40:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    # 6. Authentic Explanation
    explanation_res = None
    top_drivers = []
    if generate_explanation:
        explainer = get_explainer()
        if explainer is not None:
            explanation_res = explainer.explain_prediction(
                features_dict=dict(zip(CANONICAL_FEATURE_NAMES, vector_vals)),
                calibrated_probability=calibrated_prob,
                top_k=4,
            )
            top_drivers = explanation_res.get("top_drivers", [])

    latency_ms = (time.time() - start_time) * 1000.0

    return {
        "status": "SUCCESS",
        "is_flood_likely": is_flood,
        "calibrated_probability": round(calibrated_prob, 4),
        "raw_probability": round(raw_prob, 4),
        "decision_threshold": threshold,
        "risk_level": risk_level,
        "inference_latency_ms": round(latency_ms, 2),
        "top_drivers": top_drivers,
        "explanation": explanation_res,
        "pipeline_version": pipeline_info.get("pipeline_version", "v2.5"),
    }
