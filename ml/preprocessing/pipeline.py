"""
ml/preprocessing/pipeline.py
Flowshield — Data Preprocessing & Leak-Free Splitting Pipeline
Smart India Hackathon 2026 (PS ID: 26192)

Enforces strict temporal and event-isolated splitting:
- Train: Normal monsoon baseline (July 2022) + Disaster Wave 2 (Aug 2023)
- Test: Unseen Disaster Wave 1 (July 1 - July 25, 2023 historic catastrophe)
- Preprocessing fit strictly on training set only.
"""

import os
import pandas as pd
import numpy as np
import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from typing import Tuple, Dict, Any

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES, TARGET_COLUMN

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DATA_PATH = os.path.join(BASE_DIR, "data", "real", "mandi_real_hydrology_features.csv")


def load_raw_dataset(csv_path: str = DEFAULT_DATA_PATH) -> pd.DataFrame:
    """Loads the verified real hydrology features CSV."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at: {csv_path}")
    df = pd.read_csv(csv_path)
    df["time"] = pd.to_datetime(df["time"])
    return df


def split_by_event_temporal(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Executes a strict, leak-free event holdout split:
    - Test Set: July 1, 2023 to July 25, 2023 (The July 2023 historic catastrophe).
    - Train Set: All other periods (July 2022 baseline + July 26 to August 31, 2023 cloudburst wave).
    """
    test_mask = (df["time"] >= "2023-07-01") & (df["time"] <= "2023-07-25 23:59:59")
    test_df = df[test_mask].copy().reset_index(drop=True)
    train_df = df[~test_mask].copy().reset_index(drop=True)
    
    print(f"Dataset Split Summary:")
    print(f"  Training Set: {len(train_df):,} samples | Positive (Flood): {train_df[TARGET_COLUMN].sum():,} ({train_df[TARGET_COLUMN].mean()*100:.2f}%)")
    print(f"  Testing Set:  {len(test_df):,} samples | Positive (Flood): {test_df[TARGET_COLUMN].sum():,} ({test_df[TARGET_COLUMN].mean()*100:.2f}%)")
    return train_df, test_df


def build_preprocessor() -> Pipeline:
    """Creates an imputing and standardizing pipeline."""
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])


def prepare_datasets(csv_path: str = DEFAULT_DATA_PATH) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Pipeline, pd.DataFrame, pd.DataFrame]:
    """
    Full preprocessing execution:
    1. Loads dataset
    2. Performs event holdout split
    3. Fits preprocessor ONLY on train features
    4. Transforms train and test features
    """
    df = load_raw_dataset(csv_path)
    train_df, test_df = split_by_event_temporal(df)
    
    X_train_raw = train_df[CANONICAL_FEATURE_NAMES]
    y_train = train_df[TARGET_COLUMN].values
    
    X_test_raw = test_df[CANONICAL_FEATURE_NAMES]
    y_test = test_df[TARGET_COLUMN].values
    
    preprocessor = build_preprocessor()
    X_train = preprocessor.fit_transform(X_train_raw)
    X_test = preprocessor.transform(X_test_raw)
    
    return X_train, y_train, X_test, y_test, preprocessor, train_df, test_df
