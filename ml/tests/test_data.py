"""
ml/tests/test_data.py
Tests for data loading, partitioning, and physical range validation.
"""

import pytest
import pandas as pd
from ml.src.data.loader import load_processed_features, load_splits
from ml.src.data.validator import validate_feature_vector, validate_feature_ranges
from ml.src.features.feature_definitions import CANONICAL_FEATURE_NAMES


def test_load_processed_features():
    df = load_processed_features()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 1000
    for feat in CANONICAL_FEATURE_NAMES:
        assert feat in df.columns


def test_load_splits():
    train_df, tune_df, cal_df, test_df = load_splits()
    assert len(train_df) > 0
    assert len(tune_df) > 0
    assert len(cal_df) > 0
    assert len(test_df) > 0

    splits_dict = load_splits(as_dict=True)
    assert "train" in splits_dict
    assert "test" in splits_dict
    assert len(splits_dict["test"]) == 4200


def test_validate_feature_vector(valid_feature_dict, corrupt_feature_dict):
    is_valid, violations = validate_feature_vector(valid_feature_dict)
    assert is_valid is True
    assert len(violations) == 0

    # Test invalid bounds (negative rainfall)
    bad_dict = dict(valid_feature_dict)
    bad_dict["rainfall_1h_mm"] = -10.0
    is_valid, violations = validate_feature_vector(bad_dict)
    assert is_valid is False
    assert any("out of physical bounds" in v for v in violations)

    # Test missing values
    is_valid, violations = validate_feature_vector(corrupt_feature_dict)
    assert is_valid is False
    assert any("Missing required" in v for v in violations)


def test_validate_feature_ranges(sample_feature_df):
    result = validate_feature_ranges(sample_feature_df)
    assert result["is_valid"] is True
    assert len(result["errors"]) == 0
