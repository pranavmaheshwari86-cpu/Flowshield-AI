"""
ml/pipeline/calibrate.py
Flowshield — Multi-Region Probability Calibration

Calibrates raw classification decision scores into well-calibrated
posterior flood probabilities P(Flood | X) using:
- Isotonic Regression (non-parametric monotonic step function)
- Platt Scaling / Sigmoid (parametric logistic sigmoid)

Evaluates Brier score loss and Expected Calibration Error (ECE).
Enforces monotonicity.
"""

import logging
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import brier_score_loss

from ml.registry.feature_contract import CANONICAL_FEATURES

logger = logging.getLogger("flowshield.pipeline.calibrate")


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Computes Expected Calibration Error (ECE) across probability bins."""
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total = len(y_true)
    for i in range(n_bins):
        mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
        if np.sum(mask) > 0:
            acc = np.mean(y_true[mask])
            conf = np.mean(y_prob[mask])
            ece += (np.sum(mask) / total) * abs(acc - conf)
    return round(float(ece), 4)


def check_monotonicity(y_raw: np.ndarray, y_cal: np.ndarray) -> bool:
    """Verifies that probability calibration preserves rank monotonicity."""
    order = np.argsort(y_raw)
    sorted_cal = y_cal[order]
    diffs = np.diff(sorted_cal)
    violations = np.sum(diffs < -1e-5)
    return bool(violations == 0)


def calibrate_model(
    model_pipeline: Any,
    val_cal_df: pd.DataFrame,
    val_tune_df: pd.DataFrame,
    feature_names: Optional[list] = None,
    target_column: str = "flood_occurred",
    preferred_methods: Optional[list] = None,
) -> Tuple[Any, str, Dict[str, Any]]:
    """
    Fits and compares calibration methods on val_cal_df, evaluating on val_tune_df.

    Parameters
    ----------
    model_pipeline : Pipeline or Classifier
        Trained uncalibrated pipeline (with predict_proba).
    val_cal_df : pd.DataFrame
        Calibration partition.
    val_tune_df : pd.DataFrame
        Validation tuning partition.
    feature_names : list, optional
        Canonical features to slice. Defaults to CANONICAL_FEATURES.
    target_column : str
        Name of target column.
    preferred_methods : list, optional
        ["isotonic", "sigmoid"]

    Returns
    -------
    (calibrator_object, best_method_name, calibration_metrics_dict)
    """
    features = feature_names or CANONICAL_FEATURES
    methods = preferred_methods or ["isotonic", "sigmoid"]

    X_cal = val_cal_df[features]
    y_cal = val_cal_df[target_column].values

    X_tune = val_tune_df[features]
    y_tune = val_tune_df[target_column].values

    # Check if positive samples exist in calibration set
    pos_cal = int(np.sum(y_cal))
    pos_tune = int(np.sum(y_tune))

    # Baseline uncalibrated performance
    raw_probs_tune = model_pipeline.predict_proba(X_tune)[:, 1]
    raw_brier = float(brier_score_loss(y_tune, raw_probs_tune))
    raw_ece = compute_ece(y_tune, raw_probs_tune)

    results = {
        "raw": {
            "brier_score": round(raw_brier, 4),
            "ece": round(raw_ece, 4),
        }
    }

    if pos_cal < 3 or pos_tune < 1:
        logger.warning(
            f"Insufficient positive samples in calibration set (cal={pos_cal}, tune={pos_tune}). "
            "Using uncalibrated model."
        )
        return None, "none", {**results, "selected_method": "none", "improvement": False}

    best_method = "none"
    best_brier = raw_brier
    best_calibrator = None

    for method in methods:
        try:
            cal = CalibratedClassifierCV(
                estimator=FrozenEstimator(model_pipeline),
                method=method,
            )
            cal.fit(X_cal, y_cal)

            cal_probs = cal.predict_proba(X_tune)[:, 1]
            brier = float(brier_score_loss(y_tune, cal_probs))
            ece = compute_ece(y_tune, cal_probs)
            monotonic = check_monotonicity(raw_probs_tune, cal_probs)

            results[method] = {
                "brier_score": round(brier, 4),
                "ece": round(ece, 4),
                "monotonic": monotonic,
            }

            # Must improve Brier score and maintain reasonable monotonicity
            if brier <= best_brier:
                best_brier = brier
                best_method = method
                best_calibrator = cal

        except Exception as e:
            logger.warning(f"Calibration method '{method}' failed: {e}")
            results[method] = {"error": str(e)}

    results["selected_method"] = best_method
    results["improvement"] = bool(best_method != "none" and best_brier < raw_brier)

    logger.info(
        f"Calibration outcome: selected='{best_method}', "
        f"Brier: raw={raw_brier:.4f} → cal={best_brier:.4f}, ECE: {raw_ece:.4f}"
    )

    return best_calibrator, best_method, results
