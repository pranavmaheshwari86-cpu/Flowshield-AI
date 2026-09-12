"""
ml/src/labels/flood_labels.py
Flowshield — Ground-Truth Flood Labeling & Verification
"""

import pandas as pd
from typing import Dict, Any


def audit_label_distribution(df: pd.DataFrame, label_col: str = "flood_occurred") -> Dict[str, Any]:
    """Computes positive/negative event count and imbalance ratio."""
    counts = df[label_col].value_counts().to_dict()
    total = len(df)
    pos = counts.get(1, counts.get(True, 0))
    neg = counts.get(0, counts.get(False, 0))
    imbalance = round(neg / pos, 2) if pos > 0 else float("inf")
    return {
        "total_samples": total,
        "positive_events": pos,
        "negative_events": neg,
        "prevalence_pct": round((pos / total) * 100, 2) if total > 0 else 0.0,
        "imbalance_ratio": imbalance,
    }
