"""
ml/src/features/builder.py
Flowshield — Canonical 15-Feature Matrix Builder
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .feature_definitions import CANONICAL_FEATURE_NAMES, FEATURE_METADATA


def build_feature_vector(input_dict: Dict[str, Any]) -> pd.DataFrame:
    """
    Constructs a 1-row DataFrame containing all 15 canonical features in exact order,
    applying physical bounds clipping and median fallbacks.
    """
    row: Dict[str, float] = {}
    for feat in CANONICAL_FEATURE_NAMES:
        val = input_dict.get(feat)
        meta = FEATURE_METADATA[feat]
        if val is None or (isinstance(val, float) and np.isnan(val)):
            val = (meta["min"] + meta["max"]) / 2.0
        else:
            val = float(val)
            val = max(meta["min"], min(meta["max"], val))
        row[feat] = val
    return pd.DataFrame([row], columns=CANONICAL_FEATURE_NAMES)


class FeatureMatrixBuilder:
    """Matrix builder for batch datasets and individual records."""

    @staticmethod
    def build_vector(input_dict: Dict[str, Any]) -> pd.DataFrame:
        return build_feature_vector(input_dict)

    @staticmethod
    def build_matrix(df: pd.DataFrame, clip_bounds: bool = True) -> pd.DataFrame:
        matrix = df.copy()
        for feat in CANONICAL_FEATURE_NAMES:
            if feat not in matrix.columns:
                meta = FEATURE_METADATA[feat]
                matrix[feat] = (meta["min"] + meta["max"]) / 2.0
            else:
                matrix[feat] = pd.to_numeric(matrix[feat], errors="coerce")
                if clip_bounds:
                    meta = FEATURE_METADATA[feat]
                    matrix[feat] = matrix[feat].clip(lower=meta["min"], upper=meta["max"])
        return matrix[CANONICAL_FEATURE_NAMES]
