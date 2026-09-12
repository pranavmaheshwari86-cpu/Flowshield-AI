"""
ml/src/evaluation/__init__.py
Flowshield — Evaluation Package
"""

from .metrics import (
    compute_ece,
    check_monotonicity,
    calculate_classification_metrics,
)
from .evaluator import ModelEvaluator
from .error_analysis import perform_error_analysis

__all__ = [
    "compute_ece",
    "check_monotonicity",
    "calculate_classification_metrics",
    "ModelEvaluator",
    "perform_error_analysis",
]
