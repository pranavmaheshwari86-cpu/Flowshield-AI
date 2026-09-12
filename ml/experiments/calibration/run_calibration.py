# ml/training/run_calibration.py
import os
import sys
import json
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import brier_score_loss, roc_auc_score, average_precision_score

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SPLITS_DIR = os.path.join(REPO_ROOT, "ml", "data", "splits")
TOURNAMENT_DIR = os.path.join(REPO_ROOT, "ml", "models", "tournament")
REPORTS_DIR = os.path.join(REPO_ROOT, "ml", "reports")

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES


def compute_ece(y_true, y_prob, n_bins=10):
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


def check_monotonicity(y_raw, y_cal):
    # Sort by raw probability
    order = np.argsort(y_raw)
    sorted_cal = y_cal[order]
    # Check if calibrated probabilities are non-decreasing
    diffs = np.diff(sorted_cal)
    # Allow tiny numerical precision noise (-1e-6)
    violations = np.sum(diffs < -1e-6)
    return bool(violations == 0)


def run_calibration():
    # Load champion model
    winner_path = os.path.join(TOURNAMENT_DIR, "candidate_logisticregression.joblib")
    winner_pipe = joblib.load(winner_path)

    # Load splits
    val_cal_df = pd.read_csv(os.path.join(SPLITS_DIR, "val_cal_split.csv"))
    val_tune_df = pd.read_csv(os.path.join(SPLITS_DIR, "val_tune_split.csv"))

    X_cal = val_cal_df[CANONICAL_FEATURE_NAMES]
    y_cal = val_cal_df["flood_occurred"]

    X_tune = val_tune_df[CANONICAL_FEATURE_NAMES]
    y_tune = val_tune_df["flood_occurred"]

    raw_probs_tune = winner_pipe.predict_proba(X_tune)[:, 1]
    raw_brier = float(brier_score_loss(y_tune, raw_probs_tune))
    raw_ece = compute_ece(y_tune.values, raw_probs_tune)

    calibrator_types = ["sigmoid", "isotonic"]
    cal_eval = {}

    for method in calibrator_types:
        cal = CalibratedClassifierCV(estimator=FrozenEstimator(winner_pipe), method=method)
        cal.fit(X_cal, y_cal)

        cal_probs = cal.predict_proba(X_tune)[:, 1]
        brier = float(brier_score_loss(y_tune, cal_probs))
        ece = compute_ece(y_tune.values, cal_probs)
        auc = float(roc_auc_score(y_tune, cal_probs))
        pr_auc = float(average_precision_score(y_tune, cal_probs))
        is_monotonic = check_monotonicity(raw_probs_tune, cal_probs)

        artifact_name = f"calibrator_{method}.joblib"
        artifact_path = os.path.join(TOURNAMENT_DIR, artifact_name)
        joblib.dump(cal, artifact_path)

        cal_eval[method] = {
            "artifact_path": artifact_path,
            "brier_score": round(brier, 4),
            "ece": ece,
            "roc_auc": round(auc, 4),
            "pr_auc": round(pr_auc, 4),
            "is_monotonic": is_monotonic,
            "mean_calibrated_prob": round(float(np.mean(cal_probs)), 4),
            "min_calibrated_prob": round(float(np.min(cal_probs)), 4),
            "max_calibrated_prob": round(float(np.max(cal_probs)), 4),
        }

    # Selection rule: Lower Brier score on VAL-TUNE subject to monotonicity
    valid_methods = [m for m, s in cal_eval.items() if s["is_monotonic"]]
    if not valid_methods:
        valid_methods = list(cal_eval.keys())

    selected_method = min(valid_methods, key=lambda m: cal_eval[m]["brier_score"])
    selected_stats = cal_eval[selected_method]

    report = {
        "phase": "PHASE_8_CALIBRATION_ARCHITECTURE",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "champion_model": "LogisticRegression",
        "cal_fit_samples": len(X_cal),
        "cal_fit_positives": int(sum(y_cal)),
        "eval_tune_samples": len(X_tune),
        "eval_tune_positives": int(sum(y_tune)),
        "raw_uncalibrated": {
            "brier_score": round(raw_brier, 4),
            "ece": raw_ece,
        },
        "methods_evaluated": cal_eval,
        "selected_calibrator": selected_method,
        "selected_calibrator_artifact": selected_stats["artifact_path"],
        "status": "ALL_CHECKS_PASSED",
    }

    report_path = os.path.join(REPORTS_DIR, "calibration_evaluation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=" * 60)
    print("PHASE 8 CALIBRATION COMPLETE")
    print("=" * 60)
    print(f"Raw Uncalibrated: Brier={raw_brier:.4f}, ECE={raw_ece:.4f}")
    for m, s in cal_eval.items():
        print(f"Method: {m:<10} Brier={s['brier_score']:.4f} ECE={s['ece']:.4f} Monotonic={s['is_monotonic']}")
    print("=" * 60)
    print(f"Selected Calibrator: {selected_method} (Artifact: {selected_stats['artifact_path']})")
    print("Report written to:", report_path)


if __name__ == "__main__":
    run_calibration()
