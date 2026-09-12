"""
apps/api/app/services/model_integrity.py
Flowshield — Runtime V2 Model Integrity & Checksum Verification Service (v2.4)
Protects the production V2 inference pipeline against silent drift, schema mismatch, or tampering.
"""

import os
import sys
import json
import hashlib
import logging
import joblib
import numpy as np
import pandas as pd
from enum import Enum
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("flowshield.model_integrity")

# Find repository root
def _find_repo_root() -> str:
    curr = os.path.abspath(os.path.dirname(__file__))
    while curr and os.path.splitdrive(curr)[1] not in ["\\", ""]:
        if os.path.exists(os.path.join(curr, "ml", "models")):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))

REPO_ROOT = _find_repo_root()
MODELS_DIR = os.path.join(REPO_ROOT, "ml", "models")

# Add ml path for canonical definitions
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES

# Verified ground truth SHA-256 checksums for Flowshield V2 release
EXPECTED_CHECKSUMS: Dict[str, str] = {
    "v2_selected_model.joblib": "d45af8d35697ad8d749ede5be7b03c33fd6548bbe29748eb7c48c2c9f0d774bb",
    "v2_calibrator.joblib": "c368eacb50f972a53eac2db088d4fc37b51e223d9f404b212546863e03d4f780",
    "v2_preprocessor.joblib": "8e5c8c9570ac3ddc5e5f952da11b9309dc6563ee880b670891efa22c4d19f27c",
    "v2_decision_pipeline.json": "cddbc38cc0de334d3f51095ccce8e35feeb7a62cefb9974536447bde24cc6ea9",
}


class ModelIntegrityState(str, Enum):
    MODEL_READY = "MODEL_READY"
    MODEL_SCHEMA_UNVERIFIED = "MODEL_SCHEMA_UNVERIFIED"
    MODEL_ARTIFACT_INVALID = "MODEL_ARTIFACT_INVALID"
    MODEL_CALIBRATOR_INVALID = "MODEL_CALIBRATOR_INVALID"
    MODEL_FEATURE_SCHEMA_MISMATCH = "MODEL_FEATURE_SCHEMA_MISMATCH"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"


