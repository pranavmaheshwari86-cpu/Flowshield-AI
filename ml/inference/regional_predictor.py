"""
ml/inference/regional_predictor.py
Flowshield — Regional Flood Inference Engine

Provides real-time, explainable, calibrated flood predictions routed to the
scientifically appropriate regional model artifact for any of the 10 target regions.

Features:
- Automatic region resolution and validation
- Dynamic lazy loading and thread-safe caching via ModelRegistry
- Telemetry data quality guardrails with graceful physical degradation
- Authentic local feature attribution (SHAP / Linear log-odds) via ModelExplainer
- Multi-tier alert thresholds (Advisory, Watch, Warning)
- Backward-compatible schema with V2 Himachal Pradesh production interface
"""

import logging
import threading
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

from ml.registry.feature_contract import CANONICAL_FEATURES, PHYSICAL_BOUNDS
from ml.registry.model_registry import model_registry, RegionalModelBundle
from ml.registry.region_resolver import region_resolver, SUPPORTED_REGIONS
from ml.inference.explain import ModelExplainer

logger = logging.getLogger("flowshield.inference.regional")


def validate_regional_telemetry(input_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates physical feasibility of incoming telemetry for regional inference.
    """
    errors = []
    for feat, (lo, hi) in PHYSICAL_BOUNDS.items():
        val = input_data.get(feat)
        if val is not None:
            try:
                v = float(val)
                if np.isnan(v):
                    continue
                if v < lo or v > hi:
                    errors.append(f"{feat}={v} exceeds physical limits [{lo}, {hi}]")
            except (ValueError, TypeError):
                errors.append(f"{feat}={val} is not a valid numerical value")
    return len(errors) == 0, errors


def compute_topographic_factor(elevation_m: float, slope_deg: float, dist_to_river_m: float) -> float:
    """Computes normalized topographic flood susceptibility factor T in [0, 1]."""
    slope_norm = float(np.clip(slope_deg / 45.0, 0.0, 1.0))
    river_norm = float(np.clip(1.0 - (dist_to_river_m / 1000.0), 0.0, 1.0))
    T = (0.55 * river_norm) + (0.45 * slope_norm)
    return float(np.clip(T, 0.0, 1.0))


def compute_composite_risk(
    calibrated_prob: float,
    threshold: float,
    topographic_factor: float,
    vulnerability_index: float = 0.50,
    preparedness_factor: float = 0.50,
) -> Tuple[float, str]:
    """
    Computes composite operational flood risk score in [0, 100] and maps
    to severity tier: LOW, WATCH, HIGH, CRITICAL.
    """
    # Normalized hazard probability relative to operational threshold
    if calibrated_prob < threshold:
        norm_prob = (calibrated_prob / max(threshold, 0.01)) * 0.40
    else:
        excess = (calibrated_prob - threshold) / max(1.0 - threshold, 0.01)
        norm_prob = 0.40 + (excess * 0.60)
    norm_prob = float(np.clip(norm_prob, 0.0, 1.0))

    # Weighting: Hazard=50%, Topography=25%, Vulnerability=15%, Lack of Preparedness=10%
    risk_score = (
        (norm_prob * 50.0)
        + (topographic_factor * 25.0)
        + (vulnerability_index * 15.0)
        + ((1.0 - preparedness_factor) * 10.0)
    )
    risk_score = round(float(np.clip(risk_score, 0.0, 100.0)), 2)

    # Operational severity tier
    if calibrated_prob >= 0.70 or risk_score >= 75.0:
        level = "CRITICAL"
    elif calibrated_prob >= threshold or risk_score >= 50.0:
        level = "HIGH"
    elif calibrated_prob >= (threshold * 0.5) or risk_score >= 30.0:
        level = "WATCH"
    else:
        level = "LOW"

    return risk_score, level


class RegionalFloodPredictor:
    """
    Thread-safe regional flood risk prediction service.
    """

    def __init__(self):
        self._explainers: Dict[str, ModelExplainer] = {}
        self._lock = threading.Lock()

    def _get_explainer(self, region_slug: str, bundle: RegionalModelBundle) -> ModelExplainer:
        with self._lock:
            if region_slug not in self._explainers:
                self._explainers[region_slug] = ModelExplainer(
                    model=bundle.model,
                    preprocessor=bundle.preprocessor,
                )
            return self._explainers[region_slug]

    def predict(
        self,
        region_slug: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes calibrated prediction for a specific region.
        """
        data = input_data or {}
        slug = region_slug or "himachal_pradesh"

        # Validate region
        if not region_resolver.is_valid_region(slug):
            return {
                "error": f"Unsupported region '{slug}'. Supported regions: {SUPPORTED_REGIONS}",
                "status": "invalid_region",
                "risk_level": "UNKNOWN",
                "flood_probability": 0.0,
            }

        region_display = region_resolver.get_display_name(slug)

        # 1. Telemetry Verification
        is_valid, quality_errors = validate_regional_telemetry(data)
        if not is_valid:
            logger.warning(f"Regional telemetry validation failed for {slug}: {quality_errors}")
            return {
                "region": slug,
                "region_display_name": region_display,
                "raw_probability": 0.0,
                "calibrated_probability": 0.0,
                "flood_probability": 0.0,
                "confidence": 0.0,
                "threshold": 0.08,
                "threshold_exceeded": False,
                "top_contributing_factors": [],
                "explanation": [f"Data quality safety guardrail tripped: {err}" for err in quality_errors],
                "status": "insufficient_data",
                "risk_score": 0.0,
                "risk_level": "INSUFFICIENT_DATA",
            }

        # 2. Retrieve Regional Model Bundle
        try:
            bundle = model_registry.get(hazard="flood", region=slug)
        except Exception as e:
            logger.error(f"Failed to load model bundle for region '{slug}': {e}")
            return {
                "region": slug,
                "region_display_name": region_display,
                "error": f"Model artifact unavailable for region '{slug}': {e}",
                "status": "model_unavailable",
                "risk_level": "UNKNOWN",
                "flood_probability": 0.0,
            }

        # 3. Construct Canonical Feature Matrix
        feature_row = {}
        for feat in CANONICAL_FEATURES:
            val = data.get(feat)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                val = np.nan
            else:
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    val = np.nan
            feature_row[feat] = val

        df_single = pd.DataFrame(
            [[feature_row[f] for f in CANONICAL_FEATURES]],
            columns=CANONICAL_FEATURES,
        )

        # 4. Predict Raw and Calibrated Probabilities
        threshold = bundle.threshold
        X_scaled = None

        if hasattr(bundle.model, "named_steps"):
            raw_prob = float(bundle.model.predict_proba(df_single)[0, 1])
        else:
            X_scaled = bundle.preprocessor.transform(df_single)
            raw_prob = float(bundle.model.predict_proba(X_scaled)[0, 1])
        raw_prob = float(np.clip(raw_prob, 0.0, 1.0))

        if bundle.calibrator is not None:
            est = getattr(bundle.calibrator, "estimator", None)
            if hasattr(est, "estimator"):
                est = est.estimator
            if hasattr(est, "named_steps"):
                calibrated_prob = float(bundle.calibrator.predict_proba(df_single)[0, 1])
            else:
                if X_scaled is None:
                    X_scaled = bundle.preprocessor.transform(df_single)
                calibrated_prob = float(bundle.calibrator.predict_proba(X_scaled)[0, 1])
        else:
            calibrated_prob = raw_prob
        calibrated_prob = float(np.clip(calibrated_prob, 0.0, 1.0))

        threshold_exceeded = bool(calibrated_prob >= threshold)

        # 5. Model Explainability
        explainer = self._get_explainer(slug, bundle)
        top_factors = explainer.explain_prediction(feature_row, calibrated_prob, top_k=4)

        # 6. Topographic and Composite Risk
        elev = feature_row.get("elevation_m", 1000.0) or 1000.0
        slope = feature_row.get("catchment_slope_deg", 20.0) or 20.0
        dist = feature_row.get("dist_to_river_m", 100.0) or 100.0
        T = compute_topographic_factor(elev, slope, dist)
        V = float(np.clip(data.get("vulnerability_index", 0.50), 0.0, 1.0))
        P = float(np.clip(data.get("preparedness_factor", 0.50), 0.0, 1.0))

        risk_score, risk_level = compute_composite_risk(
            calibrated_prob=calibrated_prob,
            threshold=threshold,
            topographic_factor=T,
            vulnerability_index=V,
            preparedness_factor=P,
        )

        # 7. Statistical Classification Certainty (Max Calibrated Posterior Probability)
        confidence = float(np.clip(max(calibrated_prob, 1.0 - calibrated_prob), 0.50, 1.0))

        return {
            "region": slug,
            "region_display_name": region_display,
            "raw_probability": round(raw_prob, 4),
            "calibrated_probability": round(calibrated_prob, 4),
            "flood_probability": round(calibrated_prob, 4),
            "threshold": round(threshold, 4),
            "decision_threshold": round(threshold, 4),
            "threshold_exceeded": threshold_exceeded,
            "multi_tier_thresholds": bundle.thresholds,
            "confidence": round(confidence, 4),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "model_version": bundle.model_version,
            "model_family": type(bundle.model).__name__,
            "production_status": bundle.production_status,
            "calibration_method": bundle.calibration_method,
            "top_contributing_factors": top_factors,
            "explanation": [f["explanation"] for f in top_factors if "explanation" in f],
            "status": "operational_regional_validated",
        }


# Module-level singleton
regional_predictor = RegionalFloodPredictor()
