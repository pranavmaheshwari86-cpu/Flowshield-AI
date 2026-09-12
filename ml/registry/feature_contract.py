"""
ml/registry/feature_contract.py
Flowshield — Canonical 15-Feature Contract Enforcer

Locks the feature ordering, schema version, and provides validation
for any model or dataset claiming compliance with the Flowshield
flood prediction feature contract.
"""

import hashlib
import json
from typing import List, Dict, Any, Tuple

# Schema version — increment on any contract change
FEATURE_SCHEMA_VERSION = "3.0.0"

# The canonical 15 features in locked order.
# This is the single source of truth. All models, datasets,
# preprocessors, and inference paths must use this exact ordering.
CANONICAL_FEATURES: List[str] = [
    "rainfall_1h_mm",           # 1. Short-term rainfall intensity
    "rainfall_3h_mm",           # 2. Medium-term antecedent rainfall
    "rainfall_6h_mm",           # 3. Intermediate rainfall accumulation
    "rainfall_24h_mm",          # 4. Daily antecedent rainfall
    "rainfall_72h_mm",          # 5. Multi-day cumulative rainfall
    "soil_saturation_pct",      # 6. Topsoil saturation (0-7cm, % of field capacity)
    "deep_soil_saturation_pct", # 7. Deep soil saturation (7-28cm, % of field capacity)
    "temperature_c",            # 8. Ambient air temperature at 2m (Celsius)
    "relative_humidity_pct",    # 9. Relative atmospheric humidity (%)
    "surface_pressure_hpa",     # 10. Barometric surface pressure (hPa)
    "wind_speed_kmh",           # 11. Surface wind speed at 10m (km/h)
    "elevation_m",              # 12. Station elevation above sea level (m)
    "catchment_slope_deg",      # 13. Mean catchment hillslope incline (degrees)
    "dist_to_river_m",          # 14. Distance to active river channel (m)
    "upstream_drainage_sqkm",   # 15. Upstream contributing catchment area (km²)
]

TARGET_COLUMN = "flood_occurred"

# Physical bounds for validation
PHYSICAL_BOUNDS: Dict[str, Tuple[float, float]] = {
    "rainfall_1h_mm":           (0.0, 500.0),
    "rainfall_3h_mm":           (0.0, 800.0),
    "rainfall_6h_mm":           (0.0, 1200.0),
    "rainfall_24h_mm":          (0.0, 2000.0),
    "rainfall_72h_mm":          (0.0, 4000.0),
    "soil_saturation_pct":      (0.0, 100.0),
    "deep_soil_saturation_pct": (0.0, 100.0),
    "temperature_c":            (-50.0, 60.0),
    "relative_humidity_pct":    (0.0, 100.0),
    "surface_pressure_hpa":     (400.0, 1100.0),
    "wind_speed_kmh":           (0.0, 300.0),
    "elevation_m":              (0.0, 9000.0),
    "catchment_slope_deg":      (0.0, 90.0),
    "dist_to_river_m":          (0.0, 100000.0),
    "upstream_drainage_sqkm":   (0.0, 50000.0),
}

# Feature groups for ablation experiments
FEATURE_GROUPS = {
    "meteorology": [
        "rainfall_1h_mm", "rainfall_3h_mm", "rainfall_6h_mm",
        "rainfall_24h_mm", "rainfall_72h_mm",
        "temperature_c", "relative_humidity_pct",
        "surface_pressure_hpa", "wind_speed_kmh",
    ],
    "terrain": [
        "elevation_m", "catchment_slope_deg",
        "dist_to_river_m", "upstream_drainage_sqkm",
    ],
    "soil": [
        "soil_saturation_pct", "deep_soil_saturation_pct",
    ],
    "rainfall": [
        "rainfall_1h_mm", "rainfall_3h_mm", "rainfall_6h_mm",
        "rainfall_24h_mm", "rainfall_72h_mm",
    ],
}

# Ablation experiment definitions (spec §36)
ABLATION_EXPERIMENTS = {
    "A_meteorology_only": FEATURE_GROUPS["meteorology"],
    "B_terrain_only": FEATURE_GROUPS["terrain"],
    "C_meteorology_soil": FEATURE_GROUPS["meteorology"] + FEATURE_GROUPS["soil"],
    "D_meteorology_terrain": FEATURE_GROUPS["meteorology"] + FEATURE_GROUPS["terrain"],
    "E_all_canonical": CANONICAL_FEATURES,
}


def compute_schema_hash() -> str:
    """Compute deterministic hash of the feature schema for integrity checks."""
    payload = json.dumps({
        "version": FEATURE_SCHEMA_VERSION,
        "features": CANONICAL_FEATURES,
        "target": TARGET_COLUMN,
    }, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class FeatureContract:
    """
    Validates datasets, feature vectors, and model artifacts against
    the canonical 15-feature Flowshield contract.
    """

    def __init__(self):
        self.features = CANONICAL_FEATURES
        self.version = FEATURE_SCHEMA_VERSION
        self.schema_hash = compute_schema_hash()
        self.bounds = PHYSICAL_BOUNDS
        self.target = TARGET_COLUMN

    @property
    def feature_count(self) -> int:
        return len(self.features)

    def validate_feature_order(self, feature_list: List[str]) -> Tuple[bool, List[str]]:
        """Checks that a feature list matches the canonical order exactly."""
        errors = []
        if len(feature_list) != len(self.features):
            errors.append(
                f"Feature count mismatch: got {len(feature_list)}, "
                f"expected {len(self.features)}"
            )
            return False, errors

        for i, (actual, expected) in enumerate(zip(feature_list, self.features)):
            if actual != expected:
                errors.append(
                    f"Position {i}: got '{actual}', expected '{expected}'"
                )

        return len(errors) == 0, errors

    def validate_feature_values(
        self, feature_dict: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validates physical feasibility of feature values."""
        errors = []
        for feat, (lo, hi) in self.bounds.items():
            val = feature_dict.get(feat)
            if val is None:
                continue
            try:
                v = float(val)
                if v < lo or v > hi:
                    errors.append(
                        f"'{feat}' value {v} outside bounds [{lo}, {hi}]"
                    )
            except (ValueError, TypeError):
                errors.append(f"'{feat}' cannot be parsed as float: {val}")
        return len(errors) == 0, errors

    def validate_dataset_columns(
        self, columns: List[str]
    ) -> Tuple[bool, List[str]]:
        """Checks that a dataset has all required columns."""
        missing = [f for f in self.features if f not in columns]
        errors = []
        if missing:
            errors.append(f"Missing mandatory features: {missing}")
        if self.target not in columns:
            errors.append(f"Missing target column: {self.target}")
        return len(errors) == 0, errors

    def get_ablation_features(self, experiment: str) -> List[str]:
        """Returns feature list for a specific ablation experiment."""
        if experiment not in ABLATION_EXPERIMENTS:
            raise ValueError(
                f"Unknown ablation experiment '{experiment}'. "
                f"Available: {list(ABLATION_EXPERIMENTS.keys())}"
            )
        return ABLATION_EXPERIMENTS[experiment]

    def to_schema_dict(self) -> Dict[str, Any]:
        """Serializes the contract for model artifacts."""
        return {
            "schema_version": self.version,
            "schema_hash": self.schema_hash,
            "features": self.features,
            "feature_count": self.feature_count,
            "target": self.target,
            "physical_bounds": {
                k: {"min": lo, "max": hi}
                for k, (lo, hi) in self.bounds.items()
            },
        }


# Module-level singleton
feature_contract = FeatureContract()
