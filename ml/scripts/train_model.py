"""
ml/scripts/train_model.py
Flowshield — CLI Script: Train Flood Risk Candidate Model
Usage:
    python ml/scripts/train_model.py [--model-type logistic_regression] [--seed 26192]
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import joblib

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.src.utils.paths import MLPaths
from ml.src.utils.logger import get_logger
from ml.src.utils.seed import set_seed, DEFAULT_RANDOM_SEED
from ml.src.features.feature_definitions import CANONICAL_FEATURE_NAMES, TARGET_COLUMN
from ml.src.models.train import train_production_champion
from ml.src.models.factory import create_model

logger = get_logger("flowshield.scripts.train")


def parse_args():
    parser = argparse.ArgumentParser(description="Train Flowshield Flood Risk Model")
    parser.add_argument("--model-type", type=str, default="logistic_regression", help="Model family")
    parser.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED, help="Random seed")
    parser.add_argument("--train-data", type=str, default=None, help="Path to training CSV")
    parser.add_argument("--cal-data", type=str, default=None, help="Path to calibration CSV")
    parser.add_argument("--output-tag", type=str, default="candidate_cli", help="Output artifact tag")
    return parser.parse_args()


def main():
    args = parse_args()
    set_seed(args.seed)
    logger.info(f"Starting model training pipeline with seed={args.seed}...")

    train_path = Path(args.train_data) if args.train_data else (MLPaths.DATA_SPLITS_DIR / "train_split.csv")
    cal_path = Path(args.cal_data) if args.cal_data else (MLPaths.DATA_SPLITS_DIR / "val_cal_split.csv")

    if not train_path.exists():
        logger.error(f"Train split not found at {train_path}")
        sys.exit(1)
    if not cal_path.exists():
        logger.error(f"Calibration split not found at {cal_path}")
        sys.exit(1)

    train_df = pd.read_csv(train_path)
    cal_df = pd.read_csv(cal_path)

    logger.info(f"Loaded {len(train_df)} train records, {len(cal_df)} calibration records.")

    base_model, calibrator, preprocessor = train_production_champion(
        train_df=train_df,
        cal_df=cal_df,
        seed=args.seed,
    )

    out_dir = MLPaths.MODELS_CANDIDATES_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    model_path = out_dir / f"{args.output_tag}_model.joblib"
    cal_path_out = out_dir / f"{args.output_tag}_calibrator.joblib"
    prep_path_out = out_dir / f"{args.output_tag}_preprocessor.joblib"

    joblib.dump(base_model, model_path)
    joblib.dump(calibrator, cal_path_out)
    joblib.dump(preprocessor, prep_path_out)

    logger.info(f"Successfully saved candidate model to: {model_path}")
    logger.info(f"Successfully saved calibrator to: {cal_path_out}")
    logger.info(f"Successfully saved preprocessor to: {prep_path_out}")


if __name__ == "__main__":
    main()
