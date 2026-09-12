"""
ml/src/features/rainfall_features.py
Flowshield — Rolling Rainfall Accumulation & Antecedent Moisture Index
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def compute_rolling_rainfall(hourly_series: pd.Series) -> Dict[str, float]:
    """
    Given an hourly rainfall series ordered chronologically (latest value at end),
    computes canonical rainfall accumulation features.
    """
    vals = hourly_series.values
    n = len(vals)
    
    r1 = float(vals[-1]) if n >= 1 else 0.0
    r3 = float(np.sum(vals[-3:])) if n >= 3 else float(np.sum(vals))
    r6 = float(np.sum(vals[-6:])) if n >= 6 else float(np.sum(vals))
    r24 = float(np.sum(vals[-24:])) if n >= 24 else float(np.sum(vals))
    r72 = float(np.sum(vals[-72:])) if n >= 72 else float(np.sum(vals))
    
    return {
        "rainfall_1h_mm": max(0.0, round(r1, 2)),
        "rainfall_3h_mm": max(0.0, round(r3, 2)),
        "rainfall_6h_mm": max(0.0, round(r6, 2)),
        "rainfall_24h_mm": max(0.0, round(r24, 2)),
        "rainfall_72h_mm": max(0.0, round(r72, 2)),
    }
