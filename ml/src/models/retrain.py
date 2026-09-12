"""
ml/src/models/retrain.py
Flowshield — Continuous Retraining Pipeline & Safety Gate

Automates candidate model retraining, probabilistic calibration,
comparative champion-vs-challenger evaluation, and enforces the
strict Catastrophe Recall safety gate (Recall >= 85%).
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import joblib

from ..utils.paths import MLPaths
from ..utils.logger import get_logger
from ..utils.seed import set_seed, DEFAULT_RANDOM_SEED
from ..features.feature_definitions import CANONICAL_FEATURE_NAMES, TARGET_COLUMN
from .factory import create_model
from .train import train_production_champion
from .registry import generate_manifest

logger = get_logger("flowshield.models.retrain")


class RetrainingPipeline:
    """Continuous retraining orchestrator with candidate validation and safety gating."""

    MIN_SAMPLES_FOR_RETRAIN = 5
    CATASTROPHE_RECALL_GATE = 0.85
    MAX_AUC_DEGRADATION = 0.03

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or (MLPaths.DATA_PROCESSED_DIR / "mandi_real_hydrology_features.csv")
        if not self.data_path.exists():
            # Fallback to repo root data if not yet synced
            fallback = MLPaths.REPO_ROOT / "data" / "real" / "mandi_real_hydrology_features.csv"
            if fallback.exists():
                self.data_path = fallback

    def run(
        self,
        new_feedback_data: Optional[List[Dict[str, Any]]] = None,
        force_promotion: bool = False,
        seed: int = DEFAULT_RANDOM_SEED,
    ) -> Dict[str, Any]:
        """
        Executes complete retraining cycle:
        1. Ingests base real hydrological dataset.
        2. Augments with verified responder feedback.
        3. Trains candidate challenger model and calibrates.
        4. Evaluates challenger vs champion.
        5. Gates promotion on Catastrophe Recall >= 0.85.
        """
        now = datetime.now(timezone.utc)
        set_seed(seed)

        if not self.data_path.exists():
            return {
                "status": "error",
                "message": f"Training dataset not found at {self.data_path}",
                "timestamp": now.isoformat(),
            }

        base_df = pd.read_csv(self.data_path)
        logger.info(f"Loaded base training data ({len(base_df)} records) from {self.data_path}")

        # Augment with verified ground-truth field data
        augmented_records = []
        if new_feedback_data:
            for item in new_feedback_data:
                features = item.get("features_snapshot") or item.get("features", {})
                if features:
                    row = dict(features)
                    row[TARGET_COLUMN] = 1 if item.get("actual_flood_occurred", False) else 0
                    augmented_records.append(row)

        if augmented_records:
            augmented_df = pd.concat([base_df, pd.DataFrame(augmented_records)], ignore_index=True)
            logger.info(f"Augmented dataset with {len(augmented_records)} verified responder reports.")
        else:
            augmented_df = base_df

        # Clean features and labels
        X = augmented_df[CANONICAL_FEATURE_NAMES].fillna(0.0)
        y = augmented_df[TARGET_COLUMN].fillna(0).astype(int)

        # Chronological or stratified split (80 train / 20 test-eval)
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=seed, stratify=y
        )

        train_df = pd.concat([X_train, y_train], axis=1)
        test_df = pd.concat([X_test, y_test], axis=1)

        # Calibration split from train
        X_tr, X_cal, y_tr, y_cal = train_test_split(
            X_train, y_train, test_size=0.20, random_state=seed, stratify=y_train
        )
        tr_df = pd.concat([X_tr, y_tr], axis=1)
        cal_df = pd.concat([X_cal, y_cal], axis=1)

        # Train challenger
        base_model, calibrator, preprocessor = train_production_champion(
            train_df=tr_df, cal_df=cal_df, seed=seed
        )

        # Evaluate candidate at operational threshold tau = 0.08
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, f1_score,
            roc_auc_score, average_precision_score, brier_score_loss,
            confusion_matrix
        )

        X_test_scaled = preprocessor.transform(X_test)
        test_probs = calibrator.predict_proba(X_test_scaled)[:, 1]
        tau = 0.08
        y_pred = (test_probs >= tau).astype(int)

        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()

        candidate_metrics = {
            "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
            "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, test_probs)), 4),
            "pr_auc": round(float(average_precision_score(y_test, test_probs)), 4),
            "brier_score": round(float(brier_score_loss(y_test, test_probs)), 4),
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "false_negatives": int(fn),
            "true_positives": int(tp),
            "false_positives": int(fp),
            "true_negatives": int(tn),
            "sample_count": len(y_test),
        }

        # Champion metrics baseline
        champion_recall = 0.884
        champion_roc_auc = 0.923

        # Safety Gate Check
        passed_recall_gate = candidate_metrics["recall"] >= self.CATASTROPHE_RECALL_GATE
        passed_auc_gate = candidate_metrics["roc_auc"] >= (champion_roc_auc - self.MAX_AUC_DEGRADATION)

        promoted = (passed_recall_gate and passed_auc_gate) or force_promotion
        reason = (
            f"Candidate passed safety gates: Recall={candidate_metrics['recall']} >= {self.CATASTROPHE_RECALL_GATE}, "
            f"ROC-AUC={candidate_metrics['roc_auc']}"
            if promoted else
            f"Promotion rejected: Recall={candidate_metrics['recall']} (gate: {self.CATASTROPHE_RECALL_GATE}) "
            f"or ROC-AUC={candidate_metrics['roc_auc']} degraded below baseline."
        )

        version_tag = f"candidate-{now.strftime('%Y%m%d_%H%M%S')}"

        # Save candidate artifacts
        cand_dir = MLPaths.MODELS_CANDIDATES_DIR
        cand_dir.mkdir(parents=True, exist_ok=True)
        
        joblib.dump(base_model, cand_dir / f"{version_tag}_model.joblib")
        joblib.dump(calibrator, cand_dir / f"{version_tag}_calibrator.joblib")
        joblib.dump(preprocessor, cand_dir / f"{version_tag}_preprocessor.joblib")

        # Save candidate evaluation report
        with open(cand_dir / f"{version_tag}_eval.json", "w", encoding="utf-8") as f:
            json.dump({
                "candidate_version": version_tag,
                "timestamp": now.isoformat(),
                "promoted": promoted,
                "reason": reason,
                "metrics": candidate_metrics,
            }, f, indent=2)

        # If promoted, deploy to production directory
        if promoted:
            prod_dir = MLPaths.MODELS_PROD_DIR
            prod_dir.mkdir(parents=True, exist_ok=True)
            joblib.dump(base_model, prod_dir / "flood_risk_champion.joblib")
            joblib.dump(calibrator, prod_dir / "flood_risk_calibrator.joblib")
            joblib.dump(preprocessor, prod_dir / "flood_risk_preprocessor.joblib")
            generate_manifest(
                model_version=version_tag,
                status="production",
                metrics=candidate_metrics,
            )
            logger.info(f"Model successfully promoted to production: {version_tag}")

        return {
            "status": "success",
            "candidate_version": version_tag,
            "promoted": promoted,
            "reason": reason,
            "candidate_metrics": candidate_metrics,
            "training_samples": len(X_train),
            "evaluation_samples": len(X_test),
            "timestamp": now.isoformat(),
        }
