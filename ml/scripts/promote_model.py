"""
ml/scripts/promote_model.py
Flowshield — CLI Script: Model Promotion & Deployment Gate
Usage:
    python ml/scripts/promote_model.py --candidate-tag candidate_cli [--force]
"""

import argparse
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone
import joblib

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.src.utils.paths import MLPaths
from ml.src.utils.logger import get_logger
from ml.src.models.registry import generate_manifest
from ml.src.evaluation.evaluator import ModelEvaluator
import pandas as pd

logger = get_logger("flowshield.scripts.promote")


def parse_args():
    parser = argparse.ArgumentParser(description="Promote Candidate Model to Production")
    parser.add_argument("--candidate-tag", type=str, required=True, help="Artifact prefix in ml/models/candidates/")
    parser.add_argument("--force", action="store_true", help="Bypass safety gate check (requires manual override flag)")
    return parser.parse_args()


def main():
    args = parse_args()
    cand_dir = MLPaths.MODELS_CANDIDATES_DIR
    prod_dir = MLPaths.MODELS_PROD_DIR
    backup_dir = MLPaths.MODELS_BACKUP_DIR

    cand_model = cand_dir / f"{args.candidate_tag}_model.joblib"
    cand_cal = cand_dir / f"{args.candidate_tag}_calibrator.joblib"
    cand_prep = cand_dir / f"{args.candidate_tag}_preprocessor.joblib"

    if not cand_model.exists() or not cand_cal.exists() or not cand_prep.exists():
        logger.error(f"Candidate artifacts not found for tag: {args.candidate_tag}")
        sys.exit(1)

    # 1. Validation check
    logger.info("Running pre-promotion validation against locked test set...")
    test_path = MLPaths.DATA_SPLITS_DIR / "final_test_locked.csv"
    test_df = pd.read_csv(test_path)
    evaluator = ModelEvaluator(test_df=test_df)

    eval_result = evaluator.evaluate(
        base_model=joblib.load(cand_model),
        calibrator=joblib.load(cand_cal),
        preprocessor=joblib.load(cand_prep),
        save_report=False,
    )

    passed_recall = eval_result["safety_gates"]["catastrophe_recall_passed"]
    recall = eval_result["metrics"]["recall"]

    if not passed_recall and not args.force:
        logger.error(f"PROMOTION BLOCKED: Catastrophe Recall {recall * 100:.2f}% is below 85.0% gate!")
        sys.exit(1)

    # 2. Backup existing production model
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_tag_dir = backup_dir / f"backup_{timestamp}"
    backup_tag_dir.mkdir(parents=True, exist_ok=True)

    for item in ["flood_risk_champion.joblib", "flood_risk_calibrator.joblib", "flood_risk_preprocessor.joblib", "MODEL_MANIFEST.json"]:
        p = prod_dir / item
        if p.exists():
            shutil.copy2(p, backup_tag_dir / item)
    logger.info(f"Existing production artifacts backed up to: {backup_tag_dir}")

    # 3. Promote candidate artifacts
    prod_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cand_model, prod_dir / "flood_risk_champion.joblib")
    shutil.copy2(cand_cal, prod_dir / "flood_risk_calibrator.joblib")
    shutil.copy2(cand_prep, prod_dir / "flood_risk_preprocessor.joblib")

    # 4. Generate new manifest
    manifest = generate_manifest(
        model_version=f"candidate-{args.candidate_tag}",
        model_family="CalibratedLogisticRegression",
        status="production",
        metrics=eval_result["metrics"],
    )

    logger.info(f"Successfully promoted candidate '{args.candidate_tag}' to production!")
    logger.info(f"New production manifest written: {prod_dir / 'MODEL_MANIFEST.json'}")


if __name__ == "__main__":
    main()
