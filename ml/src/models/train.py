"""
ml/src/models/train.py
Flowshield — Production Model Training & Calibration Runner
"""

import joblib
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV

from ..features.feature_definitions import CANONICAL_FEATURE_NAMES, TARGET_COLUMN
from ..utils.paths import MLPaths
from ..utils.logger import get_logger
from ..utils.seed import set_seed, DEFAULT_RANDOM_SEED
from .factory import create_model

logger = get_logger("flowshield.models.train")


def train_production_champion(
    train_df: pd.DataFrame,
    cal_df: pd.DataFrame,
    seed: int = DEFAULT_RANDOM_SEED,
) -> Tuple[Any, Any, Any]:
    """
    Trains production champion Logistic Regression model on train_df,
    fits preprocessing pipeline, and fits isotonic calibrator on cal_df.
    Returns (fitted_pipeline, fitted_calibrator, preprocessor).
    """
    set_seed(seed)
    logger.info(f"Training production model on {len(train_df)} samples...")
    
    X_train = train_df[CANONICAL_FEATURE_NAMES]
    y_train = train_df[TARGET_COLUMN]
    
    # 1. Fit Preprocessor
    preprocessor = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    X_train_scaled = preprocessor.fit_transform(X_train)
    
    # 2. Fit Base Model
    base_model = create_model("logistic_regression", random_state=seed)
    base_model.fit(X_train_scaled, y_train)
    logger.info("Base Logistic Regression model fitted.")
    
    # 3. Fit Isotonic Calibrator
    logger.info(f"Calibrating probabilities on {len(cal_df)} calibration samples...")
    X_cal = cal_df[CANONICAL_FEATURE_NAMES]
    y_cal = cal_df[TARGET_COLUMN]
    X_cal_scaled = preprocessor.transform(X_cal)
    
    try:
        from sklearn.frozen import FrozenEstimator
        calibrator = CalibratedClassifierCV(estimator=FrozenEstimator(base_model), method="isotonic")
    except ImportError:
        calibrator = CalibratedClassifierCV(estimator=base_model, method="isotonic", cv="prefit")
    calibrator.fit(X_cal_scaled, y_cal)
    logger.info("Isotonic calibration complete.")
    
    return base_model, calibrator, preprocessor
