"""
ml/training/study_model_selection.py
Flowshield — Rigorous Model Selection, Probability Calibration & Operational Threshold Study
Smart India Hackathon 2026 (PS ID: 26192)

Executes Steps 1 through 7:
- Step 1: Spatial Catchment Partitioning of Development Data (Train: 5 stations, Val: 2 stations).
          Final Test (July 1-25, 2023) kept strictly untouched until frozen evaluation.
- Step 2: Retrains Logistic Regression, Random Forest, and XGBoost on Train only.
- Step 3: Evaluates raw calibration (Brier score, log loss, ECE) and fits Platt / Isotonic calibrators.
- Step 4: Sweeps thresholds [0.01 to 0.99] on Validation set only.
- Step 5: Defines Flowshield disaster operational objective (Min FNR / High Recall, constrained FPR).
- Step 6: Selects and freezes the winning model + calibration + threshold.
- Step 7: Evaluates frozen decision pipeline on untouched July 1-25, 2023 Catastrophe Test Set.
"""

import os
import sys
import json
import time
import datetime
import numpy as np
import pandas as pd
import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    brier_score_loss,
    log_loss
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES, TARGET_COLUMN, FEATURE_METADATA

DATA_PATH = os.path.join(BASE_DIR, "data", "real", "mandi_real_hydrology_features.csv")
MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")
REPORTS_DIR = os.path.join(BASE_DIR, "ml", "reports")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

RANDOM_SEED = 26192

# ─── Operational objective constants ───
# PRIMARY: Minimize false negatives (target recall >= 85%)
# SECONDARY: Maintain acceptable false-positive workload (FPR <= 15%)
MIN_RECALL_TARGET = 0.85
MAX_FPR_TARGET = 0.15


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Computes Expected Calibration Error (ECE)."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total_samples = len(y_true)
    
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


def perform_three_way_split(df: pd.DataFrame):
    """
    Step 1: Strict Leak-Free Three-Way Split.
    - Final Test: July 1 to July 25, 2023 (Historic Beas Mega-Catastrophe, 4,200 rows, all 7 stations).
    - Development: All other periods (July 2022 baseline + July 26-31, 2023 + August 2023 event).
      - Validation / Calibration: 2 spatial holdout catchments (Pandoh Dam PND_DAM_02 and Dharampur DHR_KHD_06).
      - Training: 5 remaining catchments (Mandi Urban, Thalout, Aut, Jogindernagar, Sundernagar).
    """
    df["time"] = pd.to_datetime(df["time"])
    test_mask = (df["time"] >= "2023-07-01") & (df["time"] <= "2023-07-25 23:59:59")
    test_df = df[test_mask].copy().reset_index(drop=True)
    dev_df = df[~test_mask].copy().reset_index(drop=True)
    
    val_stations = ["PND_DAM_02", "DHR_KHD_06"]
    val_mask = dev_df["station_id"].isin(val_stations)
    val_df = dev_df[val_mask].copy().reset_index(drop=True)
    train_df = dev_df[~val_mask].copy().reset_index(drop=True)
    
    return train_df, val_df, test_df


def sweep_thresholds(y_true: np.ndarray, y_prob: np.ndarray) -> list:
    """Step 4: Sweeps decision thresholds from 0.01 to 0.99."""
    thresholds = np.linspace(0.01, 0.99, 99)
    records = []
    
    for th in thresholds:
        th = round(float(th), 2)
        y_pred = (y_prob >= th).astype(int)
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        records.append({
            "threshold": th,
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "specificity": round(float(spec), 4),
            "false_positive_rate": round(float(fpr), 4),
            "false_negative_rate": round(float(fnr), 4),
            "true_positives": int(tp),
            "false_positives": int(fp),
            "true_negatives": int(tn),
            "false_negatives": int(fn),
        })
        
    return records


