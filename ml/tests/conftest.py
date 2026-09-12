"""
ml/tests/conftest.py
Flowshield — Test Fixtures for Machine Learning Test Suite
"""

import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.src.features.feature_definitions import CANONICAL_FEATURE_NAMES, TARGET_COLUMN


@pytest.fixture
def valid_feature_dict():
    """A physically realistic feature snapshot for Pandoh Dam station."""
    return {
        "rainfall_1h_mm": 14.5,
        "rainfall_3h_mm": 38.2,
        "rainfall_6h_mm": 65.0,
        "rainfall_24h_mm": 120.4,
        "rainfall_72h_mm": 180.5,
        "soil_saturation_pct": 84.5,
        "deep_soil_saturation_pct": 82.1,
        "temperature_c": 22.5,
        "relative_humidity_pct": 88.0,
        "surface_pressure_hpa": 915.0,
        "wind_speed_kmh": 18.5,
        "elevation_m": 895.0,
        "catchment_slope_deg": 22.0,
        "dist_to_river_m": 45.0,
        "upstream_drainage_sqkm": 5400.0,
    }


@pytest.fixture
def corrupt_feature_dict():
    """A corrupt feature dictionary with >20% missing values."""
    return {
        "rainfall_1h_mm": 5.0,
        "rainfall_3h_mm": 12.0,
        "soil_saturation_pct": 45.0,
    }


@pytest.fixture
def sample_feature_df(valid_feature_dict):
    """Small DataFrame with canonical features."""
    rows = []
    for i in range(20):
        row = dict(valid_feature_dict)
        row["rainfall_1h_mm"] = float(i * 2.0)
        row[TARGET_COLUMN] = 1 if i > 12 else 0
        rows.append(row)
    return pd.DataFrame(rows)
