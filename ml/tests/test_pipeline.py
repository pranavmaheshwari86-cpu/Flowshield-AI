"""
ml/tests/test_pipeline.py
Tests for evaluation metrics, ECE calculation, and drift/data quality monitoring.
"""

import pytest
import numpy as np
import pandas as pd

from ml.src.evaluation.metrics import compute_ece, calculate_classification_metrics
from ml.src.monitoring.drift_monitor import DriftMonitor
from ml.src.monitoring.data_quality import DataQualityAuditor
from ml.src.features.feature_definitions import CANONICAL_FEATURE_NAMES


def test_compute_ece():
    y_true = np.array([0, 0, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.8, 0.9])
    ece = compute_ece(y_true, y_prob, n_bins=5)
    assert 0.0 <= ece <= 1.0


def test_calculate_classification_metrics():
    y_true = np.array([0, 0, 0, 1, 1, 1])
    y_prob = np.array([0.02, 0.05, 0.07, 0.15, 0.85, 0.92])
    metrics = calculate_classification_metrics(y_true, y_prob, threshold=0.08)

    assert metrics["catastrophe_recall"] == 1.0
    assert metrics["false_negatives"] == 0
    assert metrics["roc_auc"] > 0.90


def test_data_quality_auditor(valid_feature_dict, corrupt_feature_dict):
    # Single record audit
    res_valid = DataQualityAuditor.audit_record(valid_feature_dict)
    assert res_valid["status"] == "HEALTHY"
    assert res_valid["is_acceptable_for_inference"] is True

    res_corrupt = DataQualityAuditor.audit_record(corrupt_feature_dict)
    assert res_corrupt["status"] == "CRITICAL_CORRUPTION"
    assert res_corrupt["is_acceptable_for_inference"] is False


def test_drift_monitor():
    # Synthetic reference data
    np.random.seed(42)
    ref_rows = []
    for _ in range(60):
        row = {f: float(np.random.uniform(10, 50)) for f in CANONICAL_FEATURE_NAMES}
        ref_rows.append(row)
    ref_df = pd.DataFrame(ref_rows)

    monitor = DriftMonitor(reference_data=ref_df, min_samples=30)

    # Identical distribution
    curr_df = pd.DataFrame([{f: float(np.random.uniform(10, 50)) for f in CANONICAL_FEATURE_NAMES} for _ in range(40)])
    result = monitor.check_drift(curr_df)
    assert result["drift_detected"] is False

    # Strongly shifted distribution (drift)
    drifted_df = pd.DataFrame([{f: float(np.random.uniform(200, 300)) for f in CANONICAL_FEATURE_NAMES} for _ in range(40)])
    result_drift = monitor.check_drift(drifted_df)
    assert result_drift["drift_detected"] is True
    assert len(result_drift["drifted_features"]) > 0