def compute_full_metrics(y_true, y_pred, y_prob):
    """Computes all classification metrics for a frozen prediction set."""
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 4) if len(np.unique(y_true)) > 1 else None,
        "pr_auc": round(float(average_precision_score(y_true, y_prob)), 4) if len(np.unique(y_true)) > 1 else None,
        "brier_score": round(float(brier_score_loss(y_true, y_prob)), 4),
        "log_loss": round(float(log_loss(y_true, y_prob)), 4),
        "false_negative_rate": round(float(fnr), 4),
        "false_positive_rate": round(float(fpr), 4),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "total_samples": len(y_true),
        "actual_flood_hours": int(tp + fn),
        "missed_flood_hours": int(fn),
        "detected_flood_hours": int(tp),
    }


def main():
    print("=" * 80)
    print("FLOWSHIELD — SCIENTIFIC MODEL SELECTION & PROBABILITY CALIBRATION STUDY")
    print("=" * 80)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 1: AUDIT & DATASET PARTITIONING
    # ═══════════════════════════════════════════════════════════════════════════
    raw_df = pd.read_csv(DATA_PATH)
    train_df, val_df, test_df = perform_three_way_split(raw_df)
    
    print("\n--- STEP 1: AUDIT & DATASET PARTITIONING ---")
    print(f"Total Raw Rows: {len(raw_df):,}")
    print(f"TRAIN Set (5 stations, 2022 baseline + 2023 Dev): {len(train_df):,} samples | Positive: {int(train_df[TARGET_COLUMN].sum()):,} ({train_df[TARGET_COLUMN].mean()*100:.2f}%)")
    print(f"VAL Set   (2 holdout stations: Pandoh, Dharampur): {len(val_df):,} samples | Positive: {int(val_df[TARGET_COLUMN].sum()):,} ({val_df[TARGET_COLUMN].mean()*100:.2f}%)")
    print(f"TEST Set  (Untouched July 1-25, 2023 Catastrophe): {len(test_df):,} samples | Positive: {int(test_df[TARGET_COLUMN].sum()):,} ({test_df[TARGET_COLUMN].mean()*100:.2f}%)")
    
    print(f"\nTrain stations: {sorted(train_df['station_id'].unique().tolist())}")
    print(f"Val stations:   {sorted(val_df['station_id'].unique().tolist())}")
    print(f"Test stations:  {sorted(test_df['station_id'].unique().tolist())}")
    
    # Preprocessor fit ONLY on Train
    preprocessor = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    
    X_train = preprocessor.fit_transform(train_df[CANONICAL_FEATURE_NAMES])
    y_train = train_df[TARGET_COLUMN].values
    
    X_val = preprocessor.transform(val_df[CANONICAL_FEATURE_NAMES])
    y_val = val_df[TARGET_COLUMN].values
    
    X_test = preprocessor.transform(test_df[CANONICAL_FEATURE_NAMES])
    y_test = test_df[TARGET_COLUMN].values
    
    # Save Preprocessor (V2)
    joblib.dump(preprocessor, os.path.join(MODELS_DIR, "v2_preprocessor.joblib"))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 2: RETRAIN CANDIDATE MODELS
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n--- STEP 2: RETRAINING CANDIDATE MODELS ---")
    
    # Model 1: Logistic Regression
    print("Training Candidate 1: Logistic Regression...")
    t0 = time.time()
    lr_base = LogisticRegression(
        C=0.1,
        class_weight="balanced",
        max_iter=1000,
        solver="lbfgs",
        random_state=RANDOM_SEED
    )
    lr_base.fit(X_train, y_train)
    lr_train_time = time.time() - t0
    y_val_prob_lr_raw = lr_base.predict_proba(X_val)[:, 1]
    
    # Model 2: Random Forest
    print("Training Candidate 2: Random Forest...")
    t0 = time.time()
    rf_base = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_split=5,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=RANDOM_SEED,
        n_jobs=-1
    )
    rf_base.fit(X_train, y_train)
    rf_train_time = time.time() - t0
    y_val_prob_rf_raw = rf_base.predict_proba(X_val)[:, 1]
    
    # Model 3: XGBoost
    print("Training Candidate 3: XGBoost Classifier...")
    t0 = time.time()
    n_pos = int((y_train == 1).sum())
    n_neg = int((y_train == 0).sum())
    scale_pos_weight = float(n_neg / n_pos) if n_pos > 0 else 1.0
    
    xgb_base = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=RANDOM_SEED,
        n_jobs=-1
    )
    xgb_base.fit(X_train, y_train)
    xgb_train_time = time.time() - t0
    y_val_prob_xgb_raw = xgb_base.predict_proba(X_val)[:, 1]
    
    candidates = {
        "logistic_regression": {"model": lr_base, "raw_prob_val": y_val_prob_lr_raw, "train_time": lr_train_time},
        "random_forest": {"model": rf_base, "raw_prob_val": y_val_prob_rf_raw, "train_time": rf_train_time},
        "xgboost": {"model": xgb_base, "raw_prob_val": y_val_prob_xgb_raw, "train_time": xgb_train_time},
    }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 3: PROBABILITY CALIBRATION STUDY (ON VALIDATION SET)
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n--- STEP 3: PROBABILITY CALIBRATION STUDY (ON VALIDATION SET) ---")
    calibration_results = {}
    calibrated_models = {}
    
    for name, c_info in candidates.items():
        base_m = c_info["model"]
        y_prob_raw = c_info["raw_prob_val"]
        
        # Raw metrics
        brier_raw = brier_score_loss(y_val, y_prob_raw)
        logloss_raw = log_loss(y_val, y_prob_raw)
        ece_raw = compute_ece(y_val, y_prob_raw)
        roc_auc_val = roc_auc_score(y_val, y_prob_raw)
        pr_auc_val = average_precision_score(y_val, y_prob_raw)
        
        # Helper to construct CalibratedClassifierCV compatible across scikit-learn versions
        def _make_calibrator(base_est, method):
            try:
                from sklearn.frozen import FrozenEstimator
                return CalibratedClassifierCV(estimator=FrozenEstimator(base_est), method=method)
            except ImportError:
                return CalibratedClassifierCV(estimator=base_est, method=method, cv="prefit")

        # Platt Scaling (Sigmoid)
        cal_sigmoid = _make_calibrator(base_m, "sigmoid")
        cal_sigmoid.fit(X_val, y_val)
        y_prob_sig = cal_sigmoid.predict_proba(X_val)[:, 1]
        brier_sig = brier_score_loss(y_val, y_prob_sig)
        logloss_sig = log_loss(y_val, y_prob_sig)
        ece_sig = compute_ece(y_val, y_prob_sig)
        
        # Isotonic Regression
        cal_iso = _make_calibrator(base_m, "isotonic")
        cal_iso.fit(X_val, y_val)
        y_prob_iso = cal_iso.predict_proba(X_val)[:, 1]
        brier_iso = brier_score_loss(y_val, y_prob_iso)
        logloss_iso = log_loss(y_val, y_prob_iso)
        ece_iso = compute_ece(y_val, y_prob_iso)
        
        calibration_results[name] = {
            "discrimination": {
                "roc_auc": round(float(roc_auc_val), 4),
                "pr_auc": round(float(pr_auc_val), 4),
            },
            "raw": {"brier_score": round(float(brier_raw), 4), "log_loss": round(float(logloss_raw), 4), "ece": ece_raw},
            "sigmoid": {"brier_score": round(float(brier_sig), 4), "log_loss": round(float(logloss_sig), 4), "ece": ece_sig},
            "isotonic": {"brier_score": round(float(brier_iso), 4), "log_loss": round(float(logloss_iso), 4), "ece": ece_iso},
        }
        
        calibrated_models[name] = {
            "base": base_m,
            "sigmoid": cal_sigmoid,
            "isotonic": cal_iso,
            "probs_val": {
                "raw": y_prob_raw,
                "sigmoid": y_prob_sig,
                "isotonic": y_prob_iso
            }
        }
        
        print(f"Model: {name:<20}")
        print(f"  Discrimination: ROC-AUC={roc_auc_val:.4f}, PR-AUC={pr_auc_val:.4f}")
        print(f"  Raw:      Brier={brier_raw:.4f}, LogLoss={logloss_raw:.4f}, ECE={ece_raw:.4f}")
        print(f"  Sigmoid:  Brier={brier_sig:.4f}, LogLoss={logloss_sig:.4f}, ECE={ece_sig:.4f}")
        print(f"  Isotonic: Brier={brier_iso:.4f}, LogLoss={logloss_iso:.4f}, ECE={ece_iso:.4f}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 4 & 5: THRESHOLD ANALYSIS & OPERATIONAL OBJECTIVE
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n--- STEP 4 & 5: THRESHOLD ANALYSIS & OPERATIONAL OBJECTIVE ---")
    print("Operational Objective:")
    print(f"  PRIMARY: Minimize False Negative Rate (Target Validation Recall >= {MIN_RECALL_TARGET*100:.0f}%)")
    print(f"  SECONDARY: Control False Alarms (Target Validation FPR <= {MAX_FPR_TARGET*100:.0f}%)")
    
    threshold_sweeps = {}
    model_eval_summary = {}
    
    for name in candidates.keys():
        threshold_sweeps[name] = {}
        for variant in ["raw", "sigmoid", "isotonic"]:
            probs_v = calibrated_models[name]["probs_val"][variant]
            sweep_data = sweep_thresholds(y_val, probs_v)
            threshold_sweeps[name][variant] = sweep_data
            
            # Find operational threshold: Recall >= MIN_RECALL_TARGET, then maximize F1
            safety_candidates = [r for r in sweep_data if r["recall"] >= MIN_RECALL_TARGET]
            if safety_candidates:
                # Among candidates meeting recall target, pick highest F1
                best_safety = max(safety_candidates, key=lambda x: x["f1_score"])
            else:
                # Fallback: pick highest recall threshold
                best_safety = max(sweep_data, key=lambda x: x["recall"])
                
            # Also record the balanced F1 optimum for reference
            best_f1 = max(sweep_data, key=lambda x: x["f1_score"])
            
            candidate_key = f"{name}_{variant}"
            model_eval_summary[candidate_key] = {
                "model_name": name,
                "calibration_variant": variant,
                "roc_auc": calibration_results[name]["discrimination"]["roc_auc"],
                "pr_auc": calibration_results[name]["discrimination"]["pr_auc"],
                "brier_score": calibration_results[name][variant]["brier_score"],
                "ece": calibration_results[name][variant]["ece"],
                "log_loss": calibration_results[name][variant]["log_loss"],
                "operational_threshold": best_safety["threshold"],
                "operational_recall": best_safety["recall"],
                "operational_precision": best_safety["precision"],
                "operational_f1": best_safety["f1_score"],
                "operational_fnr": best_safety["false_negative_rate"],
                "operational_fpr": best_safety["false_positive_rate"],
                "operational_tp": best_safety["true_positives"],
                "operational_fn": best_safety["false_negatives"],
                "operational_fp": best_safety["false_positives"],
                "operational_tn": best_safety["true_negatives"],
                "balanced_f1_threshold": best_f1["threshold"],
                "balanced_f1_score": best_f1["f1_score"],
            }
            
    print(f"\nValidation Performance Summary at Operational Point (Recall >= {MIN_RECALL_TARGET*100:.0f}%):")
    print(f"{'Candidate':<28} | {'Thresh':<6} | {'Recall':<7} | {'Prec':<7} | {'F1':<7} | {'FNR':<7} | {'FPR':<7} | {'Brier':<7} | {'ROC-AUC':<7}")
    print("-" * 105)
    for k, v in model_eval_summary.items():
        print(f"{k:<28} | {v['operational_threshold']:<6.2f} | {v['operational_recall']:<7.4f} | {v['operational_precision']:<7.4f} | {v['operational_f1']:<7.4f} | {v['operational_fnr']:<7.4f} | {v['operational_fpr']:<7.4f} | {v['brier_score']:<7.4f} | {v['roc_auc']:<7.4f}")
        
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 6: MODEL SELECTION DECISION MATRIX
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n--- STEP 6: MODEL SELECTION DECISION MATRIX ---")
    
    # Measure latency and model size for each base model
    latency_and_size = {}
    for name in candidates.keys():
        m = candidates[name]["model"]
        temp_path = os.path.join(MODELS_DIR, f"temp_{name}.joblib")
        joblib.dump(m, temp_path)
        size_kb = os.path.getsize(temp_path) / 1024.0
        os.remove(temp_path)
        
        latencies = []
        sample_x = X_val[:1]
        for _ in range(500):
            t_start = time.perf_counter()
            _ = m.predict_proba(sample_x)
            latencies.append((time.perf_counter() - t_start) * 1000.0)
            
        latency_and_size[name] = {
            "model_size_kb": round(float(size_kb), 2),
            "p50_latency_ms": round(float(np.percentile(latencies, 50)), 3),
            "p95_latency_ms": round(float(np.percentile(latencies, 95)), 3),
            "mean_latency_ms": round(float(np.mean(latencies)), 3),
            "explainability": "Direct linear coefficients" if name == "logistic_regression" else ("Tree feature importances & SHAP TreeExplainer" if name == "xgboost" else "MDI feature importances"),
        }
        print(f"{name:<20}: Size={size_kb:.1f} KB | P50={latency_and_size[name]['p50_latency_ms']} ms | P95={latency_and_size[name]['p95_latency_ms']} ms")
    
    # ─── Composite Scoring ───
    # Rank each candidate across safety-relevant dimensions.
    # Weights: Recall (0.30), FNR (0.15), ROC-AUC (0.10), PR-AUC (0.10), F1 (0.10),
    #          Brier (0.10), ECE (0.05), Latency (0.05), Size (0.05)
    # Higher is better for: recall, roc_auc, pr_auc, f1
    # Lower is better for: fnr, brier, ece, latency, size
    
    scoring_weights = {
        "recall": 0.30,       # Safety-critical
        "fnr_inv": 0.15,      # Inverse of FNR (1 - FNR = recall, but penalized separately)
        "roc_auc": 0.10,
        "pr_auc": 0.10,
        "f1": 0.10,
        "brier_inv": 0.10,    # Calibration quality
        "ece_inv": 0.05,      # Calibration reliability
        "latency_inv": 0.05,  # Operational speed
        "size_inv": 0.05,     # Deployment footprint
    }
    
    # Gather raw values for normalization
    raw_scores = {}
    for k, v in model_eval_summary.items():
        model_name = v["model_name"]
        raw_scores[k] = {
            "recall": v["operational_recall"],
            "fnr_inv": 1.0 - v["operational_fnr"],
            "roc_auc": v["roc_auc"],
            "pr_auc": v["pr_auc"],
            "f1": v["operational_f1"],
            "brier_inv": 1.0 - v["brier_score"],
            "ece_inv": 1.0 - v["ece"],
            "latency_inv": 1.0 / (1.0 + latency_and_size[model_name]["p50_latency_ms"]),
            "size_inv": 1.0 / (1.0 + latency_and_size[model_name]["model_size_kb"] / 1000.0),
        }
    
    # Min-max normalize each dimension across all candidates
    dimensions = list(scoring_weights.keys())
    dim_min = {d: min(raw_scores[k][d] for k in raw_scores) for d in dimensions}
    dim_max = {d: max(raw_scores[k][d] for k in raw_scores) for d in dimensions}
    
    composite_scores = {}
    for k in raw_scores:
        score = 0.0
        for d in dimensions:
            if dim_max[d] - dim_min[d] > 1e-9:
                normalized = (raw_scores[k][d] - dim_min[d]) / (dim_max[d] - dim_min[d])
            else:
                normalized = 1.0  # All candidates equal on this dimension
            score += scoring_weights[d] * normalized
        composite_scores[k] = round(score, 4)
    
    # Rank
    ranked = sorted(composite_scores.items(), key=lambda x: x[1], reverse=True)
    
    print("\nComposite Selection Scores (higher = better, safety-weighted):")
    print(f"{'Rank':<5} | {'Candidate':<28} | {'Score':<7} | {'Recall':<7} | {'FNR':<7} | {'Brier':<7} | {'ROC-AUC':<7}")
    print("-" * 90)
    for rank, (k, score) in enumerate(ranked, 1):
        v = model_eval_summary[k]
        print(f"{rank:<5} | {k:<28} | {score:<7.4f} | {v['operational_recall']:<7.4f} | {v['operational_fnr']:<7.4f} | {v['brier_score']:<7.4f} | {v['roc_auc']:<7.4f}")
    
    # ─── Winner selection ───
    winner_key = ranked[0][0]
    winner_info = model_eval_summary[winner_key]
    winner_model_name = winner_info["model_name"]
    winner_calibration = winner_info["calibration_variant"]
    winner_threshold = winner_info["operational_threshold"]
    
    print(f"\n{'='*80}")
    print(f"SELECTED MODEL: {winner_model_name}")
    print(f"CALIBRATION:    {winner_calibration}")
    print(f"THRESHOLD:      {winner_threshold}")
    print(f"VALIDATION RECALL: {winner_info['operational_recall']:.4f}")
    print(f"VALIDATION FNR:    {winner_info['operational_fnr']:.4f}")
    print(f"VALIDATION F1:     {winner_info['operational_f1']:.4f}")
    print(f"{'='*80}")
    
    # ─── Freeze artifacts ───
    # Save the selected base model
    selected_base_model = candidates[winner_model_name]["model"]
    joblib.dump(selected_base_model, os.path.join(MODELS_DIR, "v2_selected_model.joblib"))
    
    # Save calibrator (if not raw)
    if winner_calibration != "raw":
        selected_calibrator = calibrated_models[winner_model_name][winner_calibration]
        joblib.dump(selected_calibrator, os.path.join(MODELS_DIR, "v2_calibrator.joblib"))
    
    # Save all base models for reproducibility
    joblib.dump(lr_base, os.path.join(MODELS_DIR, "lr_real_flood_model.joblib"))
    joblib.dump(rf_base, os.path.join(MODELS_DIR, "rf_real_flood_model.joblib"))
    joblib.dump(xgb_base, os.path.join(MODELS_DIR, "xgb_real_flood_model.joblib"))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 7: FINAL UNBIASED TEST (FROZEN PIPELINE ON UNTOUCHED JULY 2023)
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n--- STEP 7: FINAL UNBIASED TEST ON UNTOUCHED JULY 1-25, 2023 CATASTROPHE SET ---")
    print(f"Frozen Pipeline: {winner_model_name} + {winner_calibration} calibration + threshold={winner_threshold}")
    print(f"Test samples: {len(y_test):,} | Actual flood hours: {int(y_test.sum()):,}")
    
    # Generate probabilities on the test set
    if winner_calibration == "raw":
        y_test_prob = selected_base_model.predict_proba(X_test)[:, 1]
    else:
        selected_calibrator_obj = calibrated_models[winner_model_name][winner_calibration]
        y_test_prob = selected_calibrator_obj.predict_proba(X_test)[:, 1]
    
    # Apply frozen threshold
    y_test_pred = (y_test_prob >= winner_threshold).astype(int)
    
    # Measure inference latency on test set
    test_latencies = []
    for _ in range(100):
        t_start = time.perf_counter()
        if winner_calibration == "raw":
            _ = selected_base_model.predict_proba(X_test[:1])
        else:
            _ = selected_calibrator_obj.predict_proba(X_test[:1])
        test_latencies.append((time.perf_counter() - t_start) * 1000.0)
    
    # Compute all final metrics
    final_metrics = compute_full_metrics(y_test, y_test_pred, y_test_prob)
    final_metrics["inference_p50_latency_ms"] = round(float(np.percentile(test_latencies, 50)), 3)
    final_metrics["inference_p95_latency_ms"] = round(float(np.percentile(test_latencies, 95)), 3)
    
    print(f"\n{'='*80}")
    print("FINAL TEST RESULTS — UNTOUCHED JULY 2023 CATASTROPHE SET")
    print(f"{'='*80}")
    print(f"Accuracy:    {final_metrics['accuracy']}")
    print(f"Precision:   {final_metrics['precision']}")
    print(f"Recall:      {final_metrics['recall']}")
    print(f"F1-Score:    {final_metrics['f1_score']}")
    print(f"ROC-AUC:     {final_metrics['roc_auc']}")
    print(f"PR-AUC:      {final_metrics['pr_auc']}")
    print(f"Brier Score: {final_metrics['brier_score']}")
    print(f"Log Loss:    {final_metrics['log_loss']}")
    print(f"FNR:         {final_metrics['false_negative_rate']}")
    print(f"FPR:         {final_metrics['false_positive_rate']}")
    print(f"\nConfusion Matrix:")
    cm = final_metrics["confusion_matrix"]
    print(f"  True Negatives:  {cm['true_negatives']}")
    print(f"  False Positives: {cm['false_positives']}")
    print(f"  False Negatives: {cm['false_negatives']} (MISSED FLOOD HOURS)")
    print(f"  True Positives:  {cm['true_positives']} (DETECTED FLOOD HOURS)")
    print(f"\n*** {final_metrics['missed_flood_hours']} of {final_metrics['actual_flood_hours']} real flood-positive hours were MISSED ***")
    print(f"*** {final_metrics['detected_flood_hours']} of {final_metrics['actual_flood_hours']} real flood-positive hours were DETECTED ***")
    print(f"{'='*80}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SAVE ALL REPORTS & FROZEN DECISION PIPELINE
    # ═══════════════════════════════════════════════════════════════════════════
    
    # 1. Frozen decision pipeline manifest
    decision_pipeline = {
        "pipeline_version": "flowshield-flood-risk-v2",
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "selected_model": winner_model_name,
        "calibration_method": winner_calibration,
        "threshold": winner_threshold,
        "model_artifact": "v2_selected_model.joblib",
        "calibrator_artifact": "v2_calibrator.joblib" if winner_calibration != "raw" else None,
        "preprocessor_artifact": "v2_preprocessor.joblib",
        "features": CANONICAL_FEATURE_NAMES,
        "target": TARGET_COLUMN,
        "operational_objective": {
            "primary": f"Minimize False Negative Rate (target recall >= {MIN_RECALL_TARGET})",
            "secondary": f"Control False Positive Rate (target FPR <= {MAX_FPR_TARGET})",
        },
        "split_strategy": {
            "train": {
                "stations": sorted(train_df["station_id"].unique().tolist()),
                "samples": len(train_df),
                "positive_count": int(train_df[TARGET_COLUMN].sum()),
            },
            "validation": {
                "stations": sorted(val_df["station_id"].unique().tolist()),
                "samples": len(val_df),
                "positive_count": int(val_df[TARGET_COLUMN].sum()),
            },
            "test": {
                "period": "2023-07-01 to 2023-07-25",
                "stations": sorted(test_df["station_id"].unique().tolist()),
                "samples": len(test_df),
                "positive_count": int(test_df[TARGET_COLUMN].sum()),
            },
        },
        "validation_metrics": {
            "recall": winner_info["operational_recall"],
            "precision": winner_info["operational_precision"],
            "f1_score": winner_info["operational_f1"],
            "fnr": winner_info["operational_fnr"],
            "fpr": winner_info["operational_fpr"],
            "roc_auc": winner_info["roc_auc"],
            "pr_auc": winner_info["pr_auc"],
            "brier_score": winner_info["brier_score"],
            "ece": winner_info["ece"],
        },
        "final_test_metrics": final_metrics,
        "composite_selection_score": composite_scores[winner_key],
        "all_candidate_scores": {k: v for k, v in ranked},
    }
    
    pipeline_path = os.path.join(MODELS_DIR, "v2_decision_pipeline.json")
    with open(pipeline_path, "w") as f:
        json.dump(decision_pipeline, f, indent=2)
    print(f"\n[OK] Frozen decision pipeline saved: {pipeline_path}")
    
    # 2. Calibration study report
    with open(os.path.join(REPORTS_DIR, "calibration_study_validation.json"), "w") as f:
        json.dump(calibration_results, f, indent=2)
    
    # 3. Threshold sweeps
    with open(os.path.join(REPORTS_DIR, "threshold_sweeps_validation.json"), "w") as f:
        json.dump(threshold_sweeps, f, indent=2)
    
    # 4. Full model comparison
    comparison_report = {
        "model_eval_summary": model_eval_summary,
        "composite_scores": {k: v for k, v in ranked},
        "latency_and_size": latency_and_size,
        "calibration_results": calibration_results,
    }
    with open(os.path.join(REPORTS_DIR, "validation_model_comparison.json"), "w") as f:
        json.dump(comparison_report, f, indent=2)
    
    # 5. Feature importances (for selected model if tree-based)
    feature_importances = []
    if hasattr(selected_base_model, "feature_importances_"):
        importances = selected_base_model.feature_importances_
        feature_importances = sorted(
            [{"feature": f, "importance": round(float(imp), 4)} for f, imp in zip(CANONICAL_FEATURE_NAMES, importances)],
            key=lambda x: x["importance"], reverse=True
        )
    elif hasattr(selected_base_model, "coef_"):
        coefs = selected_base_model.coef_[0]
        feature_importances = sorted(
            [{"feature": f, "coefficient": round(float(c), 4), "abs_importance": round(float(abs(c)), 4)} for f, c in zip(CANONICAL_FEATURE_NAMES, coefs)],
            key=lambda x: x["abs_importance"], reverse=True
        )
    
    # 6. Updated feature schema
    schema_info = {
        "model_version": "flowshield-flood-risk-v2",
        "trained_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "features": CANONICAL_FEATURE_NAMES,
        "target": TARGET_COLUMN,
        "selected_model": winner_model_name,
        "calibration_method": winner_calibration,
        "threshold": winner_threshold,
        "feature_importances": feature_importances,
    }
    with open(os.path.join(MODELS_DIR, "feature_schema.json"), "w") as f:
        json.dump(schema_info, f, indent=2)
    
    # 7. Updated metrics comparison
    v2_metrics_report = {
        "benchmark_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pipeline_version": "flowshield-flood-risk-v2",
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "test_positive_floods": int(sum(y_test)),
        "models": {
            m_name: {
                "model_name": m_name,
                "roc_auc": calibration_results[m_name]["discrimination"]["roc_auc"],
                "pr_auc": calibration_results[m_name]["discrimination"]["pr_auc"],
                "raw_brier": calibration_results[m_name]["raw"]["brier_score"],
                "calibrated_brier": calibration_results[m_name]["isotonic"]["brier_score"],
                "raw_ece": calibration_results[m_name]["raw"]["ece"],
                "calibrated_ece": calibration_results[m_name]["isotonic"]["ece"],
                "operational_recall": model_eval_summary[f"{m_name}_isotonic"]["operational_recall"],
                "operational_fnr": model_eval_summary[f"{m_name}_isotonic"]["operational_fnr"],
                "operational_f1": model_eval_summary[f"{m_name}_isotonic"]["operational_f1"],
                "operational_threshold": model_eval_summary[f"{m_name}_isotonic"]["operational_threshold"],
                "latency_p50_ms": latency_and_size[m_name]["p50_latency_ms"],
                "model_size_kb": latency_and_size[m_name]["model_size_kb"],
            }
            for m_name in ["logistic_regression", "random_forest", "xgboost"]
        },
        "selected_model": winner_model_name,
        "calibration_method": winner_calibration,
        "threshold": winner_threshold,
        "final_test_metrics": final_metrics,
        "feature_importances": feature_importances,
    }
    with open(os.path.join(REPORTS_DIR, "metrics_comparison.json"), "w") as f:
        json.dump(v2_metrics_report, f, indent=2)
    
    print(f"[OK] All reports saved to {REPORTS_DIR}")
    print(f"[OK] All model artifacts saved to {MODELS_DIR}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FINAL MODEL DECISION SUMMARY
    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'='*80}")
    print("FINAL MODEL DECISION")
    print(f"{'='*80}")
    print(f"SELECTED MODEL:        {winner_model_name}")
    print(f"CALIBRATION:           {winner_calibration}")
    print(f"OPERATIONAL THRESHOLD: {winner_threshold}")
    print(f"VALIDATION REASON:     Highest composite safety score ({composite_scores[winner_key]:.4f}) across")
    print(f"                       recall, FNR, ROC-AUC, PR-AUC, F1, Brier, ECE, latency, size")
    print(f"FINAL JULY 2023 TEST:  Recall={final_metrics['recall']}, F1={final_metrics['f1_score']}, ROC-AUC={final_metrics['roc_auc']}")
    print(f"FALSE NEGATIVES:       {final_metrics['missed_flood_hours']} of {final_metrics['actual_flood_hours']} flood hours missed")
    print(f"API VERSION:           flowshield-flood-risk-v2")
    print(f"{'='*80}")
    
    return decision_pipeline


if __name__ == "__main__":
    main()
