"""
ml/pipeline/dataset_builder.py
Flowshield — Multi-Region Dataset Builder

Assembles, engineers, validates, and splits datasets for each of the
10 supported flood intelligence regions.

Workflow:
1. Load region configuration YAML
2. Ingest or generate station meteorological data (Open-Meteo ERA5 / regional hydrology)
3. Compute canonical 15 features via feature_engineering
4. Attach flood labels via label_engineering (IndoFloods + reference events + FFG)
5. Enforce canonical 15-feature contract and physical bounds
6. Produce temporal and spatial train / val-cal / val-tune / holdout splits
7. Persist processed datasets and splits
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import yaml
import numpy as np
import pandas as pd

from ml.registry.feature_contract import (
    CANONICAL_FEATURES,
    TARGET_COLUMN,
    feature_contract,
)
from ml.registry.region_resolver import get_region_config_path
from ml.pipeline.feature_engineering import engineer_features
from ml.pipeline.label_engineering import apply_flood_labels
from ml.pipeline.splitter import split_region_data
from ml.pipeline.data_sources.indofloods import (
    load_indofloods_events,
    load_indofloods_metadata,
    filter_events_by_region,
    extract_event_dates,
)
from ml.src.utils.paths import MLPaths

logger = logging.getLogger("flowshield.pipeline.dataset_builder")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def load_region_yaml(region_slug: str) -> Dict[str, Any]:
    """Loads regional YAML configuration."""
    cfg_path = get_region_config_path(region_slug)
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _generate_synthetic_climatology_station(*args, **kwargs) -> pd.DataFrame:
    """
    PERMANENTLY DISABLED: Under Flowshield Ultimate Scientific Rebuild (§4 & §5),
    synthetic weather/climate data generation is strictly prohibited from entering model training.
    """
    raise PermissionError(
        "Synthetic climatology generation is permanently disabled under Absolute Truth Policy (§0) "
        "and Synthetic Data Ban (§4). All production candidates must use verified empirical data."
    )


def build_region_dataset(
    region_slug: str,
    force_fetch: bool = False,
) -> Tuple[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
    """
    Builds the full canonical dataset and 4 splits for a region.

    Returns
    -------
    (full_processed_df, (train_df, val_cal_df, val_tune_df, holdout_df))
    """
    region_config = load_region_yaml(region_slug)
    logger.info(f"Building dataset for region: {region_slug} ({region_config['region']['display_name']})")

    MLPaths.ensure_region_dirs(region_slug)
    raw_dir = MLPaths.region_data_dir(region_slug)
    splits_dir = MLPaths.region_splits_dir(region_slug)
    processed_dir = MLPaths.DATA_PROCESSED_DIR / region_slug
    processed_dir.mkdir(parents=True, exist_ok=True)
    splits_dir.mkdir(parents=True, exist_ok=True)

    # 1. Acquire raw data
    raw_file = raw_dir / f"{region_slug}_raw_era5.csv"
    raw_df = None

    # Check for existing Himachal real data
    if region_slug == "himachal_pradesh":
        hp_mandi_path = REPO_ROOT / "data" / "real" / "mandi_era5_hourly_raw.csv"
        if hp_mandi_path.exists():
            logger.info(f"Using verified Himachal Pradesh raw ERA5 file: {hp_mandi_path}")
            raw_df = pd.read_csv(hp_mandi_path)
            # Add missing terrain if not present
            stns = region_config.get("stations", {})
            stn_01 = next(iter(stns.values())) if stns else {}
            if "datetime_utc" not in raw_df.columns and "time" in raw_df.columns:
                raw_df["datetime_utc"] = raw_df["time"]
            if "station_id" not in raw_df.columns:
                raw_df["station_id"] = "MND_URBAN_01"
            if "elevation_m" not in raw_df.columns:
                raw_df["elevation_m"] = float(stn_01.get("elevation_m", 760.0))
            if "catchment_slope_deg" not in raw_df.columns:
                raw_df["catchment_slope_deg"] = float(stn_01.get("catchment_slope_deg", 16.0))
            if "dist_to_river_m" not in raw_df.columns:
                raw_df["dist_to_river_m"] = float(stn_01.get("dist_to_river_m", 35.0))
            if "upstream_drainage_sqkm" not in raw_df.columns:
                raw_df["upstream_drainage_sqkm"] = float(stn_01.get("upstream_drainage_sqkm", 6350.0))

    if raw_df is None and raw_file.exists() and not force_fetch:
        logger.info(f"Loading cached raw station data from {raw_file}")
        raw_df = pd.read_csv(raw_file)

    if raw_df is None:
        from ml.pipeline.data_sources.open_meteo import fetch_station_era5
        stations = region_config.get("stations", {})
        frames = []
        for stn_id, stn_cfg in stations.items():
            lat = float(stn_cfg.get("latitude", 0.0))
            lon = float(stn_cfg.get("longitude", 0.0))
            logger.info(f"Fetching authentic Copernicus ERA5-Land reanalysis for {stn_id} ({lat}, {lon})...")
            stn_df = fetch_station_era5(
                station_id=stn_id,
                latitude=lat,
                longitude=lon,
                start_date="2022-07-01",
                end_date="2023-08-31",
                cache_dir=raw_dir,
            )
            if not stn_df.empty:
                # Add authentic terrain attributes from verified regional config
                stn_df["elevation_m"] = float(stn_cfg.get("elevation_m", 1000.0))
                stn_df["catchment_slope_deg"] = float(stn_cfg.get("catchment_slope_deg", 15.0))
                stn_df["dist_to_river_m"] = float(stn_cfg.get("dist_to_river_m", 100.0))
                stn_df["upstream_drainage_sqkm"] = float(stn_cfg.get("upstream_drainage_sqkm", 2500.0))
                frames.append(stn_df)

        if frames:
            raw_df = pd.concat(frames, ignore_index=True)
            raw_df.to_csv(raw_file, index=False)
            logger.info(f"Saved authentic Copernicus ERA5 station dataset ({len(raw_df)} rows) to {raw_file}")
        else:
            raise RuntimeError(
                f"Data Provenance Gate Violation: Unable to acquire verified empirical data for '{region_slug}'. "
                "Synthetic data generation is strictly prohibited by Absolute Truth Policy (§0) and Synthetic Data Ban (§4)."
            )

    # 2. Engineer canonical 15 features
    logger.info("Computing canonical 15 features...")
    features_df = engineer_features(raw_df)

    # 3. Label engineering
    logger.info("Engineering flood labels...")
    indofloods_events = load_indofloods_events()
    indofloods_meta = load_indofloods_metadata()
    filtered_events = filter_events_by_region(
        indofloods_events, indofloods_meta, region_config.get("boundary", {})
    )
    indofloods_windows = extract_event_dates(filtered_events)

    labeled_df = apply_flood_labels(
        features_df,
        region_config=region_config,
        indofloods_windows=indofloods_windows,
        use_hydrological_ffg=True,
    )

    # 4. Enforce canonical contract
    valid, errors = feature_contract.validate_dataset_columns(list(labeled_df.columns))
    if not valid:
        raise ValueError(f"Feature contract violation in {region_slug}: {errors}")

    # Save processed full dataset
    processed_file = processed_dir / "dataset.csv"
    labeled_df.to_csv(processed_file, index=False)
    logger.info(f"Saved canonical processed dataset to {processed_file}")

    # 5. Split dataset
    train_df, val_cal_df, val_tune_df, holdout_df = split_region_data(labeled_df, region_config)

    train_df.to_csv(splits_dir / "train_split.csv", index=False)
    val_cal_df.to_csv(splits_dir / "val_cal_split.csv", index=False)
    val_tune_df.to_csv(splits_dir / "val_tune_split.csv", index=False)
    holdout_df.to_csv(splits_dir / "holdout_split.csv", index=False)

    logger.info(
        f"Region [{region_slug}] splits saved: "
        f"Train={len(train_df)}, ValCal={len(val_cal_df)}, ValTune={len(val_tune_df)}, Holdout={len(holdout_df)}"
    )

    return labeled_df, (train_df, val_cal_df, val_tune_df, holdout_df)
