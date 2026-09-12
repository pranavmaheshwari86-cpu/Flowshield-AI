"""
ml/scripts/run_pipeline.py
Flowshield — Authoritative End-to-End ML Pipeline Orchestrator (v2.5)

Runs the complete certified lifecycle:
INGEST -> VALIDATE -> FEATURES -> SPLIT -> TRAIN -> CALIBRATE -> EVALUATE -> PROMOTE
"""

import sys
from pathlib import Path
import pandas as pd
import joblib

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.src.utils.paths import MLPaths
from ml.src.utils.logger import get_logger
from ml.src.utils.seed import set_seed, DEFAULT_RANDOM_SEED
from ml.src.data.loader import load_processed_hydrology_data, load_splits
from ml.src.data.validator import validate_feature_ranges
from ml.src.features.feature_definitions import CANONICAL_FEATURE_NAMES, TARGET_COLUMN
from ml.src.models.train import train_production_champion
from ml.src.models.registry import generate_manifest
from ml.src.evaluation.evaluator import ModelEvaluator

logger = get_logger("flowshield.pipeline.orchestrator")


def run_full_pipeline(seed: int = DEFAULT_RANDOM_SEED) -> bool:
    """Executes the complete unified pipeline."""
    set_seed(seed)
    print("\n" + "=" * 65)
    print("   FLOWSHIELD UNIFIED ML PIPELINE EXECUTION (v2.5)")
    print("=" * 65 + "\n")

    # Step 1: Ingest & Validate
    logger.info("[STEP 1/6] Ingesting real baseline hydrology dataset...")
    df = load_processed_hydrology_data()
    logger.info(f"Loaded {len(df)} records from processed hydrology data.")

    val_res = validate_feature_ranges(df)
    if not val_res["is_valid"]:
        logger.warning(f"Data validation identified warnings: {val_res['errors']}")
    else:
        logger.info("Physical range validation: PASSED (100% physically sound).")

    # Step 2: Feature Verification
    logger.info("[STEP 2/6] Verifying canonical 15-feature contract...")
    missing_feats = [f for f in CANONICAL_FEATURE_NAMES if f not in df.columns]
    if missing_feats:
        logger.error(f"Missing canonical features: {missing_feats}")
        return False
    logger.info(f"All {len(CANONICAL_FEATURE_NAMES)} canonical features confirmed.")

    # Step 3: Load Data Splits
    logger.info("[STEP 3/6] Loading stratified chronological splits...")
    splits = load_splits(as_dict=True)
    train_df = splits["train"]
    val_cal_df = splits["val_cal"]
    val_tune_df = splits["val_tune"]
    test_df = splits["test"]
    logger.info(f"Splits loaded: Train={len(train_df)}, Val-Cal={len(val_cal_df)}, Val-Tune={len(val_tune_df)}, Test={len(test_df)}")

    # Step 4: Train & Calibrate
    logger.info("[STEP 4/6] Training production champion and fitting isotonic calibrator...")
    base_model, calibrator, preprocessor = train_production_champion(
        train_df=train_df,
        cal_df=val_cal_df,
        seed=seed,
    )

    # Step 5: Evaluate on Locked Test Set
    logger.info("[STEP 5/6] Evaluating on locked July 2023 catastrophe test set...")
    evaluator = ModelEvaluator(test_df=test_df)
    eval_results = evaluator.evaluate(
        base_model=base_model,
        calibrator=calibrator,
        preprocessor=preprocessor,
        threshold=0.08,
        save_report=True,
        report_name="pipeline_production_eval.json",
    )

    metrics = eval_results["metrics"]
    gates = eval_results["safety_gates"]
    recall = metrics["recall"]
    roc_auc = metrics["roc_auc"]
    ece = metrics["ece"]

    print("\n" + "-" * 50)
    print(f"  Test Catastrophe Recall : {recall * 100:.2f}% (Gate >= 85%)")
    print(f"  Test ROC-AUC            : {roc_auc:.4f} (Gate >= 0.90)")
    print(f"  Expected Calib. Error   : {ece:.4f} (Gate <= 0.05)")
    print(f"  PR-AUC                  : {metrics['pr_auc']:.4f}")
    print(f"  Brier Score             : {metrics['brier_score']:.4f}")
    print(f"  Disaster Misses (FN)    : {metrics['false_negatives']}")
    print("-" * 50 + "\n")

    # Step 6: Safety Gate Promotion
    logger.info("[STEP 6/6] Verifying safety gate and updating production registry...")
    if not gates["catastrophe_recall_passed"]:
        logger.error(f"FAILED: Model recall {recall * 100:.2f}% did not satisfy 85% safety gate.")
        return False

    prod_dir = MLPaths.MODELS_PROD_DIR
    prod_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(base_model, prod_dir / "flood_risk_champion.joblib")
    joblib.dump(calibrator, prod_dir / "flood_risk_calibrator.joblib")
    joblib.dump(preprocessor, prod_dir / "flood_risk_preprocessor.joblib")

    manifest = generate_manifest(
        model_version="2.5.0-production",
        model_family="CalibratedLogisticRegression",
        status="ACTIVE_PRODUCTION",
        metrics=metrics,
    )

    print("=" * 65)
    print("   FLOWSHIELD PIPELINE EXECUTION SUCCESSFUL")
    print(f"   Production Model Registered: {prod_dir / 'MODEL_MANIFEST.json'}")
    print("=" * 65 + "\n")
    return True


if __name__ == "__main__":
    success = run_full_pipeline()
    if not success:
        sys.exit(1)
