"""
Canonical Feature Schema for Flowshield ML Models (DEPRECATED - V1 Legacy)
DEPRECATION NOTICE: This 12-feature schema was used for V1 synthetic models.
The canonical 15-feature contract is defined in `ml.features.feature_definitions`.
"""

import warnings
from typing import Dict, List, Tuple

warnings.warn(
    "ml.feature_schema is deprecated as of V2.5. "
    "Please import from ml.features.feature_definitions for the canonical 15-feature contract.",
    DeprecationWarning,
    stacklevel=2,
)

# Canonical 15-feature import for forwards compatibility
try:
    from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES
except ImportError:
    CANONICAL_FEATURE_NAMES = None

# Exact 12-feature ordered contract (preserved for legacy V1 backwards compatibility)
FEATURE_SCHEMA: List[str] = [
    "rainfall_1h",
    "rainfall_3h",
    "rainfall_6h",
    "rainfall_24h",
    "rainfall_intensity",
    "soil_moisture",
    "river_level",
    "river_level_change",
    "elevation",
    "slope",
    "distance_to_river",
    "historical_flood_frequency",
]

# Physical and hydrological validation bounds
FEATURE_BOUNDS: Dict[str, Tuple[float, float]] = {
    "rainfall_1h": (0.0, 200.0),                  # mm in last hour
    "rainfall_3h": (0.0, 350.0),                  # mm cumulative 3h
    "rainfall_6h": (0.0, 500.0),                  # mm cumulative 6h
    "rainfall_24h": (0.0, 800.0),                 # mm cumulative 24h
    "rainfall_intensity": (0.0, 120.0),            # mm/hr instantaneous
    "soil_moisture": (0.0, 100.0),                # % saturation
    "river_level": (0.5, 18.0),                   # meters gauge height
    "river_level_change": (-3.0, 6.0),            # m/hr rate of change
    "elevation": (300.0, 3500.0),                 # meters AMSL (Himalayan foothill/valley range)
    "slope": (0.0, 60.0),                         # degrees catchment inclination
    "distance_to_river": (0.02, 20.0),            # km distance to nearest major stream
    "historical_flood_frequency": (0.0, 1.0),     # annualized historical flood frequency (0 to 1)
}

TARGET_COLUMN: str = "flood_label"
MODEL_VERSION_PREFIX: str = "xgb-v1.0.0"
DEFAULT_SEED: int = 26192
