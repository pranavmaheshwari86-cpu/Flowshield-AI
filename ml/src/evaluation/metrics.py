"""
ml/src/evaluation/metrics.py
Flowshield — Evaluation Metrics, Expected Calibration Error & Safety Gates
"""

from typing import Dict, Any, Union
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    brier_score_loss,
    log_loss,
)


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """
    Computes Expected Calibration Error (ECE) across n uniform probability bins.
    ECE = sum_{b=1}^B (|B_b| / N) * |acc(B_b) - conf(B_b)|
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    
    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    total_samples = len(y_true)

    if total_samples == 0:
        return 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        if i == n_bins - 1:
            in_bin = (y_prob >= bin_lower) & (y_prob <= bin_upper)
        else:
            in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)

        bin_size = np.sum(in_bin)
        if bin_size > 0:
            bin_acc = np.mean(y_true[in_bin])
            bin_conf = np.mean(y_prob[in_bin])
            ece += (bin_size / total_samples) * abs(bin_acc - bin_conf)

    return round(float(ece), 4)


def check_monotonicity(y_raw: np.ndarray, y_cal: np.ndarray) -> bool:
    """
    Verifies that probability calibrator preserves ranking monotonicity.
    Ensures higher raw risk scores correspond to non-decreasing calibrated probabilities.
    """
    order = np.argsort(y_raw)
    sorted_cal = np.asarray(y_cal)[order]
    diffs = np.diff(sorted_cal)
    # Allow numerical precision margin (-1e-6)
    violations = np.sum(diffs < -1e-6)
    return bool(violations == 0)


def calculate_classification_metrics(
    y_true: Union[np.ndarray, list],
    y_prob: Union[np.ndarray, list],
    threshold: float = 0.08,
) -> Dict[str, Any]:
    """
    Computes comprehensive flood operational risk classification metrics.
    Emphasizes Catastrophe Recall (minimizing False Negative Rate).
    """
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob).astype(float)
    y_pred = (y_prob >= threshold).astype(int)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    recall = float(recall_score(y_true, y_pred, zero_division=0))
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    acc = float(accuracy_score(y_true, y_pred))

    try:
        roc_auc = float(roc_auc_score(y_true, y_prob))
    except ValueError:
        roc_auc = 0.5

    try:
        pr_auc = float(average_precision_score(y_true, y_prob))
    except ValueError:
        pr_auc = 0.0

    brier = float(brier_score_loss(y_true, y_prob))
    ece = compute_ece(y_true, y_prob)

    fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    return {
        "threshold": float(threshold),
        "recall": round(recall, 4),
        "catastrophe_recall": round(recall, 4),
        "precision": round(precision, 4),
        "f1_score": round(f1, 4),
        "accuracy": round(acc, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "brier_score": round(brier, 4),
        "ece": round(ece, 4),
        "fnr": round(float(fnr), 4),
        "fpr": round(float(fpr), 4),
        "true_positives": int(tp),
        "false_negatives": int(fn),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "total_samples": len(y_true),
    }
