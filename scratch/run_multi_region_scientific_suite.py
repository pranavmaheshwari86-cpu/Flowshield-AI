"""
scratch/run_multi_region_scientific_suite.py
Flowshield — Multi-Region Training, Baseline Evaluation & Cross-Region Transfer Suite
Evaluates all 10 Himalayan & North-Eastern regions on authentic real empirical data.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.frozen import FrozenEstimator
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    recall_score,
    precision_score,
    f1_score,
    brier_score_loss,
    confusion_matrix,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES
from ml.registry.region_resolver import SUPPORTED_REGIONS, region_resolver

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("flowshield.multi_region_suite")

def evaluate_predictions(y_true, y_prob, threshold=0.5):
    if len(y_true) == 0:
        return {}
    y_pred = (y_prob >= threshold).astype(int)
    has_two_classes = len(np.unique(y_true)) > 1
    roc = float(roc_auc_score(y_true, y_prob)) if has_two_classes else 0.5
    pr = float(average_precision_score(y_true, y_prob)) if has_two_classes else float(y_true.mean())
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    brier = float(brier_score_loss(y_true, y_prob))
    
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=5, strategy="uniform") if has_two_classes else ([], [])
    ece = float(np.mean(np.abs(prob_true - prob_pred))) if len(prob_true) > 0 else 0.0
    
    return {
        "roc_auc": round(roc, 4),
        "pr_auc": round(pr, 4),
        "recall": round(rec, 4),
        "precision": round(prec, 4),
        "f1": round(f1, 4),
        "brier": round(brier, 4),
        "ece": round(ece, 4),
        "samples": len(y_true),
        "flood_hours": int(np.sum(y_true)),
    }

def process_region(region_slug: str) -> Dict[str, Any]:
    processed_p = REPO_ROOT / "ml" / "data" / "processed" / region_slug / f"{region_slug}_processed_dataset.csv"
    if not processed_p.exists():
        logger.warning(f"No processed dataset for {region_slug}")
        return {"status": "NO_DATA"}
        
    df = pd.read_csv(processed_p)
    time_col = "datetime_utc" if "datetime_utc" in df.columns else "time"
    df[time_col] = pd.to_datetime(df[time_col], utc=True)
    df = df.sort_values(time_col).reset_index(drop=True)
    
    total_len = len(df)
    n_floods = int(df["flood_occurred"].sum())
    prev = (n_floods / total_len * 100.0) if total_len > 0 else 0.0
    
    logger.info(f"Evaluating {region_slug}: {total_len} rows, {n_floods} flood hours ({prev:.2f}%)")
    
    if n_floods < 10:
        return {
            "status": "INSUFFICIENT_EVENTS",
            "region_slug": region_slug,
            "total_samples": total_len,
            "flood_hours": n_floods,
            "prevalence_pct": round(prev, 2),
            "reason": f"Only {n_floods} positive hours available in verified record (minimum 10 required for holdout splitting)."
        }
        
    if region_slug == "himachal_pradesh":
        train_df = df[(df[time_col] >= "2022-07-01") & (df[time_col] <= "2022-07-31 23:00:00")].copy()
        val_df = df[(df[time_col] >= "2023-07-01") & (df[time_col] <= "2023-07-31 23:00:00")].copy()
        hold_df = df[(df[time_col] >= "2023-08-01") & (df[time_col] <= "2023-08-31 23:00:00")].copy()
    elif region_slug == "jammu_kashmir":
        train_df = df[(df[time_col] >= "2023-06-01") & (df[time_col] <= "2023-06-30 23:00:00")].copy()
        val_df = df[(df[time_col] >= "2023-07-01") & (df[time_col] <= "2023-07-31 23:00:00")].copy()
        hold_df = df[(df[time_col] >= "2023-08-01") & (df[time_col] <= "2023-08-31 23:00:00")].copy()
    else:
        # Chronological partition (50% Train, 25% Val, 25% Holdout)
        n_train = int(total_len * 0.50)
        n_val = int(total_len * 0.25)
        
        train_df = df.iloc[:n_train].copy()
        val_df = df.iloc[n_train:n_train + n_val].copy()
        hold_df = df.iloc[n_train + n_val:].copy()
    
    y_train = train_df["flood_occurred"].values
    y_val = val_df["flood_occurred"].values
    y_hold = hold_df["flood_occurred"].values
    
    if len(np.unique(y_train)) < 2 or len(np.unique(y_hold)) < 2:
        return {
            "status": "TEMPORAL_CONCENTRATION_LIMIT",
            "region_slug": region_slug,
            "total_samples": total_len,
            "flood_hours": n_floods,
            "train_floods": int(np.sum(y_train)),
            "val_floods": int(np.sum(y_val)),
            "holdout_floods": int(np.sum(y_hold)),
            "reason": f"Flood events are temporally clustered in a single partition (Train={int(np.sum(y_train))}, Val={int(np.sum(y_val))}, Holdout={int(np.sum(y_hold))}). Multi-season acquisition required for within-region holdout.",
        }
    
    # 1. Rung 2: 24h Rain Heuristic (>= 30mm)
    p_r2 = np.clip(hold_df["rainfall_24h_mm"].values / 60.0, 0.0, 1.0)
    eval_r2 = evaluate_predictions(y_hold, p_r2, threshold=30.0 / 60.0)
    
    # 2. Rung 3: Rainfall-Only Logistic
    f_r3 = ["rainfall_1h_mm", "rainfall_3h_mm", "rainfall_6h_mm", "rainfall_24h_mm", "rainfall_72h_mm"]
    pipe_r3 = Pipeline([("imp", SimpleImputer(strategy="median")), ("scl", StandardScaler()), ("lr", LogisticRegression(class_weight="balanced", random_state=42))])
    pipe_r3.fit(train_df[f_r3], y_train)
    p_r3 = pipe_r3.predict_proba(hold_df[f_r3])[:, 1]
    eval_r3 = evaluate_predictions(y_hold, p_r3, threshold=0.5)
    
    # 3. Rung 7: Full 15-Feature Calibrated Logistic Regression
    pipe_r7 = Pipeline([("imp", SimpleImputer(strategy="median")), ("scl", StandardScaler()), ("lr", LogisticRegression(class_weight="balanced", random_state=42))])
    pipe_r7.fit(train_df[CANONICAL_FEATURE_NAMES], y_train)
    
    # Calibration
    if len(np.unique(y_val)) > 1:
        cal = CalibratedClassifierCV(estimator=FrozenEstimator(pipe_r7), method="isotonic")
        cal.fit(val_df[CANONICAL_FEATURE_NAMES], y_val)
        p_r7 = cal.predict_proba(hold_df[CANONICAL_FEATURE_NAMES])[:, 1]
        
        # Operational threshold optimization on validation set
        val_probs = cal.predict_proba(val_df[CANONICAL_FEATURE_NAMES])[:, 1]
        best_t, best_u = 0.5, -999.0
        for t in np.linspace(0.05, 0.95, 19):
            preds = (val_probs >= t).astype(int)
            r = recall_score(y_val, preds, zero_division=0)
            tn, fp, fn, tp = confusion_matrix(y_val, preds, labels=[0, 1]).ravel()
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
            u = r - 0.5 * fpr
            if u > best_u:
                best_u = u
                best_t = t
        opt_tau = round(best_t, 2)
    else:
        p_r7 = pipe_r7.predict_proba(hold_df[CANONICAL_FEATURE_NAMES])[:, 1]
        opt_tau = 0.50
        
    eval_r7 = evaluate_predictions(y_hold, p_r7, threshold=opt_tau)
    
    return {
        "status": "EVALUATED",
        "region_slug": region_slug,
        "total_samples": total_len,
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "holdout_samples": len(hold_df),
        "holdout_flood_hours": int(np.sum(y_hold)),
        "optimal_threshold": opt_tau,
        "rung_2_rain_24h_heuristic": eval_r2,
        "rung_3_rainfall_only_ml": eval_r3,
        "rung_7_full_15_calibrated_ml": eval_r7,
    }

if __name__ == "__main__":
    multi_results = {}
    for slug in SUPPORTED_REGIONS:
        res = process_region(slug)
        multi_results[slug] = res
        
    out_file = REPO_ROOT / "scratch" / "multi_region_evaluation_results.json"
    with open(out_file, "w") as f:
        json.dump(multi_results, f, indent=2)
        
    print(f"\nSaved multi-region evaluation to {out_file}")
