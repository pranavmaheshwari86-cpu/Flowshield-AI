"""
ml/tests/test_features.py
Tests for feature definitions, physical boundaries, and feature matrix builder.
"""

import pytest
import pandas as pd
import numpy as np

from ml.src.features.feature_definitions import (
    CANONICAL_FEATURE_NAMES,
    FEATURE_METADATA,
    PHYSICAL_MIN_BOUNDS,
    PHYSICAL_MAX_BOUNDS,
    STATION_COORDINATES,
)
from ml.src.features.builder import FeatureMatrixBuilder


def test_canonical_feature_count():
    assert len(CANONICAL_FEATURE_NAMES) == 15
    assert len(FEATURE_METADATA) == 15
    assert len(PHYSICAL_MIN_BOUNDS) == 15
    assert len(PHYSICAL_MAX_BOUNDS) == 15


def test_physical_bounds_consistency():
    for feat in CANONICAL_FEATURE_NAMES:
        min_b = PHYSICAL_MIN_BOUNDS[feat]
        max_b = PHYSICAL_MAX_BOUNDS[feat]
        assert min_b < max_b, f"Feature {feat} has invalid bounds [{min_b}, {max_b}]"
        assert "unit" in FEATURE_METADATA[feat]
        assert "display_name" in FEATURE_METADATA[feat]


def test_station_coordinates():
    assert "PND_DAM_02" in STATION_COORDINATES or "Pandoh Dam Reservoir" in [s.get("name") for s in STATION_COORDINATES.values()]


def test_feature_matrix_builder_bounds_clipping(valid_feature_dict):
    builder = FeatureMatrixBuilder()
    extreme_dict = dict(valid_feature_dict)
    extreme_dict["rainfall_1h_mm"] = 9999.0  # Max is 300.0
    extreme_dict["soil_saturation_pct"] = -50.0  # Min is 0.0

    df = pd.DataFrame([extreme_dict])
    matrix = builder.build_matrix(df, clip_bounds=True)

    assert matrix.loc[0, "rainfall_1h_mm"] <= 300.0
    assert matrix.loc[0, "soil_saturation_pct"] >= 0.0
