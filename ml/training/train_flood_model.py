"""
ml/training/train_flood_model.py
Flowshield — Reproducible Real Baseline ML Training Pipeline
Smart India Hackathon 2026 (PS ID: 26192)

Trains and benchmarks:
1. Baseline A: Logistic Regression (Linear)
2. Baseline B: Random Forest (Non-linear bagging ensemble)
3. Advanced: XGBoost (Gradient Boosting Decision Trees)

Strictly uses real public data in data/real/. Zero fabrication.
Evaluates on an isolated historical mega-disaster holdout window (July 2023).
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
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from ml.preprocessing.pipeline import prepare_datasets
from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES, TARGET_COLUMN

MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")
REPORTS_DIR = os.path.join(BASE_DIR, "ml", "reports")
CONFIG_PATH = os.path.join(BASE_DIR, "ml", "configs", "train_config.json")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def calculate_metrics(y_true, y_pred, y_prob) -> dict:
    """Computes comprehensive evaluation metrics with focus on disaster recall."""
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    # False Negative Rate: Percentage of actual flood events that were missed
    fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0
    
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 4) if len(np.unique(y_true)) > 1 else None,
        "pr_auc": round(float(average_precision_score(y_true, y_prob)), 4) if len(np.unique(y_true)) > 1 else None,
        "false_negative_rate": round(float(fnr), 4),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "total_test_samples": len(y_true),
        "actual_floods_count": int(tp + fn),
        "missed_floods_count": int(fn),
    }


def main():
    print("================================================================================")
    print("FLOWSHIELD — REAL DATA BASELINE ML TRAINING & BENCHMARKING PIPELINE")
    print("================================================================================")
    
    # Load config
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    seed = config.get("random_seed", 26192)
    print(f"Random Seed: {seed}")
    
    # Prepare datasets
    X_train, y_train, X_test, y_test, preprocessor, train_df, test_df = prepare_datasets()
    
    # Save preprocessor
    preproc_path = os.path.join(MODELS_DIR, "preprocessor.joblib")
    joblib.dump(preprocessor, preproc_path)
    print(f"[OK] Preprocessing pipeline saved: {preproc_path}")
    
    results = {}
    trained_models = {}
    
    # 1. Model A1: Logistic Regression (Linear Baseline)
    print("\n--- Training Model 1: Logistic Regression (Baseline) ---")
    t0 = time.time()
    lr_cfg = config["models"]["logistic_regression"]
    lr_model = LogisticRegression(
        C=lr_cfg["C"],
        class_weight=lr_cfg["class_weight"],
        max_iter=lr_cfg["max_iter"],
        solver=lr_cfg["solver"],
        random_state=seed
    )
    lr_model.fit(X_train, y_train)
    lr_time = time.time() - t0
    
    y_pred_lr = lr_model.predict(X_test)
    y_prob_lr = lr_model.predict_proba(X_test)[:, 1]
    metrics_lr = calculate_metrics(y_test, y_pred_lr, y_prob_lr)
    metrics_lr["training_time_sec"] = round(lr_time, 3)
    results["logistic_regression"] = metrics_lr
    trained_models["logistic_regression"] = lr_model
    print(f"Logistic Regression Results: Acc={metrics_lr['accuracy']}, Recall={metrics_lr['recall']}, F1={metrics_lr['f1_score']}, ROC-AUC={metrics_lr['roc_auc']}, FNR={metrics_lr['false_negative_rate']}")
    
    # 2. Model A2: Random Forest (Bagging Ensemble Baseline)
    print("\n--- Training Model 2: Random Forest (Non-Linear Baseline) ---")
    t0 = time.time()
    rf_cfg = config["models"]["random_forest"]
    rf_model = RandomForestClassifier(
        n_estimators=rf_cfg["n_estimators"],
        max_depth=rf_cfg["max_depth"],
        min_samples_split=rf_cfg["min_samples_split"],
        min_samples_leaf=rf_cfg["min_samples_leaf"],
        class_weight=rf_cfg["class_weight"],
        random_state=seed,
        n_jobs=rf_cfg["n_jobs"]
    )
    rf_model.fit(X_train, y_train)
    rf_time = time.time() - t0
    
    y_pred_rf = rf_model.predict(X_test)
    y_prob_rf = rf_model.predict_proba(X_test)[:, 1]
    metrics_rf = calculate_metrics(y_test, y_pred_rf, y_prob_rf)
    metrics_rf["training_time_sec"] = round(rf_time, 3)
    results["random_forest"] = metrics_rf
    trained_models["random_forest"] = rf_model
    print(f"Random Forest Results: Acc={metrics_rf['accuracy']}, Recall={metrics_rf['recall']}, F1={metrics_rf['f1_score']}, ROC-AUC={metrics_rf['roc_auc']}, FNR={metrics_rf['false_negative_rate']}")
    
    # 3. Model A3: XGBoost (Gradient Boosting)
    print("\n--- Training Model 3: XGBoost (Primary Gradient Boosting) ---")
    t0 = time.time()
    xgb_cfg = config["models"]["xgboost"]
    xgb_model = XGBClassifier(
        n_estimators=xgb_cfg["n_estimators"],
        max_depth=xgb_cfg["max_depth"],
        learning_rate=xgb_cfg["learning_rate"],
        subsample=xgb_cfg["subsample"],
        colsample_bytree=xgb_cfg["colsample_bytree"],
        scale_pos_weight=xgb_cfg["scale_pos_weight"],
        eval_metric=xgb_cfg["eval_metric"],
        random_state=seed,
        n_jobs=xgb_cfg["n_jobs"]
    )
    xgb_model.fit(X_train, y_train)
    xgb_time = time.time() - t0
    
    y_pred_xgb = xgb_model.predict(X_test)
    y_prob_xgb = xgb_model.predict_proba(X_test)[:, 1]
    metrics_xgb = calculate_metrics(y_test, y_pred_xgb, y_prob_xgb)
    metrics_xgb["training_time_sec"] = round(xgb_time, 3)
    results["xgboost"] = metrics_xgb
    trained_models["xgboost"] = xgb_model
    print(f"XGBoost Results: Acc={metrics_xgb['accuracy']}, Recall={metrics_xgb['recall']}, F1={metrics_xgb['f1_score']}, ROC-AUC={metrics_xgb['roc_auc']}, FNR={metrics_xgb['false_negative_rate']}")
    
    # Feature Importances from XGBoost
    importances = xgb_model.feature_importances_
    feat_imp = sorted(
        [{"feature": f, "importance": round(float(imp), 4)} for f, imp in zip(CANONICAL_FEATURE_NAMES, importances)],
        key=lambda x: x["importance"],
        reverse=True
    )
    
    # Save All Model Artifacts
    joblib.dump(lr_model, os.path.join(MODELS_DIR, "lr_real_flood_model.joblib"))
    joblib.dump(rf_model, os.path.join(MODELS_DIR, "rf_real_flood_model.joblib"))
    best_model_name = "xgboost"
    best_model = trained_models[best_model_name]
    model_version = f"flowshield-xgb-real-v1-{datetime.datetime.now().strftime('%Y%m%d')}"
    
    best_model_path = os.path.join(MODELS_DIR, "xgb_real_flood_model.joblib")
    joblib.dump(best_model, best_model_path)
    print(f"\n[OK] Saved all models (LR, RF, XGB) to {MODELS_DIR}")
    
    # Save Feature Schema
    schema_info = {
        "model_version": model_version,
        "trained_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "random_seed": seed,
        "features": CANONICAL_FEATURE_NAMES,
        "target": TARGET_COLUMN,
        "best_model": best_model_name,
        "feature_importances": feat_imp,
    }
    schema_path = os.path.join(MODELS_DIR, "feature_schema.json")
    with open(schema_path, "w") as f:
        json.dump(schema_info, f, indent=2)
    print(f"[OK] Saved feature schema: {schema_path}")
    
    # Save Benchmark Metrics Comparison Report
    summary_report = {
        "benchmark_date": datetime.datetime.utcnow().isoformat() + "Z",
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "test_positive_floods": int(sum(y_test)),
        "models": results,
        "feature_importances_xgb": feat_imp,
    }
    report_path = os.path.join(REPORTS_DIR, "metrics_comparison.json")
    with open(report_path, "w") as f:
        json.dump(summary_report, f, indent=2)
    print(f"[OK] Saved benchmark metrics report: {report_path}")
    
    print("\n================================================================================")
    print("MODEL BENCHMARK COMPARISON TABLE")
    print("================================================================================")
    print(f"{'Model':<24} | {'Accuracy':<8} | {'Precision':<9} | {'Recall':<7} | {'F1-Score':<8} | {'ROC-AUC':<8} | {'FNR (Missed)':<12}")
    print("-" * 90)
    for m_key, m_res in results.items():
        print(f"{m_key:<24} | {m_res['accuracy']:<8} | {m_res['precision']:<9} | {m_res['recall']:<7} | {m_res['f1_score']:<8} | {str(m_res['roc_auc']):<8} | {m_res['false_negative_rate']:<12}")
    print("================================================================================")

if __name__ == "__main__":
    main()
