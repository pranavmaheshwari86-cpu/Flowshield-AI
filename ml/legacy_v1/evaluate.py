"""
Evaluation and Audit Tool for Flowshield ML Models (Legacy V1 Synthetic Audit)
NOTE: This script audits the historical V1 synthetic model.
For production V2 model evaluation, see `ml/evaluation/evaluate_flood_model.py`
and `ml/training/study_model_selection.py`.
"""

import os
import json
import joblib
import warnings
import numpy as np
import pandas as pd

warnings.warn(
    "ml/evaluate.py is an archived V1 synthetic model evaluation tool. "
    "For production V2 evaluation, use ml/evaluation/evaluate_flood_model.py.",
    DeprecationWarning,
    stacklevel=2,
)

try:
    from ml.legacy_v1.feature_schema import FEATURE_SCHEMA, FEATURE_BOUNDS
except ImportError:
    from feature_schema import FEATURE_SCHEMA, FEATURE_BOUNDS


def evaluate_model(models_dir: str = None, test_data_path: str = None):
    curr_dir = os.path.dirname(__file__)
    if models_dir is None:
        models_dir = os.path.join(curr_dir, "models")
    if test_data_path is None:
        test_data_path = os.path.join(curr_dir, "data", "synthetic_flood_data.csv")

    model_file = os.path.join(models_dir, "xgb_flood_model.joblib")
    meta_file = os.path.join(models_dir, "model_metadata.json")

    if not os.path.exists(model_file) or not os.path.exists(meta_file):
        raise FileNotFoundError("Trained model or metadata not found. Run train.py first.")

    with open(meta_file, "r") as f:
        metadata = json.load(f)

    # Feature schema consistency check
    assert metadata["feature_schema"] == FEATURE_SCHEMA, "Feature schema mismatch detected!"

    model = joblib.load(model_file)
    df = pd.read_csv(test_data_path)
    X = df[FEATURE_SCHEMA]

    probs = model.predict_proba(X)[:, 1]
    preds = model.predict(X)

    print("=== Flowshield Model Audit ===")
    print(f"Model Version: {metadata['model_version']}")
    print(f"Training Time: {metadata['training_timestamp']}")
    print(f"Total Evaluated: {len(X)}")
    print(f"Mean Predicted Probability: {np.mean(probs):.3f}")
    print(f"Min / Max Probability: {np.min(probs):.3f} / {np.max(probs):.3f}")
    print(f"Recorded Test ROC-AUC: {metadata['evaluation_metrics']['roc_auc']}")
    print(f"Recorded Test F1: {metadata['evaluation_metrics']['f1_score']}")
    print(f"Top 3 SHAP Features: {metadata['shap_importance_ranking'][:3]}")

    return {
        "status": "VALID",
        "model_version": metadata["model_version"],
        "metrics": metadata["evaluation_metrics"],
    }


if __name__ == "__main__":
    evaluate_model()
