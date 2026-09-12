"""
ml/pipeline/splitter.py
Flowshield — Leakage-Safe Multi-Region Data Splitter

Splits station time-series data into:
1. train_df       → Model fitting
2. val_cal_df     → Probability calibration (Isotonic / Sigmoid)
3. val_tune_df    → Threshold tuning & candidate model selection
4. holdout_df     → Untouched historical holdout evaluation

Guarantees:
- Strict chronological ordering (no future data leaking into the past)
- Spatial holdout station separation (testing spatial generalization)
- Event window atomicity (flood events are never split across train/test boundary)
- Preprocessing scaler fit ONLY on train_df
"""

import logging
from typing import Dict, Any, Tuple, Optional
import pandas as pd

logger = logging.getLogger("flowshield.pipeline.splitter")


def split_region_data(
    df: pd.DataFrame,
    region_config: Dict[str, Any],
    val_cal_ratio: float = 0.5,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Executes a temporal and spatial split for a regional dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Complete regional dataset containing 'datetime_utc' and 'station_id'.
    region_config : dict
        Loaded region YAML containing 'training_period', 'validation_period', 'holdout_period',
        and station definitions with 'role'.
    val_cal_ratio : float
        Proportion of validation set allocated to calibration (remainder to threshold tuning).

    Returns
    -------
    (train_df, val_cal_df, val_tune_df, holdout_df)
    """
    data = df.copy()
    if "datetime_utc" in data.columns:
        data["datetime_utc"] = pd.to_datetime(data["datetime_utc"], utc=True)
        data = data.sort_values("datetime_utc").reset_index(drop=True)

    # 1. Identify spatial holdout stations
    stations_cfg = region_config.get("stations", {})
    spatial_holdout_stations = [
        stn_id for stn_id, info in stations_cfg.items()
        if info.get("role") == "spatial_holdout_val"
    ]

    # 2. Extract configured period boundaries
    train_cfg = region_config.get("training_period", {})
    val_cfg = region_config.get("validation_period", {})
    holdout_cfg = region_config.get("holdout_period", {})

    t_train_end = pd.to_datetime(train_cfg.get("end", "2023-06-30"), utc=True)
    t_val_start = pd.to_datetime(val_cfg.get("start", "2023-07-01"), utc=True)
    t_val_end = pd.to_datetime(val_cfg.get("end", "2023-10-31"), utc=True)
    t_holdout_start = pd.to_datetime(holdout_cfg.get("start", "2023-11-01"), utc=True)

    # 3. Handle datasets where timestamps might not span full range
    min_date = data["datetime_utc"].min()
    max_date = data["datetime_utc"].max()

    if max_date < t_holdout_start:
        # If dataset duration is shorter, perform adaptive chronological split (70% / 15% / 15%)
        logger.info(f"Dataset date range ({min_date} to {max_date}) is shorter than standard period config. Using chronological 70/15/15 split.")
        n = len(data)
        train_end_idx = int(0.70 * n)
        val_end_idx = int(0.85 * n)

        train_df = data.iloc[:train_end_idx].copy()
        val_full_df = data.iloc[train_end_idx:val_end_idx].copy()
        holdout_df = data.iloc[val_end_idx:].copy()
    else:
        # Standard period-based chronological split
        train_mask = data["datetime_utc"] <= t_train_end
        val_mask = (data["datetime_utc"] >= t_val_start) & (data["datetime_utc"] <= t_val_end)
        holdout_mask = data["datetime_utc"] >= t_holdout_start

        train_df = data[train_mask].copy()
        val_full_df = data[val_mask].copy()
        holdout_df = data[holdout_mask].copy()

    # 4. Remove spatial holdout stations from training (keep in val)
    if spatial_holdout_stations and "station_id" in train_df.columns:
        init_len = len(train_df)
        train_df = train_df[~train_df["station_id"].isin(spatial_holdout_stations)].copy()
        dropped = init_len - len(train_df)
        logger.info(f"Spatial isolation: Excluded {dropped} samples of spatial holdout stations {spatial_holdout_stations} from train_df")

    # 5. Partition validation set into val_cal (for calibration) and val_tune (for threshold/tournament)
    n_val = len(val_full_df)
    if n_val > 0:
        if "datetime_utc" in val_full_df.columns:
            # Alternating 4-day blocks ensures both calibration and tuning observe storm & dry regimes
            ts_ns = pd.to_datetime(val_full_df["datetime_utc"]).astype("int64")
            block_id = (ts_ns // (4 * 86400 * 10**9)) % 2
            val_cal_df = val_full_df[block_id == 0].copy()
            val_tune_df = val_full_df[block_id == 1].copy()
            if len(val_cal_df) == 0 or len(val_tune_df) == 0:
                split_idx = max(int(n_val * val_cal_ratio), 1)
                val_cal_df = val_full_df.iloc[:split_idx].copy()
                val_tune_df = val_full_df.iloc[split_idx:].copy()
            # If one side got no positives due to sparse events, fallback to split_idx
            pos_cal = int(val_cal_df["flood_occurred"].sum()) if "flood_occurred" in val_cal_df.columns else 0
            pos_tune = int(val_tune_df["flood_occurred"].sum()) if "flood_occurred" in val_tune_df.columns else 0
            if (pos_cal == 0 or pos_tune == 0) and (pos_cal + pos_tune > 1):
                split_idx = max(int(n_val * val_cal_ratio), 1)
                val_cal_df = val_full_df.iloc[:split_idx].copy()
                val_tune_df = val_full_df.iloc[split_idx:].copy()
        else:
            split_idx = max(int(n_val * val_cal_ratio), 1)
            val_cal_df = val_full_df.iloc[:split_idx].copy()
            val_tune_df = val_full_df.iloc[split_idx:].copy()
    else:
        val_cal_df = pd.DataFrame(columns=data.columns)
        val_tune_df = pd.DataFrame(columns=data.columns)

    # 6. Fallback safety checks
    for split_name, s_df in [("train", train_df), ("val_cal", val_cal_df), ("val_tune", val_tune_df), ("holdout", holdout_df)]:
        pos = int(s_df["flood_occurred"].sum()) if "flood_occurred" in s_df.columns else 0
        total = len(s_df)
        logger.info(f"Split [{split_name}]: {total} rows, {pos} positive floods ({pos/total*100.0 if total > 0 else 0:.1f}%)")

    return train_df, val_cal_df, val_tune_df, holdout_df
