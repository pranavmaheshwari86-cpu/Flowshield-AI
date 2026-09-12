"""FlowShield Canonical Feature Engineering Package"""
from .feature_definitions import (
    CANONICAL_FEATURE_NAMES,
    TARGET_COLUMN,
    FEATURE_METADATA,
    MANDI_STATIONS_METADATA,
)
from .rainfall_features import compute_rolling_rainfall
from .soil_moisture_features import calculate_soil_saturation
from .terrain_features import haversine_distance_meters
from .builder import build_feature_vector

__all__ = [
    "CANONICAL_FEATURE_NAMES",
    "TARGET_COLUMN",
    "FEATURE_METADATA",
    "MANDI_STATIONS_METADATA",
    "compute_rolling_rainfall",
    "calculate_soil_saturation",
    "haversine_distance_meters",
    "build_feature_vector",
]
