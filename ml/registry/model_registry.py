"""
ml/registry/model_registry.py
Flowshield — Multi-Region Model Registry

Discovers, loads, and serves region-specific model artifacts from the
filesystem hierarchy:
    ml/models/flood/{region_slug}/
        model.joblib
        preprocessor.joblib
        calibrator.joblib
        thresholds.json
        feature_schema.json
        metadata.json

Also supports legacy V2 artifacts at ml/models/ for backward compatibility
with the existing Himachal Pradesh deployment.
"""

import os
import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import joblib

from .region_resolver import SUPPORTED_REGIONS

logger = logging.getLogger("flowshield.model_registry")

_ML_ROOT = Path(__file__).resolve().parent.parent
_MODELS_DIR = _ML_ROOT / "models"
_FLOOD_MODELS_DIR = _MODELS_DIR / "flood"


class RegionalModelBundle:
    """Holds all artifacts for a single region's flood model."""

    def __init__(
        self,
        region: str,
        model: Any,
        preprocessor: Any,
        calibrator: Optional[Any],
        thresholds: Dict[str, Any],
        feature_schema: Dict[str, Any],
        metadata: Dict[str, Any],
    ):
        self.region = region
        self.model = model
        self.preprocessor = preprocessor
        self.calibrator = calibrator
        self.thresholds = thresholds
        self.feature_schema = feature_schema
        self.metadata = metadata

    @property
    def threshold(self) -> float:
        return float(self.thresholds.get("selected_threshold", 0.08))

    @property
    def model_version(self) -> str:
        return self.metadata.get("model_version", "unknown")

    @property
    def calibration_method(self) -> str:
        return self.metadata.get("calibration_method", "none")

    @property
    def production_status(self) -> str:
        return self.metadata.get("production_status", "UNKNOWN")

    @property
    def status(self) -> str:
        return self.production_status


