"""
scratch/hardcore_audit_engine.py
Flowshield Hardcore Adversarial Model Audit Engine
Executes empirical benchmarks, stress tests, leakage tests, baselines,
adversarial attacks, calibration analyses, and regional evaluations.
"""

import os
import sys
import json
import time
import copy
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    recall_score,
    precision_score,
    f1_score,
    brier_score_loss,
    confusion_matrix,
    accuracy_score,
)
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.calibration import calibration_curve

# Root paths
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES, TARGET_COLUMN
from ml.registry.feature_contract import CANONICAL_FEATURES, PHYSICAL_BOUNDS
from ml.registry.model_registry import model_registry
from ml.inference.predict import predict_flood_risk, load_inference_artifacts


def compute_ece(y_true, y_prob, n_bins=10):
    """Computes Expected Calibration Error."""
    bin_limits = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total_samples = len(y_true)
    for i in range(n_bins):
        bin_mask = (y_prob >= bin_limits[i]) & (y_prob < bin_limits[i + 1])
        if i == n_bins - 1:
            bin_mask = (y_prob >= bin_limits[i]) & (y_prob <= bin_limits[i + 1])
        bin_samples = np.sum(bin_mask)
        if bin_samples > 0:
            bin_acc = np.mean(y_true[bin_mask])
            bin_conf = np.mean(y_prob[bin_mask])
            ece += (bin_samples / total_samples) * np.abs(bin_acc - bin_conf)
    return float(ece)


def evaluate_predictions(y_true, y_prob, threshold=0.5):
    """Computes comprehensive metrics for binary classification."""
    y_pred = (y_prob >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    roc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else None
    pr = float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else None
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    acc = float(accuracy_score(y_true, y_pred))
    brier = float(brier_score_loss(y_true, y_prob))
    ece = compute_ece(y_true, y_prob, n_bins=10)
    fnr = float(fn / (tp + fn)) if (tp + fn) > 0 else 0.0
    fpr = float(fp / (tn + fp)) if (tn + fp) > 0 else 0.0

    return {
        "roc_auc": round(roc, 4) if roc is not None else None,
        "pr_auc": round(pr, 4) if pr is not None else None,
        "recall": round(rec, 4),
        "precision": round(prec, 4),
        "f1": round(f1, 4),
        "accuracy": round(acc, 4),
        "brier_score": round(brier, 4),
        "ece": round(ece, 4),
        "fnr": round(fnr, 4),
        "fpr": round(fpr, 4),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "total": len(y_true),
        "prevalence": round(float(np.mean(y_true)), 4),
    }


def audit_baselines(X_train, y_train, X_test, y_test, raw_test_df):
    """Benchmarks production candidate against trivial and simple models."""
    results = {}
    
    # 1. Always Negative (Majority)
    prob_0 = np.zeros(len(y_test))
    results["always_negative"] = evaluate_predictions(y_test, prob_0, threshold=0.5)
    
    # 2. Always Positive
    prob_1 = np.ones(len(y_test))
    results["always_positive"] = evaluate_predictions(y_test, prob_1, threshold=0.5)
    
    # 3. Rainfall 24h Thresholds
    rain_24 = raw_test_df["rainfall_24h_mm"].values
    for r_thresh in [30.0, 50.0, 75.0, 100.0]:
        y_pred = (rain_24 >= r_thresh).astype(int)
        # Normalized pseudo-probability based on rain_24 / 150
        prob = np.clip(rain_24 / 150.0, 0.0, 1.0)
        results[f"rain_24h_ge_{int(r_thresh)}mm"] = evaluate_predictions(y_test, prob, threshold=r_thresh/150.0)

    # 4. Rainfall 1h Cloudburst Threshold
    rain_1 = raw_test_df["rainfall_1h_mm"].values
    prob_1h = np.clip(rain_1 / 50.0, 0.0, 1.0)
    results["rain_1h_ge_30mm"] = evaluate_predictions(y_test, prob_1h, threshold=30.0/50.0)

    # 5. Joint Heuristic: Rain24h >= 75 & SoilSat >= 70%
    soil = raw_test_df["soil_saturation_pct"].values
    joint_rule = ((rain_24 >= 75.0) & (soil >= 70.0)).astype(int)
    prob_joint = joint_rule.astype(float)
    results["joint_rain_soil_heuristic"] = evaluate_predictions(y_test, prob_joint, threshold=0.5)

    # 6. Single Decision Stump (Depth 1)
    stump = DecisionTreeClassifier(max_depth=1, random_state=42)
    stump.fit(X_train, y_train)
    prob_stump = stump.predict_proba(X_test)[:, 1]
    results["decision_stump_depth_1"] = evaluate_predictions(y_test, prob_stump, threshold=0.5)

    # 7. Shallow Decision Tree (Depth 3)
    tree3 = DecisionTreeClassifier(max_depth=3, random_state=42)
    tree3.fit(X_train, y_train)
    prob_tree3 = tree3.predict_proba(X_test)[:, 1]
    results["decision_tree_depth_3"] = evaluate_predictions(y_test, prob_tree3, threshold=0.5)

    # 8. Unregularized Logistic Regression
    lr = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    prob_lr = lr.predict_proba(X_test)[:, 1]
    results["logistic_regression_default"] = evaluate_predictions(y_test, prob_lr, threshold=0.5)

    return results


print("Loaded audit engine module successfully.")
