"""
ml/src/data/loader.py
Flowshield — Standardized Dataset Loader
"""

import os
from pathlib import Path
from typing import Tuple, Optional
import pandas as pd
from ..utils.paths import MLPaths
from ..utils.logger import get_logger

logger = get_logger("flowshield.data.loader")


def load_processed_features(csv_path: Optional[Path] = None) -> pd.DataFrame:
    """Loads authoritative 15-feature Mandi hydrological dataset."""
    path = csv_path or (MLPaths.DATA_PROCESSED_DIR / "mandi_real_hydrology_features.csv")
    if not path.exists():
        # Fallback to data/real in repo root
        fallback = MLPaths.REPO_ROOT / "data" / "real" / "mandi_real_hydrology_features.csv"
        if fallback.exists():
            path = fallback
        else:
            raise FileNotFoundError(f"Processed hydrology dataset not found at {path} or {fallback}")
    logger.info(f"Loading processed features from: {path}")
    return pd.read_csv(path)


def load_splits(as_dict: bool = False):
    """Loads immutable train, val_tune, val_cal, and final_test_locked partitions."""
    splits_dir = MLPaths.DATA_SPLITS_DIR
    train_df = pd.read_csv(splits_dir / "train_split.csv")
    tune_df = pd.read_csv(splits_dir / "val_tune_split.csv")
    cal_df = pd.read_csv(splits_dir / "val_cal_split.csv")
    test_df = pd.read_csv(splits_dir / "final_test_locked.csv")
    logger.info(f"Splits loaded: train={len(train_df)}, tune={len(tune_df)}, cal={len(cal_df)}, test={len(test_df)}")
    if as_dict:
        return {
            "train": train_df,
            "val_tune": tune_df,
            "val_cal": cal_df,
            "test": test_df,
        }
    return train_df, tune_df, cal_df, test_df


# Alias for backward compatibility
load_processed_hydrology_data = load_processed_features

