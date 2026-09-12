"""
ml/src/models/registry.py
Flowshield — Model Artifact Registry & Manifest Generator
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from ..utils.paths import MLPaths
from ..utils.hashing import compute_sha256


def generate_manifest(
    model_version: str = "2.5.0",
    model_family: str = "CalibratedLogisticRegression",
    status: str = "production",
    metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generates production model manifest with cryptographic checksums."""
    prod_dir = MLPaths.MODELS_PROD_DIR
    
    champion_path = prod_dir / "flood_risk_champion.joblib"
    calibrator_path = prod_dir / "flood_risk_calibrator.joblib"
    preprocessor_path = prod_dir / "flood_risk_preprocessor.joblib"
    
    manifest = {
        "model_version": model_version,
        "model_family": model_family,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "checksums": {
            "flood_risk_champion.joblib": compute_sha256(champion_path) if champion_path.exists() else None,
            "flood_risk_calibrator.joblib": compute_sha256(calibrator_path) if calibrator_path.exists() else None,
            "flood_risk_preprocessor.joblib": compute_sha256(preprocessor_path) if preprocessor_path.exists() else None,
        },
        "metrics": metrics or {},
    }
    
    manifest_path = prod_dir / "MODEL_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    return manifest
