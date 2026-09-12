"""
ml/src/monitoring/data_quality.py
Flowshield — Real-time Telemetry & Batch Data Quality Auditor
"""

from typing import Dict, Any, List, Union
import numpy as np
import pandas as pd

from ..features.feature_definitions import (
    CANONICAL_FEATURE_NAMES,
    FEATURE_METADATA,
    PHYSICAL_MIN_BOUNDS,
    PHYSICAL_MAX_BOUNDS,
)


class DataQualityAuditor:
    """Audits incoming feature dictionaries and batches for physical validity and corruption."""

    MAX_MISSING_RATIO_TOLERANCE = 0.20

    @classmethod
    def audit_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """Audits a single streaming feature record."""
        missing = []
        out_of_bounds = {}
        invalid_types = []

        for feat in CANONICAL_FEATURE_NAMES:
            val = record.get(feat)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                missing.append(feat)
                continue

            try:
                num_val = float(val)
            except (ValueError, TypeError):
                invalid_types.append(feat)
                continue

            min_bound = PHYSICAL_MIN_BOUNDS.get(feat, -1e9)
            max_bound = PHYSICAL_MAX_BOUNDS.get(feat, 1e9)

            if num_val < min_bound or num_val > max_bound:
                out_of_bounds[feat] = {
                    "value": num_val,
                    "min_allowed": min_bound,
                    "max_allowed": max_bound,
                }

        missing_ratio = len(missing) / len(CANONICAL_FEATURE_NAMES)
        is_corrupt = (missing_ratio > cls.MAX_MISSING_RATIO_TOLERANCE) or (len(invalid_types) > 2)

        quality_status = "HEALTHY"
        if is_corrupt:
            quality_status = "CRITICAL_CORRUPTION"
        elif missing_ratio > 0 or len(out_of_bounds) > 0:
            quality_status = "DEGRADED"

        return {
            "status": quality_status,
            "missing_features": missing,
            "missing_ratio": round(float(missing_ratio), 4),
            "out_of_bounds": out_of_bounds,
            "invalid_types": invalid_types,
            "is_acceptable_for_inference": not is_corrupt,
        }

    @classmethod
    def audit_batch(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Audits a batch dataframe against canonical expectations."""
        total_rows = len(df)
        if total_rows == 0:
            return {"status": "EMPTY_BATCH", "total_rows": 0, "health_score": 0.0}

        missing_per_feature = {}
        out_of_bounds_counts = {}

        for feat in CANONICAL_FEATURE_NAMES:
            if feat not in df.columns:
                missing_per_feature[feat] = total_rows
                continue

            series = pd.to_numeric(df[feat], errors="coerce")
            nan_cnt = int(series.isna().sum())
            missing_per_feature[feat] = nan_cnt

            min_b = PHYSICAL_MIN_BOUNDS.get(feat, -1e9)
            max_b = PHYSICAL_MAX_BOUNDS.get(feat, 1e9)
            oob = int(((series < min_b) | (series > max_b)).sum())
            if oob > 0:
                out_of_bounds_counts[feat] = oob

        total_cells = total_rows * len(CANONICAL_FEATURE_NAMES)
        total_missing = sum(missing_per_feature.values())
        total_oob = sum(out_of_bounds_counts.values())

        health_score = max(0.0, 100.0 - ((total_missing + total_oob) / total_cells * 100.0))

        return {
            "status": "HEALTHY" if health_score >= 95.0 else ("DEGRADED" if health_score >= 80.0 else "POOR"),
            "total_rows": total_rows,
            "health_score": round(float(health_score), 2),
            "missing_counts": missing_per_feature,
            "out_of_bounds_counts": out_of_bounds_counts,
        }
