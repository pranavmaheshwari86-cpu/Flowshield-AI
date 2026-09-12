"""
ml/pipeline/prepare_data.py
Flowshield — Multi-Region Data Preparation CLI

Builds canonical feature matrices, attaches flood labels, and generates
train/val/holdout splits for one or all supported regions.

Usage:
    python -m ml.pipeline.prepare_data --region leh_ladakh
    python -m ml.pipeline.prepare_data --all
"""

import sys
import argparse
import logging
from ml.registry.region_resolver import SUPPORTED_REGIONS
from ml.pipeline.dataset_builder import build_region_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("flowshield.pipeline.prepare_data")


def prepare_region(region_slug: str, force: bool = False):
    logger.info(f"Preparing dataset and splits for {region_slug}...")
    labeled_df, (train_df, val_cal_df, val_tune_df, holdout_df) = build_region_dataset(
        region_slug=region_slug,
        force_fetch=force,
    )
    print(
        f"[OK] {region_slug}: {len(labeled_df)} rows "
        f"(Train={len(train_df)}, ValCal={len(val_cal_df)}, ValTune={len(val_tune_df)}, Holdout={len(holdout_df)})"
    )


def main():
    parser = argparse.ArgumentParser(description="Prepare Flowshield regional data")
    parser.add_argument("--region", type=str, help="Specific region slug")
    parser.add_argument("--all", action="store_true", help="Prepare all 10 regions")
    parser.add_argument("--force", action="store_true", help="Force re-fetch/re-generation")
    args = parser.parse_args()

    if args.all:
        for r in SUPPORTED_REGIONS:
            prepare_region(r, force=args.force)
    elif args.region:
        prepare_region(args.region, force=args.force)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
