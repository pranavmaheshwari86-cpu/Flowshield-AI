"""
ml/src/data/splitter.py
Flowshield — Chronological & Spatial Data Splitter
"""

import pandas as pd
from typing import Tuple


def chronological_split(
    df: pd.DataFrame,
    timestamp_col: str = "timestamp",
    train_ratio: float = 0.70,
    tune_ratio: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Sorts chronologically and creates leak-free train, tune, and calibration splits.
    """
    sorted_df = df.sort_values(by=timestamp_col).reset_index(drop=True)
    n = len(sorted_df)
    train_end = int(n * train_ratio)
    tune_end = int(n * (train_ratio + tune_ratio))
    
    train = sorted_df.iloc[:train_end].copy()
    tune = sorted_df.iloc[train_end:tune_end].copy()
    cal = sorted_df.iloc[tune_end:].copy()
    return train, tune, cal
