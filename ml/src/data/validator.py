"""
ml/src/data/validator.py
Flowshield — Physical Range & Schema Validator
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
from ..features.feature_definitions import CANONICAL_FEATURE_NAMES, FEATURE_METADATA


def validate_feature_vector(features: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that a feature vector conforms to canonical names and physical boundaries.
    Returns (is_valid, list_of_violations).
    """
    violations: List[str] = []
    for name in CANONICAL_FEATURE_NAMES:
        if name not in features:
            violations.append(f"Missing required canonical feature: '{name}'")
            continue
        val = features[name]
        try:
            f_val = float(val)
        except (ValueError, TypeError):
            violations.append(f"Feature '{name}' has non-numeric value: {val}")
            continue
        meta = FEATURE_METADATA[name]
        if f_val < meta["min"] or f_val > meta["max"]:
            violations.append(
                f"Feature '{name}' value {f_val} out of physical bounds [{meta['min']}, {meta['max']}]"
            )
    return len(violations) == 0, violations


def validate_feature_ranges(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates that a DataFrame conforms to canonical names and physical boundaries.
    Returns a dictionary with is_valid status, error list, and out-of-bounds count.
    """
    errors: List[str] = []
    out_of_bounds = {}

    for name in CANONICAL_FEATURE_NAMES:
        if name not in df.columns:
            errors.append(f"Missing required canonical feature column: '{name}'")
            continue
        meta = FEATURE_METADATA[name]
        series = pd.to_numeric(df[name], errors="coerce")
        nan_count = int(series.isna().sum())
        if nan_count > 0:
            errors.append(f"Column '{name}' has {nan_count} NaN or non-numeric values.")

        oob = int(((series < meta["min"]) | (series > meta["max"])).sum())
        if oob > 0:
            out_of_bounds[name] = oob

    is_valid = len(errors) == 0
    return {
        "is_valid": is_valid,
        "errors": errors,
        "out_of_bounds": out_of_bounds,
    }