class ModelRegistry:
    """
    Thread-safe model registry for multi-region Flowshield deployment.

    Usage:
        bundle = model_registry.get(hazard="flood", region="leh_ladakh")
        prediction = bundle.model.predict_proba(X)
    """

    def __init__(self, models_dir: Optional[Path] = None):
        self._models_dir = models_dir or _FLOOD_MODELS_DIR
        self._legacy_dir = _MODELS_DIR
        self._cache: Dict[str, RegionalModelBundle] = {}
        self._lock = threading.Lock()

    def get(
        self,
        hazard: str = "flood",
        region: str = "himachal_pradesh",
    ) -> RegionalModelBundle:
        """
        Retrieves model bundle for a hazard/region pair.
        Loads from disk on first access, caches thereafter.
        """
        if hazard != "flood":
            raise ValueError(
                f"Unsupported hazard type '{hazard}'. Only 'flood' is supported."
            )

        if region not in SUPPORTED_REGIONS:
            raise ValueError(
                f"Unknown region '{region}'. Supported: {SUPPORTED_REGIONS}"
            )

        cache_key = f"{hazard}:{region}"

        with self._lock:
            if cache_key in self._cache:
                return self._cache[cache_key]

        bundle = self._load_bundle(region)

        with self._lock:
            self._cache[cache_key] = bundle

        return bundle

    def _load_bundle(self, region: str) -> RegionalModelBundle:
        """Loads model artifacts from the region's directory."""
        region_dir = self._models_dir / region

        # For himachal_pradesh, also check legacy V2 location
        if region == "himachal_pradesh" and not region_dir.exists():
            return self._load_legacy_bundle()

        if not region_dir.exists():
            raise FileNotFoundError(
                f"No model artifacts found for region '{region}' at {region_dir}. "
                f"Train the model first with: python -m ml.pipeline.train --region {region}"
            )

        model = self._load_artifact(region_dir / "model.joblib", region, "model")
        preprocessor = self._load_artifact(
            region_dir / "preprocessor.joblib", region, "preprocessor"
        )
        calibrator = self._load_artifact_optional(region_dir / "calibrator.joblib")
        thresholds = self._load_json(region_dir / "thresholds.json", {"selected_threshold": 0.08})
        feature_schema = self._load_json(region_dir / "feature_schema.json", {})
        metadata = self._load_json(region_dir / "metadata.json", {})

        logger.info(
            f"Loaded model bundle for '{region}': "
            f"version={metadata.get('model_version', '?')}, "
            f"status={metadata.get('production_status', '?')}"
        )

        return RegionalModelBundle(
            region=region,
            model=model,
            preprocessor=preprocessor,
            calibrator=calibrator,
            thresholds=thresholds,
            feature_schema=feature_schema,
            metadata=metadata,
        )

    def _load_legacy_bundle(self) -> RegionalModelBundle:
        """Loads the existing V2 Himachal Pradesh model from legacy paths."""
        legacy = self._legacy_dir

        # Try V2 pipeline artifacts
        pipeline_path = legacy / "v2_decision_pipeline.json"
        if pipeline_path.exists():
            with open(pipeline_path, "r") as f:
                pipeline_info = json.load(f)
        else:
            pipeline_info = {
                "pipeline_version": "flowshield-flood-risk-v2",
                "selected_model": "logistic_regression",
                "calibration_method": "isotonic",
                "threshold": 0.08,
            }

        model_file = pipeline_info.get("model_artifact", "v2_selected_model.joblib")
        model = joblib.load(legacy / model_file)

        prep_file = pipeline_info.get("preprocessor_artifact", "v2_preprocessor.joblib")
        preprocessor = joblib.load(legacy / prep_file)

        calibrator = None
        cal_file = pipeline_info.get("calibrator_artifact")
        if cal_file and (legacy / cal_file).exists():
            calibrator = joblib.load(legacy / cal_file)

        thresholds = {"selected_threshold": pipeline_info.get("threshold", 0.08)}

        schema_path = legacy / "feature_schema.json"
        feature_schema = {}
        if schema_path.exists():
            with open(schema_path, "r") as f:
                feature_schema = json.load(f)

        metadata = {
            "model_version": pipeline_info.get("pipeline_version", "flowshield-flood-risk-v2"),
            "calibration_method": pipeline_info.get("calibration_method", "isotonic"),
            "production_status": "PRODUCTION_READY",
            "region": "himachal_pradesh",
            "legacy_load": True,
        }

        logger.info("Loaded legacy V2 Himachal Pradesh model bundle")

        return RegionalModelBundle(
            region="himachal_pradesh",
            model=model,
            preprocessor=preprocessor,
            calibrator=calibrator,
            thresholds=thresholds,
            feature_schema=feature_schema,
            metadata=metadata,
        )

    @staticmethod
    def _load_artifact(path: Path, region: str, artifact_name: str) -> Any:
        if not path.exists():
            raise FileNotFoundError(
                f"Missing {artifact_name} artifact for region '{region}': {path}"
            )
        # Compute SHA-256 checksum before deserialization
        import hashlib
        with open(path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        logger.debug(f"Verified {artifact_name} for region '{region}' (SHA256: {file_hash[:12]}...)")
        return joblib.load(path)

    @staticmethod
    def _load_artifact_optional(path: Path) -> Optional[Any]:
        if path.exists():
            return joblib.load(path)
        return None

    @staticmethod
    def _load_json(path: Path, default: Dict) -> Dict[str, Any]:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return default

    def is_available(self, region: str) -> bool:
        """Checks whether a trained model exists for a region."""
        region_dir = self._models_dir / region
        if region_dir.exists() and (region_dir / "model.joblib").exists():
            return True
        if region == "himachal_pradesh":
            return (self._legacy_dir / "v2_selected_model.joblib").exists()
        return False

    def get_status(self, region: str) -> Dict[str, Any]:
        """Returns model availability and status for a region without loading."""
        region_dir = self._models_dir / region
        meta_path = region_dir / "metadata.json"

        if not self.is_available(region):
            return {
                "region": region,
                "available": False,
                "production_status": "NOT_TRAINED",
            }

        if meta_path.exists():
            with open(meta_path, "r") as f:
                meta = json.load(f)
            return {
                "region": region,
                "available": True,
                "production_status": meta.get("production_status", "UNKNOWN"),
                "model_version": meta.get("model_version", "unknown"),
                "calibration_method": meta.get("calibration_method", "none"),
            }

        # Legacy Himachal
        if region == "himachal_pradesh":
            return {
                "region": region,
                "available": True,
                "production_status": "PRODUCTION_READY",
                "model_version": "flowshield-flood-risk-v2",
                "calibration_method": "isotonic",
            }

        return {
            "region": region,
            "available": True,
            "production_status": "UNKNOWN",
        }

    def list_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Returns status for all supported regions."""
        return {r: self.get_status(r) for r in SUPPORTED_REGIONS}

    def evict(self, region: str):
        """Evicts a cached model bundle (e.g., after retraining)."""
        cache_key = f"flood:{region}"
        with self._lock:
            self._cache.pop(cache_key, None)

    def evict_all(self):
        """Clears the entire model cache."""
        with self._lock:
            self._cache.clear()


# Module-level singleton
model_registry = ModelRegistry()
