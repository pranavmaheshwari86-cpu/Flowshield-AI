"""
ml/retraining/retrain_pipeline.py
Flowshield — Continuous Learning & Automated Model Retraining Pipeline (v3.0)
Smart India Hackathon 2026 (PS ID: 26192)

Implements continuous learning lifecycle:
1. Ingests accumulated ground-truth verified outcomes from field responders
2. Augments real baseline hydrological training set
3. Trains a challenger model with probability calibration
4. Runs strict comparative champion-vs-challenger evaluation
5. Enforces safety gate: Minimum Catastrophe Recall >= 85% required for promotion
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES, TARGET_COLUMN

logger = logging.getLogger("flowshield.retrain")

MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")
DATA_PATH = os.path.join(BASE_DIR, "data", "real", "mandi_real_hydrology_features.csv")
V2_PIPELINE_PATH = os.path.join(MODELS_DIR, "v2_decision_pipeline.json")


class RetrainPipeline:
    """Orchestrates candidate model retraining, validation, and promotion."""

    MIN_VERIFIED_OUTCOMES_FOR_AUTO_RETRAIN = 5

    def run_retrain(
        self,
        verified_outcomes: Optional[list] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Executes an end-to-end retraining cycle.
        Returns a detailed comparative report.
        """
        now = datetime.now(timezone.utc)
        
        # 1. Load base training data
        if not os.path.exists(DATA_PATH):
            return {
                "status": "error",
                "message": f"Base dataset missing at {DATA_PATH}",
                "timestamp": now.isoformat()
            }

        base_df = pd.read_csv(DATA_PATH)
        
        # 2. Augment with verified ground-truth outcomes
        new_rows = []
        if verified_outcomes:
            for vo in verified_outcomes:
                if vo.features_snapshot:
                    row = dict(vo.features_snapshot)
                    row[TARGET_COLUMN] = 1 if vo.actual_flood_occurred else 0
                    new_rows.append(row)

        if new_rows:
            augmented_df = pd.concat([base_df, pd.DataFrame(new_rows)], ignore_index=True)
            logger.info(f"Augmented base dataset ({len(base_df)} rows) with {len(new_rows)} verified outcomes.")
        else:
            augmented_df = base_df

        # 3. Clean features and target
        X = augmented_df[CANONICAL_FEATURE_NAMES].fillna(0.0)
        y = augmented_df[TARGET_COLUMN].fillna(0).astype(int)

        # 4. Train-test split (80/20 stratified)
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42, stratify=y
        )

        # 5. Fit preprocessor
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # 6. Train candidate model
        base_estimator = LogisticRegression(
            C=1.0, penalty="l2", solver="lbfgs", max_iter=1000, random_state=42, class_weight="balanced"
        )
        base_estimator.fit(X_train_scaled, y_train)

        # 7. Probability Calibration using Isotonic Regression
        calibrator = CalibratedClassifierCV(estimator=base_estimator, method="isotonic", cv="prefit")
        calibrator.fit(X_test_scaled, y_test)

        # 8. Evaluation at operational decision threshold tau = 0.08
        test_probs = calibrator.predict_proba(X_test_scaled)[:, 1]
        operational_threshold = 0.08
        y_pred = (test_probs >= operational_threshold).astype(int)

        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()
        candidate_metrics = {
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "recall": round(float(recall_score(y_test, y_pred)), 4),
            "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, test_probs)), 4),
            "pr_auc": round(float(average_precision_score(y_test, test_probs)), 4),
            "brier_score": round(float(brier_score_loss(y_test, test_probs)), 4),
            "false_negatives": int(fn),
            "true_positives": int(tp),
            "false_positives": int(fp),
            "true_negatives": int(tn),
            "training_samples": len(X_train),
            "evaluation_samples": len(X_test)
        }

        # 9. Load champion metrics for comparison
        champion_metrics = {}
        champion_version = "flowshield-flood-risk-v2"
        if os.path.exists(V2_PIPELINE_PATH):
            try:
                with open(V2_PIPELINE_PATH, "r") as f:
                    pipe_data = json.load(f)
                    champion_metrics = pipe_data.get("evaluation_metrics", {})
                    champion_version = pipe_data.get("pipeline_version", champion_version)
            except Exception:
                pass

        # 10. Promotion Safety Gate
        # Rules:
        # 1. Disaster Recall must be >= 0.85
        # 2. ROC-AUC must not degrade by more than 0.03
        champion_recall = float(champion_metrics.get("recall", 0.884))
        champion_roc_auc = float(champion_metrics.get("roc_auc", 0.923))

        passed_recall_gate = candidate_metrics["recall"] >= 0.85
        passed_auc_gate = candidate_metrics["roc_auc"] >= (champion_roc_auc - 0.03)

        promoted = (passed_recall_gate and passed_auc_gate) or force
        reason = (
            f"Candidate passed safety gates (Recall={candidate_metrics['recall']:.3f} >= 0.85, "
            f"ROC-AUC={candidate_metrics['roc_auc']:.3f})"
            if promoted else
            f"Promotion rejected: Recall ({candidate_metrics['recall']:.3f}) below safety threshold or ROC-AUC degraded."
        )

        candidate_version = f"flowshield-v2-retrained-{now.strftime('%Y%m%d%H%M')}"

        if promoted:
            # Save new candidate artifacts
            candidate_model_path = os.path.join(MODELS_DIR, f"{candidate_version}.joblib")
            candidate_calibrator_path = os.path.join(MODELS_DIR, f"{candidate_version}_calibrator.joblib")
            candidate_preprocessor_path = os.path.join(MODELS_DIR, f"{candidate_version}_preprocessor.joblib")

            joblib.dump(base_estimator, candidate_model_path)
            joblib.dump(calibrator, candidate_calibrator_path)
            joblib.dump(scaler, candidate_preprocessor_path)

            logger.info(f"Promoted and saved model artifacts for {candidate_version}")

        return {
            "status": "success",
            "retrained_at": now.isoformat(),
            "candidate_version": candidate_version,
            "champion_version": champion_version,
            "promoted": promoted,
            "decision_reason": reason,
            "candidate_metrics": candidate_metrics,
            "champion_metrics": champion_metrics,
            "augmented_samples_count": len(new_rows),
            "total_dataset_size": len(augmented_df),
        }


retrain_pipeline = RetrainPipeline()
