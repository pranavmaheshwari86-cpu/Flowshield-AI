"""
Model Training & Explainability Pipeline for Flowshield
Trains XGBoost classifier on synthetic hydrology dataset.
Extracts metrics honestly without fabrication and serializes model + SHAP explainer + metadata.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from xgboost import XGBClassifier
import shap

from feature_schema import (
    FEATURE_SCHEMA,
    FEATURE_BOUNDS,
    TARGET_COLUMN,
    MODEL_VERSION_PREFIX,
    DEFAULT_SEED,
)


def compute_file_hash(filepath: str) -> str:
    """Calculates SHA256 hash of a file for provenance."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def train_pipeline(data_path: str = None, models_dir: str = None):
    curr_dir = os.path.dirname(__file__)
    if data_path is None:
        data_path = os.path.join(curr_dir, "data", "synthetic_flood_data.csv")
    if models_dir is None:
        models_dir = os.path.join(curr_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    print(f"Loading training data from: {data_path}")
    if not os.path.exists(data_path):
        from generate_data import generate_synthetic_dataset
        df = generate_synthetic_dataset(num_samples=6000, seed=DEFAULT_SEED)
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        df.to_csv(data_path, index=False)
    else:
        df = pd.read_csv(data_path)

    # 1. Validation: Verify all columns present and match schema exactly
    for col in FEATURE_SCHEMA:
        if col not in df.columns:
            raise ValueError(f"Missing required feature in training data: {col}")
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing target column: {TARGET_COLUMN}")

    # Enforce exact column order from canonical schema
    X = df[FEATURE_SCHEMA]
    y = df[TARGET_COLUMN].values

    # Check bounds
    for col in FEATURE_SCHEMA:
        b_min, b_max = FEATURE_BOUNDS[col]
        outliers = (X[col] < b_min) | (X[col] > b_max)
        if outliers.any():
            print(f"Warning: {outliers.sum()} values out of bounds for feature {col}. Clamping.")
            X[col] = X[col].clip(b_min, b_max)

    # 2. Stratified 80/20 train/test split (zero data leakage)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=DEFAULT_SEED, stratify=y
    )

    pos_count = np.sum(y_train == 1)
    neg_count = np.sum(y_train == 0)
    scale_pos_weight = float(neg_count / max(1, pos_count))

    print(f"Train samples: {len(X_train)} (Positive: {pos_count}, Negative: {neg_count})")
    print(f"Test samples: {len(X_test)} (Scale pos weight: {scale_pos_weight:.2f})")

    # 3. XGBoost Hyperparameters
    hyperparameters = {
        "max_depth": 5,
        "n_estimators": 180,
        "learning_rate": 0.08,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "scale_pos_weight": round(scale_pos_weight, 3),
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "random_state": DEFAULT_SEED,
        "n_jobs": -1,
    }

    # 4. Train Model
    print("Training XGBoost classifier...")
    model = XGBClassifier(**hyperparameters)
    model.fit(X_train, y_train)

    # 5. Evaluate on Held-Out Test Set (Honest Real Metrics)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    cm = confusion_matrix(y_test, y_pred).tolist()

    print("\n--- Model Evaluation Results (Test Set) ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print(f"Confusion Matrix: {cm}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred))

    # 6. SHAP Explainer
    print("Fitting SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(model)
    shap_sample = X_test.iloc[:200]
    shap_values = explainer.shap_values(shap_sample)
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    shap_ranking = [
        FEATURE_SCHEMA[i]
        for i in np.argsort(mean_abs_shap)[::-1]
    ]
    print(f"Top SHAP features: {shap_ranking[:5]}")

    # 7. Model Versioning & Provenance Metadata
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    model_version = f"{MODEL_VERSION_PREFIX}-{timestamp_str}"
    data_hash = compute_file_hash(data_path)

    metadata = {
        "model_version": model_version,
        "model_type": "XGBClassifier",
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "random_seed": DEFAULT_SEED,
        "feature_schema": FEATURE_SCHEMA,
        "feature_schema_hash": hashlib.sha256(
            json.dumps(FEATURE_SCHEMA).encode()
        ).hexdigest(),
        "hyperparameters": hyperparameters,
        "dataset_metadata": {
            "source": "Flowshield Physically-Correlated Synthetic Hydrology Dataset",
            "is_synthetic": True,
            "data_hash": data_hash,
            "total_samples": len(df),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "test_positive_rate": round(float(np.mean(y_test)), 3),
            "disclosure": "Demonstration synthetic data modeled on Himalayan river valley parameters. Not intended for real-world unverified emergency deployment.",
        },
        "evaluation_metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "confusion_matrix": cm,
        },
        "shap_importance_ranking": shap_ranking,
        "shap_expected_value": float(explainer.expected_value),
    }

    # 8. Save Artifacts
    model_out = os.path.join(models_dir, "xgb_flood_model.joblib")
    meta_out = os.path.join(models_dir, "model_metadata.json")

    joblib.dump(model, model_out)
    with open(meta_out, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nModel artifact saved to: {model_out}")
    print(f"Metadata saved to: {meta_out}")
    return metadata


if __name__ == "__main__":
    train_pipeline()
