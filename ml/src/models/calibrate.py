"""
ml/src/models/calibrate.py
Flowshield — Probability Calibration Utility
"""

from typing import Any
from sklearn.calibration import CalibratedClassifierCV


def fit_calibrator(base_estimator: Any, X_cal: Any, y_cal: Any, method: str = "isotonic") -> Any:
    """Fits an isotonic or sigmoid probability calibrator on held-out calibration data."""
    try:
        from sklearn.frozen import FrozenEstimator
        calibrator = CalibratedClassifierCV(estimator=FrozenEstimator(base_estimator), method=method)
    except ImportError:
        calibrator = CalibratedClassifierCV(estimator=base_estimator, method=method, cv="prefit")
    calibrator.fit(X_cal, y_cal)
    return calibrator


# Alias for backward compatibility
calibrate_model = fit_calibrator

