"""
ml/scripts/rollback_model.py
Flowshield — CLI Script: Automated Production Model Rollback
Usage:
    python ml/scripts/rollback_model.py [--backup-dir <path_to_backup>]
"""

import argparse
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.src.utils.paths import MLPaths
from ml.src.utils.logger import get_logger
from ml.src.models.registry import generate_manifest

logger = get_logger("flowshield.scripts.rollback")


def parse_args():
    parser = argparse.ArgumentParser(description="Rollback Production Model to Previous Safe Baseline")
    parser.add_argument("--backup-dir", type=str, default=None, help="Explicit path to backup directory")
    return parser.parse_args()


def main():
    args = parse_args()
    prod_dir = MLPaths.MODELS_PROD_DIR
    backup_base = MLPaths.MODELS_BACKUP_DIR

    target_backup = None
    if args.backup_dir:
        target_backup = Path(args.backup_dir)
    else:
        # Find latest backup subfolder
        subdirs = [d for d in backup_base.iterdir() if d.is_dir()]
        if subdirs:
            target_backup = sorted(subdirs, key=lambda d: d.stat().st_mtime, reverse=True)[0]
        else:
            # Fallback to base backup dir files
            target_backup = backup_base

    if not target_backup.exists():
        logger.error(f"Backup target does not exist: {target_backup}")
        sys.exit(1)

    logger.info(f"Restoring production artifacts from backup: {target_backup}")

    restored = 0
    # Map of backup artifacts
    artifact_mappings = [
        ("flood_risk_champion.joblib", "flood_risk_champion.joblib"),
        ("flood_risk_calibrator.joblib", "flood_risk_calibrator.joblib"),
        ("flood_risk_preprocessor.joblib", "flood_risk_preprocessor.joblib"),
        ("v2_selected_model.joblib", "flood_risk_champion.joblib"),
        ("v2_calibrator.joblib", "flood_risk_calibrator.joblib"),
        ("v2_preprocessor.joblib", "flood_risk_preprocessor.joblib"),
    ]

    for src_name, dst_name in artifact_mappings:
        src = target_backup / src_name
        if src.exists():
            dst = prod_dir / dst_name
            shutil.copy2(src, dst)
            logger.info(f"Restored: {src_name} -> {dst_name}")
            restored += 1

    if restored == 0:
        logger.error("No valid model artifacts found in backup directory to restore!")
        sys.exit(1)

    manifest = generate_manifest(
        model_version="rollback-safe-baseline",
        status="ROLLED_BACK",
    )
    logger.info("Successfully executed production model rollback.")


if __name__ == "__main__":
    main()
