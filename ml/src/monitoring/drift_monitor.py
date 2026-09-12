"""
ml/src/monitoring/drift_monitor.py
Flowshield — Statistical Feature Drift Detector (KS-Test & Wasserstein Distance)
"""

from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, wasserstein_distance

from ..utils.logger import get_logger
from ..features.feature_definitions import CANONICAL_FEATURE_NAMES

logger = get_logger("flowshield.monitoring.drift")


class DriftMonitor:
    """Monitors feature distributions for statistical covariate drift."""

    def __init__(
        self,
        reference_data: pd.DataFrame,
        p_value_threshold: float = 0.01,
        min_samples: int = 50,
    ):
        self.reference_data = reference_data[CANONICAL_FEATURE_NAMES].dropna()
        self.p_value_threshold = p_value_threshold
        self.min_samples = min_samples

    def check_drift(
        self,
        current_data: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Runs Kolmogorov-Smirnov two-sample test and calculates Wasserstein distance
        for each canonical feature between reference and current production data.
        """
        if len(current_data) < self.min_samples:
            return {
                "status": "INSUFFICIENT_SAMPLES",
                "sample_count": len(current_data),
                "min_required": self.min_samples,
                "drift_detected": False,
                "drifted_features": [],
                "feature_reports": {},
            }

        drifted_features: List[str] = []
        feature_reports: Dict[str, Any] = {}

        for feat in CANONICAL_FEATURE_NAMES:
            if feat not in current_data.columns:
                continue

            ref_series = self.reference_data[feat].values
            curr_series = current_data[feat].dropna().values

            if len(curr_series) < 5:
                continue

            # Two-sample Kolmogorov-Smirnov test
            ks_stat, p_val = ks_2samp(ref_series, curr_series)
            
            # Wasserstein (Earth Mover's) Distance
            w_dist = wasserstein_distance(ref_series, curr_series)

            is_drifted = bool(p_val < self.p_value_threshold)
            if is_drifted:
                drifted_features.append(feat)

            feature_reports[feat] = {
                "ks_statistic": round(float(ks_stat), 4),
                "p_value": round(float(p_val), 6),
                "wasserstein_distance": round(float(w_dist), 4),
                "is_drifted": is_drifted,
                "ref_mean": round(float(np.mean(ref_series)), 3),
                "curr_mean": round(float(np.mean(curr_series)), 3),
            }

        drift_ratio = len(drifted_features) / len(CANONICAL_FEATURE_NAMES)
        overall_drift = drift_ratio > 0.20  # More than 20% of features drifted

        return {
            "status": "DRIFT_DETECTED" if overall_drift else "STABLE",
            "drift_detected": overall_drift,
            "drift_ratio": round(float(drift_ratio), 4),
            "drifted_features": drifted_features,
            "sample_count": len(current_data),
            "feature_reports": feature_reports,
        }
