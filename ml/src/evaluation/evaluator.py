"""
ml/src/evaluation/evaluator.py
Flowshield — Model Evaluator & Safety Gate Validator
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from ..utils.paths import MLPaths
from ..utils.logger import get_logger
from ..features.feature_definitions import CANONICAL_FEATURE_NAMES, TARGET_COLUMN
from .metrics import calculate_classification_metrics

logger = get_logger("flowshield.evaluation.evaluator")


class ModelEvaluator:
    """Evaluates trained pipelines against locked test sets and safety gates."""

    RECALL_GATE = 0.85
    ROC_AUC_GATE = 0.90
    ECE_GATE = 0.05

    def __init__(self, test_df: Optional[pd.DataFrame] = None):
        if test_df is not None:
            self.test_df = test_df
        else:
            test_path = MLPaths.DATA_SPLITS_DIR / "final_test_locked.csv"
            if test_path.exists():
                self.test_df = pd.read_csv(test_path)
            else:
                self.test_df = None

    def evaluate(
        self,
        base_model: Any,
        calibrator: Any,
        preprocessor: Any,
        threshold: float = 0.08,
        save_report: bool = True,
        report_name: str = "model_evaluation_report.json",
    ) -> Dict[str, Any]:
        """Runs full evaluation on the test set."""
        if self.test_df is None or len(self.test_df) == 0:
            raise ValueError("Test set is empty or not loaded.")

        X_test = self.test_df[CANONICAL_FEATURE_NAMES]
        y_test = self.test_df[TARGET_COLUMN].values

        X_test_scaled = preprocessor.transform(X_test)
        y_probs = calibrator.predict_proba(X_test_scaled)[:, 1]

        metrics = calculate_classification_metrics(
            y_true=y_test,
            y_prob=y_probs,
            threshold=threshold,
        )

        passed_recall = metrics["recall"] >= self.RECALL_GATE
        passed_auc = metrics["roc_auc"] >= self.ROC_AUC_GATE
        passed_ece = metrics["ece"] <= self.ECE_GATE

        all_passed = passed_recall and passed_auc and passed_ece

        result = {
            "metrics": metrics,
            "safety_gates": {
                "catastrophe_recall_passed": passed_recall,
                "roc_auc_passed": passed_auc,
                "ece_passed": passed_ece,
                "all_gates_passed": all_passed,
            },
            "gate_thresholds": {
                "min_recall": self.RECALL_GATE,
                "min_roc_auc": self.ROC_AUC_GATE,
                "max_ece": self.ECE_GATE,
            },
            "dataset_info": {
                "test_samples": len(self.test_df),
                "flood_events": int(np.sum(y_test)),
                "non_flood_events": int(len(y_test) - np.sum(y_test)),
            },
        }

        if save_report:
            reports_dir = MLPaths.REPORTS_DIR
            reports_dir.mkdir(parents=True, exist_ok=True)
            report_path = reports_dir / report_name
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            logger.info(f"Saved evaluation report to {report_path}")

        return result
