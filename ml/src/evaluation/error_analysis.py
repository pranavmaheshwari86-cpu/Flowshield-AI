"""
ml/src/evaluation/error_analysis.py
Flowshield — Error Analysis & Failure Mode Diagnosis
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np

from ..features.feature_definitions import CANONICAL_FEATURE_NAMES, TARGET_COLUMN


def perform_error_analysis(
    df: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
) -> Dict[str, Any]:
    """
    Diagnoses model failure modes by breaking down False Negatives (missed floods)
    and False Positives (false alarms) across physical features.
    """
    analysis_df = df.copy()
    analysis_df["y_true"] = y_true
    analysis_df["y_pred"] = y_pred
    analysis_df["y_prob"] = y_prob

    # Segment confusion categories
    fn_mask = (analysis_df["y_true"] == 1) & (analysis_df["y_pred"] == 0)
    fp_mask = (analysis_df["y_true"] == 0) & (analysis_df["y_pred"] == 1)
    tp_mask = (analysis_df["y_true"] == 1) & (analysis_df["y_pred"] == 1)
    tn_mask = (analysis_df["y_true"] == 0) & (analysis_df["y_pred"] == 0)

    fn_df = analysis_df[fn_mask]
    fp_df = analysis_df[fp_mask]

    # Feature averages across error classes
    feature_comparison = {}
    for feat in CANONICAL_FEATURE_NAMES:
        if feat in analysis_df.columns:
            feature_comparison[feat] = {
                "fn_mean": round(float(fn_df[feat].mean()), 3) if len(fn_df) > 0 else None,
                "fp_mean": round(float(fp_df[feat].mean()), 3) if len(fp_df) > 0 else None,
                "tp_mean": round(float(analysis_df[tp_mask][feat].mean()), 3) if tp_mask.sum() > 0 else None,
                "overall_mean": round(float(analysis_df[feat].mean()), 3),
            }

    # Identify most severe missed floods (highest true rainfall among FNs)
    severe_misses = []
    if len(fn_df) > 0 and "rainfall_1h" in fn_df.columns:
        worst_fns = fn_df.sort_values(by="rainfall_1h", ascending=False).head(5)
        for _, row in worst_fns.iterrows():
            severe_misses.append({
                "predicted_prob": round(float(row["y_prob"]), 4),
                "rainfall_1h": round(float(row.get("rainfall_1h", 0.0)), 2),
                "rainfall_24h": round(float(row.get("rainfall_24h", 0.0)), 2),
                "soil_moisture": round(float(row.get("soil_moisture", 0.0)), 2),
                "river_distance": round(float(row.get("river_distance", 0.0)), 2),
            })

    return {
        "summary": {
            "total_samples": len(analysis_df),
            "false_negatives_count": int(len(fn_df)),
            "false_positives_count": int(len(fp_df)),
            "true_positives_count": int(tp_mask.sum()),
            "true_negatives_count": int(tn_mask.sum()),
        },
        "feature_comparison": feature_comparison,
        "severe_missed_events": severe_misses,
        "recommendation": (
            "Review soil moisture and rolling rainfall thresholds for False Negatives."
            if len(fn_df) > 0 else "Zero False Negatives detected. Recall is 100%."
        ),
    }
