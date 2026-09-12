"""
scratch/acquire_tier2_regional_data.py
Flowshield — Real Regional Data Acquisition for Tier 2 & Special Case Regions
Fetches authentic ERA5-Land hourly reanalysis via Open-Meteo Archive API
for Mizoram, Tripura, Manipur, Nagaland, and Leh & Ladakh.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.pipeline.data_sources.open_meteo import fetch_region_era5
from ml.pipeline.feature_engineering import engineer_features
from ml.pipeline.independent_labeler import independent_labeler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("flowshield.tier2_acquisition")

TIER_2_REGIONS = {
    "mizoram": {"start_date": "2023-06-01", "end_date": "2023-08-31"},
    "tripura": {"start_date": "2023-06-01", "end_date": "2023-08-31"},
    "manipur": {"start_date": "2023-06-01", "end_date": "2023-08-31"},
    "nagaland": {"start_date": "2023-06-01", "end_date": "2023-08-31"},
    "leh_ladakh": {"start_date": "2023-06-01", "end_date": "2023-08-31"},
}

def acquire_region(region_slug: str, start_date: str, end_date: str) -> Dict[str, Any]:
    cfg_path = REPO_ROOT / "ml" / "configs" / "regions" / f"{region_slug}.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
        
    stations = cfg.get("stations", {})
    raw_dir = REPO_ROOT / "ml" / "data" / "raw" / "regions" / region_slug
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"\nACQUIRING REAL DATA: {cfg.get('region', {}).get('display_name', region_slug)} ({len(stations)} stns)")
    raw_df = fetch_region_era5(
        stations=stations,
        start_date=start_date,
        end_date=end_date,
        cache_dir=raw_dir / "cache",
    )
    
    if raw_df.empty:
        logger.error(f"Failed to fetch data for {region_slug}")
        return {"status": "FAILED", "region": region_slug}
        
    raw_csv_path = raw_dir / f"{region_slug}_era5_hourly_raw.csv"
    raw_df.to_csv(raw_csv_path, index=False)
    
    feat_df = engineer_features(raw_df)
    labeled_df = independent_labeler.label_station_forecasting(
        feat_df,
        region_slug=region_slug,
        region_config=cfg,
        lead_hours=6,
    )
    
    processed_dir = REPO_ROOT / "ml" / "data" / "processed" / region_slug
    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_csv_path = processed_dir / f"{region_slug}_processed_dataset.csv"
    labeled_df.to_csv(processed_csv_path, index=False)
    
    total_samples = len(labeled_df)
    flood_samples = int(labeled_df["flood_occurred"].sum())
    prev = (flood_samples / total_samples * 100.0) if total_samples > 0 else 0.0
    
    logger.info(f"Done for {region_slug}: Rows={total_samples}, FloodHours={flood_samples} ({prev:.2f}%)")
    return {
        "status": "SUCCESS",
        "region_slug": region_slug,
        "total_rows": total_samples,
        "flood_hours": flood_samples,
        "prevalence_pct": round(prev, 2),
    }

if __name__ == "__main__":
    results = {}
    for r_slug, r_meta in TIER_2_REGIONS.items():
        res = acquire_region(r_slug, r_meta["start_date"], r_meta["end_date"])
        results[r_slug] = res
        time.sleep(2.0)
        
    import json
    with open(REPO_ROOT / "scratch" / "tier2_acquisition_summary.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nTier 2 Data acquisition complete!")
