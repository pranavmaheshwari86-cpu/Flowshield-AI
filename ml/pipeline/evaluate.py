"""
ml/pipeline/evaluate.py
Flowshield — Multi-Region Model Evaluation Engine

Generates rigorous evaluation reports on untouched holdout partitions:
- Discriminative power: ROC-AUC, PR-AUC (Average Precision)
- Disaster metrics: Recall, Precision, F1, Macro-F1, False Negative Rate (FNR)
- Probabilistic quality: Brier score loss, Expected Calibration Error (ECE)
- Confusion matrix and absolute counts
- Production readiness gatekeeper
"""

import logging
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
)

from ml.registry.feature_contract import CANONICAL_FEATURES
from ml.pipeline.calibrate import compute_ece

logger = logging.getLogger("flowshield.pipeline.evaluate")


def evaluate_model_holdout(
    model_or_calibrator: Any,
    holdout_df: pd.DataFrame,
    thresholds: Dict[str, Any],
    region_slug: str,
    model_name: str = "champion_model",
    feature_names: Optional[List[str]] = None,
    target_column: str = "flood_occurred",
) -> Dict[str, Any]:
    """
    Evaluates a trained & calibrated model on the untouched holdout dataset.

    Parameters
    ----------
    model_or_calibrator : Any
        Predictor object with predict_proba.
    holdout_df : pd.DataFrame
        Untouched holdout dataset.
    thresholds : dict
        Dict containing 'selected_threshold', 'advisory_threshold', etc.
    region_slug : str
        Slug of the evaluated region.
    model_name : str
        Algorithm name (e.g. 'xgboost', 'logistic_regression').

    Returns
    -------
    dict : Full evaluation report with production gate status.
    """
    features = feature_names or CANONICAL_FEATURES
    X_holdout = holdout_df[features]
    y_true = holdout_df[target_column].values

    probabilities = model_or_calibrator.predict_proba(X_holdout)[:, 1]
    tau = float(thresholds.get("selected_threshold", 0.08))
    y_pred = (probabilities >= tau).astype(int)

    total_samples = len(y_true)
    actual_positives = int(np.sum(y_true))
    actual_negatives = total_samples - actual_positives

    # Basic metrics
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    # Curve metrics (requires at least one positive and one negative)
    has_both_classes = (actual_positives > 0) and (actual_negatives > 0)
    roc_auc = float(roc_auc_score(y_true, probabilities)) if has_both_classes else None
    pr_auc = float(average_precision_score(y_true, probabilities)) if has_both_classes else None
    brier = float(brier_score_loss(y_true, probabilities))
    ece = compute_ece(y_true, probabilities)

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    fnr = float(fn / (tp + fn)) if (tp + fn) > 0 else 0.0
    fpr = float(fp / (tn + fp)) if (tn + fp) > 0 else 0.0

    # Multi-tier alert evaluations
    alert_breakdown = {}
    for tier_key in ["advisory_threshold", "watch_threshold", "warning_threshold"]:
        if tier_key in thresholds:
            t_val = float(thresholds[tier_key])
            t_pred = (probabilities >= t_val).astype(int)
            alert_breakdown[tier_key] = {
                "threshold": t_val,
                "recall": round(float(recall_score(y_true, t_pred, zero_division=0)), 4),
                "precision": round(float(precision_score(y_true, t_pred, zero_division=0)), 4),
                "predicted_alerts": int(np.sum(t_pred)),
            }

    # Production gate determination
    # Rules:
    # 1. actual_positives >= 5 AND recall >= 0.70 AND roc_auc >= 0.75 -> PRODUCTION_READY
    # 2. actual_positives >= 1 -> VALIDATION_ONLY
    # 3. actual_positives == 0 -> DATA_INSUFFICIENT
    if actual_positives == 0:
        production_status = "DATA_INSUFFICIENT"
        status_reason = "No positive flood events occurred in holdout period."
    elif roc_auc is not None and roc_auc >= 0.75 and rec >= 0.70:
        production_status = "PRODUCTION_READY"
        status_reason = "Model passed holdout discrimination, recall, and calibration gates."
    else:
        production_status = "VALIDATION_ONLY"
        status_reason = f"Holdout metrics below strict production bar (Recall={rec:.2f}, ROC-AUC={roc_auc})."

    report = {
        "region": region_slug,
        "model_architecture": model_name,
        "production_status": production_status,
        "status_reason": status_reason,
        "threshold_used": tau,
        "holdout_sample_count": total_samples,
        "actual_floods_count": actual_positives,
        "missed_floods_count": int(fn),
        "detected_floods_count": int(tp),
        "false_alarms_count": int(fp),
        "metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "macro_f1": round(macro_f1, 4),
            "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
            "pr_auc": round(pr_auc, 4) if pr_auc is not None else None,
            "brier_score": round(brier, 4),
            "expected_calibration_error": round(ece, 4),
            "false_negative_rate": round(fnr, 4),
            "false_positive_rate": round(fpr, 4),
        },
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "multi_tier_alert_performance": alert_breakdown,
    }

    logger.info(
        f"Evaluation [{region_slug}]: Status={production_status}, "
        f"Recall={rec:.4f}, ROC-AUC={roc_auc}, F1={f1:.4f}, Brier={brier:.4f}"
    )

    return report
