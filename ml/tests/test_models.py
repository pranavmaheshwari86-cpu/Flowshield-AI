"""
ml/tests/test_models.py
Tests for model factory, training, and calibration reproducibility.
"""

import pytest
import numpy as np
import pandas as pd
from ml.src.models.factory import ModelFactory, create_model
from ml.src.models.train import train_production_champion
from ml.src.models.calibrate import fit_calibrator
from ml.src.evaluation.metrics import check_monotonicity
from ml.src.data.loader import load_splits


def test_model_factory_architectures():
    lr = ModelFactory.create("logistic_regression")
    assert lr is not None
    assert hasattr(lr, "fit")

    rf = ModelFactory.create("random_forest")
    assert rf is not None
    assert hasattr(rf, "fit")


def test_train_production_champion():
    splits = load_splits(as_dict=True)
    # Stratified sample ensuring both positive and negative flood events are present
    train_df = pd.concat([
        splits["train"][splits["train"]["flood_occurred"] == 0].sample(200, random_state=42),
        splits["train"][splits["train"]["flood_occurred"] == 1].sample(50, random_state=42),
    ])
    cal_df = pd.concat([
        splits["val_cal"][splits["val_cal"]["flood_occurred"] == 0].sample(100, random_state=42),
        splits["val_cal"][splits["val_cal"]["flood_occurred"] == 1].sample(30, random_state=42),
    ])

    model, calibrator, preprocessor = train_production_champion(
        train_df=train_df,
        cal_df=cal_df,
        seed=26192,
    )

    assert model is not None
    assert calibrator is not None
    assert preprocessor is not None

    from ml.src.features.feature_definitions import CANONICAL_FEATURE_NAMES
    X_test = cal_df[CANONICAL_FEATURE_NAMES]
    X_scaled = preprocessor.transform(X_test)
    raw_probs = model.predict_proba(X_scaled)[:, 1]
    cal_probs = calibrator.predict_proba(X_scaled)[:, 1]

    assert len(cal_probs) == len(cal_df)
    assert np.all(cal_probs >= 0.0) and np.all(cal_probs <= 1.0)
    # Check monotonicity
    assert check_monotonicity(raw_probs, cal_probs) is True
