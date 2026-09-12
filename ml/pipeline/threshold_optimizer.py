"""
ml/pipeline/threshold_optimizer.py
Flowshield — Multi-Region Decision Threshold Optimization

Sweeps classification thresholds to optimize disaster-response trade-offs:
- Primary objective: Disaster Recall >= recall_bar (default 0.85, §64)
- Secondary objective: Minimize False Positive Rate (FPR <= 0.15) / Maximize F1
- Multi-tier operational thresholds:
    * Advisory (Early Watch): 95% Recall
    * Watch (Standard Alert): 85% Recall (Selected operational threshold)
    * Warning (Urgent Evacuation): High Precision / Lower FPR
"""

import logging
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

from ml.registry.feature_contract import CANONICAL_FEATURES

logger = logging.getLogger("flowshield.pipeline.threshold_optimizer")


def optimize_threshold(
    model_or_calibrator: Any,
    val_tune_df: pd.DataFrame,
    recall_bar: float = 0.85,
    fpr_bar: float = 0.15,
    feature_names: Optional[List[str]] = None,
    target_column: str = "flood_occurred",
    grid_size: int = 100,
) -> Dict[str, Any]:
    """
    Sweeps thresholds on val_tune_df to find optimal operational alert cutoffs.

    Parameters
    ----------
    model_or_calibrator : Any
        Fitted model or calibrator with predict_proba.
    val_tune_df : pd.DataFrame
        Validation tuning dataset.
    recall_bar : float
        Mandatory minimum recall target (e.g. 0.85).
    fpr_bar : float
        Maximum permissible false positive rate (e.g. 0.15).
    feature_names : list, optional
        Features to feed model. Defaults to CANONICAL_FEATURES.

    Returns
    -------
    dict containing:
        - selected_threshold
        - multi_tier_thresholds (advisory, watch, warning)
        - metrics_at_threshold
        - sweep_curve_summary
    """
    features = feature_names or CANONICAL_FEATURES
    X_tune = val_tune_df[features]
    y_tune = val_tune_df[target_column].values

    probabilities = model_or_calibrator.predict_proba(X_tune)[:, 1]

    # Grid of candidate thresholds
    thresholds = np.linspace(0.01, 0.95, grid_size)
    candidates = []

    total_positives = int(np.sum(y_tune))
    total_negatives = len(y_tune) - total_positives

    if total_positives == 0:
        logger.warning("Zero positive flood events in val_tune. Defaulting threshold to 0.10.")
        return {
            "selected_threshold": 0.10,
            "advisory_threshold": 0.05,
            "watch_threshold": 0.10,
            "warning_threshold": 0.20,
            "recall_at_threshold": 0.0,
            "precision_at_threshold": 0.0,
            "fpr_at_threshold": 0.0,
            "recall_bar_met": False,
        }

    for tau in thresholds:
        y_pred = (probabilities >= tau).astype(int)
        rec = recall_score(y_tune, y_pred, zero_division=0)
        prec = precision_score(y_tune, y_pred, zero_division=0)
        f1 = f1_score(y_tune, y_pred, zero_division=0)

        cm = confusion_matrix(y_tune, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        fpr = fp / total_negatives if total_negatives > 0 else 0.0
        fnr = fn / total_positives if total_positives > 0 else 0.0

        candidates.append({
            "threshold": round(float(tau), 4),
            "recall": round(float(rec), 4),
            "precision": round(float(prec), 4),
            "f1": round(float(f1), 4),
            "fpr": round(float(fpr), 4),
            "fnr": round(float(fnr), 4),
            "meets_recall_bar": bool(rec >= recall_bar),
            "meets_fpr_bar": bool(fpr <= fpr_bar),
        })

    cand_df = pd.DataFrame(candidates)

    # 1. Select operational threshold: satisfies recall_bar with highest F1 / lowest FPR
    satisfying = cand_df[cand_df["meets_recall_bar"]]
    if not satisfying.empty:
        # Sort by F1 descending, then threshold descending (higher threshold = fewer false alarms)
        best_row = satisfying.sort_values(by=["f1", "threshold"], ascending=[False, False]).iloc[0]
        recall_bar_met = True
    else:
        # Fallback: pick candidate with maximum recall
        best_row = cand_df.sort_values(by=["recall", "f1"], ascending=[False, False]).iloc[0]
        recall_bar_met = False
        logger.warning(
            f"Recall bar {recall_bar} could not be fully met. Max achievable recall: {best_row['recall']}"
        )

    selected_tau = float(best_row["threshold"])

    # 2. Multi-tier thresholds
    # Advisory: Target 95% recall (lowest threshold)
    adv_candidates = cand_df[cand_df["recall"] >= 0.95]
    if not adv_candidates.empty:
        advisory_tau = float(adv_candidates.sort_values(by="threshold", ascending=False).iloc[0]["threshold"])
    else:
        advisory_tau = max(round(selected_tau * 0.6, 3), 0.02)

    # Watch: Standard alert threshold
    watch_tau = selected_tau

    # Warning / Critical: High confidence
    warn_candidates = cand_df[cand_df["precision"] >= 0.50]
    if not warn_candidates.empty:
        warning_tau = float(warn_candidates.sort_values(by="threshold", ascending=True).iloc[0]["threshold"])
        warning_tau = max(warning_tau, watch_tau * 1.5)
    else:
        warning_tau = min(round(selected_tau * 2.0, 3), 0.85)

    # Ensure ordering: advisory <= watch <= warning
    if advisory_tau > watch_tau:
        advisory_tau = round(watch_tau * 0.7, 3)
    if warning_tau <= watch_tau:
        warning_tau = min(round(watch_tau * 1.5, 3), 0.90)

    result = {
        "selected_threshold": round(selected_tau, 4),
        "advisory_threshold": round(advisory_tau, 4),
        "watch_threshold": round(watch_tau, 4),
        "warning_threshold": round(warning_tau, 4),
        "metrics_at_selected_threshold": {
            "recall": float(best_row["recall"]),
            "precision": float(best_row["precision"]),
            "f1_score": float(best_row["f1"]),
            "false_positive_rate": float(best_row["fpr"]),
            "false_negative_rate": float(best_row["fnr"]),
        },
        "recall_bar_target": recall_bar,
        "recall_bar_met": recall_bar_met,
    }

    logger.info(
        f"Threshold optimization: selected={selected_tau:.4f} "
        f"(Recall={best_row['recall']:.2f}, F1={best_row['f1']:.2f}, FPR={best_row['fpr']:.2f})"
    )

    return result
