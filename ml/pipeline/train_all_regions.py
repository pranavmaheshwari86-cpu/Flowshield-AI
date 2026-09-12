"""
ml/pipeline/train_all_regions.py
Flowshield — Batch Multi-Region Training & Packaging Orchestrator

Iterates through all 10 target regions, runs the full training, calibration,
threshold optimization, and evaluation pipeline, and produces a consolidated
multi-region governance summary.

Usage:
    python -m ml.pipeline.train_all_regions
"""

import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from ml.registry.region_resolver import SUPPORTED_REGIONS
from ml.pipeline.train import train_region

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("flowshield.pipeline.train_all_regions")

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def train_all(random_seed: int = 42, force_rebuild: bool = False) -> Dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    print("\n" + "=" * 80)
    print("FLOWSHIELD — BATCH MULTI-REGION ML TRAINING & GOVERNANCE ORCHESTRATOR")
    print(f"Targeting {len(SUPPORTED_REGIONS)} Regions | Seed={random_seed}")
    print("=" * 80 + "\n")

    summary = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "total_regions": len(SUPPORTED_REGIONS),
        "regions": {},
    }

    for idx, region_slug in enumerate(SUPPORTED_REGIONS, start=1):
        print(f"\n[{idx}/{len(SUPPORTED_REGIONS)}] Executing training pipeline for '{region_slug}'...")
        try:
            res = train_region(region_slug, random_seed=random_seed, force_rebuild_data=force_rebuild)
            summary["regions"][region_slug] = {
                "status": res["status"],
                "champion": res["champion"],
                "threshold": res["threshold"],
                "recall": res["metrics"]["recall"],
                "roc_auc": res["metrics"]["roc_auc"],
                "f1_score": res["metrics"]["f1_score"],
                "brier_score": res["metrics"]["brier_score"],
            }
        except Exception as e:
            logger.error(f"Failed to train region {region_slug}: {e}", exc_info=True)
            summary["regions"][region_slug] = {
                "status": "FAILED",
                "error": str(e),
            }

    summary["duration_seconds"] = round(time.time() - t_start, 2)

    # Save summary report
    summary_path = REPORTS_DIR / "multi_region_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Print summary table
    print("\n" + "=" * 105)
    print("MULTI-REGION MODEL TOURNAMENT & VALIDATION BENCHMARK SUMMARY")
    print("=" * 105)
    print(f"{'Region':<22} | {'Status':<18} | {'Champion':<20} | {'Threshold':<10} | {'Recall':<8} | {'ROC-AUC':<8} | {'F1':<6}")
    print("-" * 105)
    for r, info in summary["regions"].items():
        st = info.get("status", "FAILED")
        champ = info.get("champion", "N/A")
        tau = str(info.get("threshold", "N/A"))
        rec = str(info.get("recall", "N/A"))
        auc = str(info.get("roc_auc", "N/A"))
        f1 = str(info.get("f1_score", "N/A"))
        print(f"{r:<22} | {st:<18} | {champ:<20} | {tau:<10} | {rec:<8} | {auc:<8} | {f1:<6}")
    print("=" * 105)
    print(f"Summary written to: {summary_path}\n")

    return summary


def main():
    train_all()


if __name__ == "__main__":
    main()
