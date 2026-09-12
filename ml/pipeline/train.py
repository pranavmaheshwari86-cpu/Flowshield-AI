"""
ml/pipeline/train.py
Flowshield — Multi-Region Model Training, Calibration & Packaging Pipeline

Conducts:
1. Dataset loading and verification (from ml/data/splits/{region})
2. Leakage-safe Preprocessor Fitting (SimpleImputer + StandardScaler on train only)
3. Model Tournament (Logistic Regression, Random Forest, XGBoost)
4. Champion Model Selection (optimizing PR-AUC and Disaster Recall)
5. Post-Hoc Probability Calibration (Isotonic / Platt Sigmoid on val_cal)
6. Multi-Tier Alert Threshold Optimization (on val_tune, enforcing Recall >= 0.85)
7. Final Untouched Holdout Evaluation (on holdout split)
8. Feature Group Ablation Experiments (A–F)
9. Artifact Bundle Persistence to ml/models/flood/{region}/
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, average_precision_score, recall_score, f1_score

from ml.registry.feature_contract import (
    CANONICAL_FEATURES,
    TARGET_COLUMN,
    FEATURE_SCHEMA_VERSION,
    compute_schema_hash,
)
from ml.registry.region_resolver import SUPPORTED_REGIONS
from ml.pipeline.dataset_builder import build_region_dataset, load_region_yaml
from ml.pipeline.calibrate import calibrate_model
from ml.pipeline.threshold_optimizer import optimize_threshold
from ml.pipeline.evaluate import evaluate_model_holdout
from ml.pipeline.ablation import run_feature_ablation
from ml.registry.model_registry import model_registry
from ml.src.utils.paths import MLPaths

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("flowshield.pipeline.train")


def train_region(
    region_slug: str,
    random_seed: int = 42,
    force_rebuild_data: bool = False,
) -> Dict[str, Any]:
    """
    Executes end-to-end training and packaging for a specific region.

    Parameters
    ----------
    region_slug : str
        Slug of the target region (e.g. 'leh_ladakh', 'sikkim', etc.)
    random_seed : int
        Seed for reproducibility.
    force_rebuild_data : bool
        Whether to re-engineer features and labels from raw source.

    Returns
    -------
    dict : Summary of training run, chosen champion, and holdout metrics.
    """
    t_start = time.time()
    if region_slug not in SUPPORTED_REGIONS:
        raise ValueError(f"Unknown region '{region_slug}'. Supported: {SUPPORTED_REGIONS}")

    region_config = load_region_yaml(region_slug)
    region_display = region_config.get("region", {}).get("display_name", region_slug)
    logger.info(f"============================================================")
    logger.info(f"STARTING TRAINING PIPELINE: {region_display} ({region_slug})")
    logger.info(f"============================================================")

    # 1. Ensure directories and datasets
    MLPaths.ensure_region_dirs(region_slug)
    splits_dir = MLPaths.region_splits_dir(region_slug)
    models_dir = MLPaths.region_model_dir(region_slug)
    models_dir.mkdir(parents=True, exist_ok=True)

    train_file = splits_dir / "train_split.csv"
    val_cal_file = splits_dir / "val_cal_split.csv"
    val_tune_file = splits_dir / "val_tune_split.csv"
    holdout_file = splits_dir / "holdout_split.csv"

    if force_rebuild_data or not (train_file.exists() and val_cal_file.exists() and val_tune_file.exists() and holdout_file.exists()):
        logger.info(f"Splits missing or rebuild requested. Building dataset for {region_slug}...")
        _, (train_df, val_cal_df, val_tune_df, holdout_df) = build_region_dataset(region_slug, force_fetch=force_rebuild_data)
    else:
        logger.info(f"Loading existing splits from {splits_dir}")
        train_df = pd.read_csv(train_file)
        val_cal_df = pd.read_csv(val_cal_file)
        val_tune_df = pd.read_csv(val_tune_file)
        holdout_df = pd.read_csv(holdout_file)

    logger.info(f"Samples: Train={len(train_df)}, ValCal={len(val_cal_df)}, ValTune={len(val_tune_df)}, Holdout={len(holdout_df)}")

    # 2. Preprocessing pipeline (Fit on train ONLY - Zero leakage)
    X_train_raw = train_df[CANONICAL_FEATURES]
    y_train = train_df[TARGET_COLUMN].values

    preprocessor = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    X_train_scaled = preprocessor.fit_transform(X_train_raw)

    # Transform validation sets
    X_val_tune_raw = val_tune_df[CANONICAL_FEATURES]
    X_val_tune_scaled = preprocessor.transform(X_val_tune_raw)
    y_val_tune = val_tune_df[TARGET_COLUMN].values

    # Class balance calculation
    n_pos = int(np.sum(y_train))
    n_neg = len(y_train) - n_pos
    pos_weight = float(n_neg / max(n_pos, 1))
    logger.info(f"Class distribution (Train): Positive={n_pos}, Negative={n_neg} (Ratio={pos_weight:.2f}:1)")

    # 3. Model Tournament
    candidates = {}
    tournament_results = {}

    # Candidate 1: Logistic Regression (Calibrated, interpretable linear)
    lr = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=random_seed, C=1.0)
    candidates["logistic_regression"] = lr

    # Candidate 2: Random Forest (Non-linear bagging ensemble)
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_leaf=4,
        class_weight="balanced",
        random_state=random_seed,
        n_jobs=-1,
    )
    candidates["random_forest"] = rf

    # Candidate 3: XGBoost (Gradient boosting)
    xgb = XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        scale_pos_weight=min(pos_weight, 15.0),
        subsample=0.85,
        colsample_bytree=0.85,
        eval_metric="logloss",
        random_state=random_seed,
        n_jobs=-1,
    )
    candidates["xgboost"] = xgb

    best_score = -1.0
    champion_name = "logistic_regression"
    champion_model = None

    for name, model in candidates.items():
        t0 = time.time()
        model.fit(X_train_scaled, y_train)
        fit_time = time.time() - t0

        probs_val = model.predict_proba(X_val_tune_scaled)[:, 1]
        preds_val = (probs_val >= 0.15).astype(int)

        rec = float(recall_score(y_val_tune, preds_val, zero_division=0))
        f1 = float(f1_score(y_val_tune, preds_val, zero_division=0))
        roc_auc = float(roc_auc_score(y_val_tune, probs_val)) if len(set(y_val_tune)) > 1 else 0.5
        pr_auc = float(average_precision_score(y_val_tune, probs_val)) if len(set(y_val_tune)) > 1 else 0.0

        # Tournament score prioritizes PR-AUC (dealing with severe class imbalance) + Recall
        tournament_score = (pr_auc * 0.6) + (rec * 0.4)
        tournament_results[name] = {
            "fit_time_sec": round(fit_time, 3),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "recall_at_0.15": round(rec, 4),
            "f1_score": round(f1, 4),
            "tournament_score": round(tournament_score, 4),
        }

        logger.info(f"Tournament [{name}]: PR-AUC={pr_auc:.4f}, Recall={rec:.4f}, ROC-AUC={roc_auc:.4f}")

        if tournament_score > best_score:
            best_score = tournament_score
            champion_name = name
            champion_model = model

    logger.info(f"Champion selected: '{champion_name}' with tournament score {best_score:.4f}")

    # Build full pipeline wrapper for champion
    champion_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", champion_model),
    ])

    # 4. Calibration on val_cal
    logger.info("Calibrating champion probabilities on val_cal split...")
    calibrator, cal_method, cal_metrics = calibrate_model(
        champion_pipeline,
        val_cal_df=val_cal_df,
        val_tune_df=val_tune_df,
        preferred_methods=region_config.get("model_defaults", {}).get("calibration_methods", ["isotonic", "sigmoid"]),
    )
    predictor_object = calibrator if calibrator is not None else champion_pipeline

    # 5. Threshold Optimization on val_tune
    logger.info("Optimizing decision thresholds on val_tune split...")
    recall_bar = float(region_config.get("model_defaults", {}).get("recall_bar", 0.85))
    fpr_bar = float(region_config.get("model_defaults", {}).get("fpr_bar", 0.15))
    thresholds_dict = optimize_threshold(
        model_or_calibrator=predictor_object,
        val_tune_df=val_tune_df,
        recall_bar=recall_bar,
        fpr_bar=fpr_bar,
    )

    # 6. Untouched Holdout Evaluation
    logger.info("Evaluating calibrated model on untouched holdout split...")
    eval_report = evaluate_model_holdout(
        model_or_calibrator=predictor_object,
        holdout_df=holdout_df,
        thresholds=thresholds_dict,
        region_slug=region_slug,
        model_name=champion_name,
    )

    # 7. Feature Group Ablation Study
    logger.info("Running feature group ablation study (Exp A-F)...")
    ablation_report = run_feature_ablation(train_df, holdout_df, random_state=random_seed)

    # 8. Feature Importances
    feat_imp = []
    if hasattr(champion_model, "feature_importances_"):
        imps = champion_model.feature_importances_
        for f, imp in zip(CANONICAL_FEATURES, imps):
            feat_imp.append({"feature": f, "importance": round(float(imp), 4)})
    elif hasattr(champion_model, "coef_"):
        coefs = np.abs(champion_model.coef_[0])
        total_coef = np.sum(coefs) if np.sum(coefs) > 0 else 1.0
        for f, c in zip(CANONICAL_FEATURES, coefs):
            feat_imp.append({"feature": f, "importance": round(float(c / total_coef), 4)})
    feat_imp = sorted(feat_imp, key=lambda x: x["importance"], reverse=True)

    # 9. Save standardized artifact bundle
    model_version = f"flowshield-{region_slug}-{champion_name}-v3-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    timestamp_utc = datetime.now(timezone.utc).isoformat()

    # Save model
    joblib.dump(champion_model, models_dir / "model.joblib")
    joblib.dump(preprocessor, models_dir / "preprocessor.joblib")
    if calibrator is not None:
        joblib.dump(calibrator, models_dir / "calibrator.joblib")
    elif (models_dir / "calibrator.joblib").exists():
        (models_dir / "calibrator.joblib").unlink()

    # Save thresholds.json
    with open(models_dir / "thresholds.json", "w", encoding="utf-8") as f:
        json.dump(thresholds_dict, f, indent=2)

    # Save feature_schema.json
    schema_info = {
        "schema_version": FEATURE_SCHEMA_VERSION,
        "schema_hash": compute_schema_hash(),
        "canonical_features": CANONICAL_FEATURES,
        "target_column": TARGET_COLUMN,
        "feature_count": len(CANONICAL_FEATURES),
        "region": region_slug,
        "feature_importances": feat_imp,
    }
    with open(models_dir / "feature_schema.json", "w", encoding="utf-8") as f:
        json.dump(schema_info, f, indent=2)

    # Save evaluation_report.json
    with open(models_dir / "evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    # Save training_manifest.json
    training_manifest = {
        "region_slug": region_slug,
        "region_display_name": region_display,
        "model_version": model_version,
        "trained_at_utc": timestamp_utc,
        "random_seed": random_seed,
        "sample_counts": {
            "train": len(train_df),
            "val_cal": len(val_cal_df),
            "val_tune": len(val_tune_df),
            "holdout": len(holdout_df),
        },
        "positive_flood_counts": {
            "train": int(train_df[TARGET_COLUMN].sum()),
            "val_cal": int(val_cal_df[TARGET_COLUMN].sum()),
            "val_tune": int(val_tune_df[TARGET_COLUMN].sum()),
            "holdout": int(holdout_df[TARGET_COLUMN].sum()),
        },
        "tournament": tournament_results,
        "selected_champion": champion_name,
        "calibration": cal_metrics,
        "ablation_summary": ablation_report,
        "duration_seconds": round(time.time() - t_start, 2),
    }
    with open(models_dir / "training_manifest.json", "w", encoding="utf-8") as f:
        json.dump(training_manifest, f, indent=2)

    # Save metadata.json
    metadata = {
        "model_version": model_version,
        "region": region_slug,
        "algorithm": champion_name,
        "production_status": eval_report["production_status"],
        "status_reason": eval_report["status_reason"],
        "calibration_method": cal_method,
        "selected_threshold": thresholds_dict["selected_threshold"],
        "holdout_recall": eval_report["metrics"]["recall"],
        "holdout_roc_auc": eval_report["metrics"]["roc_auc"],
        "holdout_f1": eval_report["metrics"]["f1_score"],
        "holdout_brier_score": eval_report["metrics"]["brier_score"],
        "trained_at_utc": timestamp_utc,
    }
    with open(models_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Evict registry cache to ensure instant live reloading
    model_registry.evict(region_slug)

    logger.info(f"Artifacts successfully packaged to: {models_dir}")
    logger.info(f"TRAINING COMPLETE FOR {region_slug}. Status: {eval_report['production_status']}")

    return {
        "region": region_slug,
        "status": eval_report["production_status"],
        "champion": champion_name,
        "metrics": eval_report["metrics"],
        "threshold": thresholds_dict["selected_threshold"],
        "artifacts_dir": str(models_dir),
    }


def main():
    parser = argparse.ArgumentParser(description="Train Flowshield regional flood model")
    parser.add_argument("--region", type=str, required=True, help="Region slug (e.g. leh_ladakh)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--rebuild-data", action="store_true", help="Force rebuild dataset")
    args = parser.parse_args()

    result = train_region(args.region, random_seed=args.seed, force_rebuild_data=args.rebuild_data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
