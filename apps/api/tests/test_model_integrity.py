"""
apps/api/tests/test_model_integrity.py
Unit tests for ModelIntegrityChecker and frozen V2 artifacts (v2.4).
"""

import pytest
from apps.api.app.services.model_integrity import (
    ModelIntegrityChecker,
    ModelIntegrityState,
    model_integrity_checker,
    EXPECTED_CHECKSUMS,
)


def test_model_integrity_verification_passes():
    """Verify that all frozen V2 model artifacts match their expected SHA-256 checksums."""
    checker = ModelIntegrityChecker()
    state, details = checker.verify_integrity(enforce_checksums=True)

    assert state == ModelIntegrityState.MODEL_READY
    assert details["status"] == "ALL_CHECKS_PASSED"
    assert details["verified_features_count"] == 15
    assert details["decision_threshold"] == 0.08
    assert len(details["errors"]) == 0
    assert "smoke_test" in details["checks"]
    assert details["checks"]["smoke_test"]["status"] == "PASSED"


def test_model_integrity_checksum_mismatch_handling(monkeypatch):
    """Verify that a corrupted checksum triggers MODEL_ARTIFACT_INVALID."""
    checker = ModelIntegrityChecker()

    # Simulate corrupted checksum on one model file
    original_compute = checker.compute_sha256
    def mock_compute(fpath):
        if "v2_selected_model.joblib" in fpath:
            return "bad_tampered_hash_00000000000000000000000000000000000000000000000000"
        return original_compute(fpath)

    monkeypatch.setattr(checker, "compute_sha256", mock_compute)
    state, details = checker.verify_integrity(enforce_checksums=True)

    assert state == ModelIntegrityState.MODEL_ARTIFACT_INVALID
    assert any("Checksum mismatch" in err for err in details["errors"])

    # Reset checker state
    checker.verify_integrity(enforce_checksums=True)


def test_canonical_feature_count_and_threshold():
    """Verify that the decision pipeline manifest strictly defines 15 features and tau=0.08."""
    checker = ModelIntegrityChecker()
    state, details = checker.verify_integrity(enforce_checksums=True)

    assert state == ModelIntegrityState.MODEL_READY
    assert checker.manifest is not None
    assert len(checker.manifest["features"]) == 15
    assert checker.manifest["threshold"] == 0.08
