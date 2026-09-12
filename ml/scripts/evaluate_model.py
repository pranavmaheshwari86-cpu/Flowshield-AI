"""
ml/scripts/evaluate_model.py
Flowshield — CLI Script: Evaluate Model Pipeline on Locked Test Set
Usage:
    python ml/scripts/evaluate_model.py [--threshold 0.08] [--report-name evaluation_report.json]
"""

import argparse
import sys
import json
from pathlib import Path
import joblib
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.src.utils.paths import MLPaths
from ml.src.utils.logger import get_logger
from ml.src.evaluation.evaluator import ModelEvaluator

logger = get_logger("flowshield.scripts.evaluate")


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Flowshield Flood Risk Model")
    parser.add_argument("--model-path", type=str, default=None, help="Path to base model joblib")
    parser.add_argument("--calibrator-path", type=str, default=None, help="Path to calibrator joblib")
    parser.add_argument("--preprocessor-path", type=str, default=None, help="Path to preprocessor joblib")
    parser.add_argument("--test-data", type=str, default=None, help="Path to test CSV")
    parser.add_argument("--threshold", type=float, default=0.08, help="Operational threshold tau")
    parser.add_argument("--report-name", type=str, default="evaluation_report.json", help="Report filename")
    return parser.parse_args()


def main():
    args = parse_args()

    prod_dir = MLPaths.MODELS_PROD_DIR
    model_path = Path(args.model_path) if args.model_path else (prod_dir / "flood_risk_champion.joblib")
    cal_path = Path(args.calibrator_path) if args.calibrator_path else (prod_dir / "flood_risk_calibrator.joblib")
    prep_path = Path(args.preprocessor_path) if args.preprocessor_path else (prod_dir / "flood_risk_preprocessor.joblib")

    # Fallback to models/ if prod_dir artifacts not yet promoted
    if not model_path.exists():
        model_path = MLPaths.MODELS_DIR / "v2_selected_model.joblib"
    if not cal_path.exists():
        cal_path = MLPaths.MODELS_DIR / "v2_calibrator.joblib"
    if not prep_path.exists():
        prep_path = MLPaths.MODELS_DIR / "v2_preprocessor.joblib"

    logger.info(f"Evaluating model: {model_path}")
    logger.info(f"Calibrator: {cal_path}")
    logger.info(f"Preprocessor: {prep_path}")

    model = joblib.load(model_path)
    calibrator = joblib.load(cal_path)
    preprocessor = joblib.load(prep_path)

    test_path = Path(args.test_data) if args.test_data else (MLPaths.DATA_SPLITS_DIR / "final_test_locked.csv")
    test_df = pd.read_csv(test_path)

    evaluator = ModelEvaluator(test_df=test_df)
    results = evaluator.evaluate(
        base_model=model,
        calibrator=calibrator,
        preprocessor=preprocessor,
        threshold=args.threshold,
        save_report=True,
        report_name=args.report_name,
    )

    metrics = results["metrics"]
    gates = results["safety_gates"]

    print("\n" + "=" * 60)
    print("FLOWSHIELD OPERATIONAL EVALUATION RESULTS")
    print("=" * 60)
    print(f"Operational Decision Threshold (tau) : {metrics['threshold']}")
    print(f"Catastrophe Recall (Sensitivity)    : {metrics['recall'] * 100:.2f}% (Gate >= 85%: {'PASSED' if gates['catastrophe_recall_passed'] else 'FAILED'})")
    print(f"ROC-AUC                             : {metrics['roc_auc']:.4f} (Gate >= 0.90: {'PASSED' if gates['roc_auc_passed'] else 'FAILED'})")
    print(f"Expected Calibration Error (ECE)    : {metrics['ece']:.4f} (Gate <= 0.05: {'PASSED' if gates['ece_passed'] else 'FAILED'})")
    print(f"PR-AUC (Average Precision)          : {metrics['pr_auc']:.4f}")
    print(f"Brier Score                         : {metrics['brier_score']:.4f}")
    print(f"Precision                           : {metrics['precision'] * 100:.2f}%")
    print(f"F1-Score                            : {metrics['f1_score']:.4f}")
    print("-" * 60)
    print(f"True Positives  (TP) : {metrics['true_positives']}")
    print(f"False Negatives (FN) : {metrics['false_negatives']} (Disasters missed)")
    print(f"False Positives (FP) : {metrics['false_positives']} (False alerts)")
    print(f"True Negatives  (TN) : {metrics['true_negatives']}")
    print("=" * 60)
    print(f"OVERALL SAFETY GATE STATUS: {'PASSED' if gates['all_gates_passed'] else 'FAILED'}\n")


if __name__ == "__main__":
    main()