class ModelIntegrityChecker:
    """Performs runtime validation of V2 model artifacts, feature order, and calibration."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelIntegrityChecker, cls).__new__(cls)
            cls._instance.state = ModelIntegrityState.MODEL_UNAVAILABLE
            cls._instance.last_check_details = {}
            cls._instance.model = None
            cls._instance.calibrator = None
            cls._instance.preprocessor = None
            cls._instance.manifest = None
        return cls._instance

    @staticmethod
    def compute_sha256(filepath: str) -> str:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def verify_integrity(self, enforce_checksums: bool = True) -> Tuple[ModelIntegrityState, Dict[str, Any]]:
        """
        Executes all 5 mandatory model integrity checks:
        1. Artifact presence
        2. Checksum match against frozen manifest
        3. Feature order matching canonical 15 features
        4. Deserialization
        5. Smoke inference test
        """
        details = {
            "checks": {},
            "verified_features_count": 0,
            "decision_threshold": None,
            "errors": [],
        }

        # 1. Check artifact presence
        for filename in EXPECTED_CHECKSUMS.keys():
            fpath = os.path.join(MODELS_DIR, filename)
            if not os.path.exists(fpath):
                details["errors"].append(f"Artifact missing: {filename}")
                self.state = ModelIntegrityState.MODEL_ARTIFACT_INVALID
                self.last_check_details = details
                return self.state, details

        # 2. Checksum validation
        details["checks"]["checksums"] = {}
        for filename, expected_hash in EXPECTED_CHECKSUMS.items():
            fpath = os.path.join(MODELS_DIR, filename)
            actual_hash = self.compute_sha256(fpath)
            details["checks"]["checksums"][filename] = {
                "actual": actual_hash,
                "expected": expected_hash,
                "match": actual_hash == expected_hash,
            }
            if enforce_checksums and actual_hash != expected_hash:
                details["errors"].append(f"Checksum mismatch for {filename}")
                self.state = ModelIntegrityState.MODEL_ARTIFACT_INVALID
                self.last_check_details = details
                return self.state, details

        # 3. Load manifest and verify schema
        manifest_path = os.path.join(MODELS_DIR, "v2_decision_pipeline.json")
        try:
            with open(manifest_path, "r") as f:
                self.manifest = json.load(f)
            manifest_features = self.manifest.get("features", [])
            details["verified_features_count"] = len(manifest_features)
            details["decision_threshold"] = self.manifest.get("threshold", 0.08)

            if len(manifest_features) != 15:
                details["errors"].append(f"Manifest features count is {len(manifest_features)}, expected 15")
                self.state = ModelIntegrityState.MODEL_FEATURE_SCHEMA_MISMATCH
                self.last_check_details = details
                return self.state, details

            if manifest_features != CANONICAL_FEATURE_NAMES:
                details["errors"].append("Manifest feature list does not match CANONICAL_FEATURE_NAMES order")
                self.state = ModelIntegrityState.MODEL_SCHEMA_UNVERIFIED
                self.last_check_details = details
                return self.state, details
        except Exception as e:
            details["errors"].append(f"Error parsing manifest: {e}")
            self.state = ModelIntegrityState.MODEL_ARTIFACT_INVALID
            self.last_check_details = details
            return self.state, details

        # 4. Deserialization
        try:
            self.model = joblib.load(os.path.join(MODELS_DIR, "v2_selected_model.joblib"))
            self.calibrator = joblib.load(os.path.join(MODELS_DIR, "v2_calibrator.joblib"))
            self.preprocessor = joblib.load(os.path.join(MODELS_DIR, "v2_preprocessor.joblib"))

            if not hasattr(self.model, "predict_proba"):
                details["errors"].append("Loaded model lacks predict_proba method")
                self.state = ModelIntegrityState.MODEL_ARTIFACT_INVALID
                return self.state, details

            if not hasattr(self.calibrator, "predict_proba"):
                details["errors"].append("Loaded calibrator lacks predict_proba method")
                self.state = ModelIntegrityState.MODEL_CALIBRATOR_INVALID
                return self.state, details

            if not hasattr(self.preprocessor, "transform"):
                details["errors"].append("Loaded preprocessor lacks transform method")
                self.state = ModelIntegrityState.MODEL_ARTIFACT_INVALID
                return self.state, details
        except Exception as e:
            details["errors"].append(f"Deserialization failure: {e}")
            self.state = ModelIntegrityState.MODEL_ARTIFACT_INVALID
            self.last_check_details = details
            return self.state, details

        # 5. Smoke test inference with test vector
        try:
            smoke_features = {f: 10.0 for f in CANONICAL_FEATURE_NAMES}
            smoke_features["elevation_m"] = 800.0
            smoke_features["catchment_slope_deg"] = 22.0
            smoke_features["dist_to_river_m"] = 120.0
            smoke_features["upstream_drainage_sqkm"] = 3500.0

            df_smoke = pd.DataFrame([smoke_features])[CANONICAL_FEATURE_NAMES]
            X_scaled = None
            if hasattr(self.model, "named_steps"):
                raw_prob = float(self.model.predict_proba(df_smoke)[0, 1])
            else:
                X_scaled = self.preprocessor.transform(df_smoke)
                raw_prob = float(self.model.predict_proba(X_scaled)[0, 1])

            est = getattr(self.calibrator, "estimator", None)
            if hasattr(est, "estimator"):
                est = est.estimator
            if hasattr(est, "named_steps"):
                calibrated_prob = float(self.calibrator.predict_proba(df_smoke)[0, 1])
            else:
                if X_scaled is None:
                    X_scaled = self.preprocessor.transform(df_smoke)
                calibrated_prob = float(self.calibrator.predict_proba(X_scaled)[0, 1])

            details["checks"]["smoke_test"] = {
                "raw_probability": round(raw_prob, 4),
                "calibrated_probability": round(calibrated_prob, 4),
                "status": "PASSED",
            }
        except Exception as e:
            details["errors"].append(f"Smoke test inference failed: {e}")
            self.state = ModelIntegrityState.MODEL_ARTIFACT_INVALID
            self.last_check_details = details
            return self.state, details

        self.state = ModelIntegrityState.MODEL_READY
        details["status"] = "ALL_CHECKS_PASSED"
        self.last_check_details = details
        logger.info("Flowshield V2 ModelIntegrityChecker: MODEL_READY confirmed.")
        return self.state, details


model_integrity_checker = ModelIntegrityChecker()
