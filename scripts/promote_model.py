"""
scripts/promote_model.py
Flowshield — Model Promotion & Checksum Governance Automation (v3.0)
Smart India Hackathon 2026 (PS ID: 26192)

Promotes verified tournament winner and calibrator to production artifacts,
calculates SHA-256 checksums, generates MODEL_MANIFEST.json, and atomically
updates EXPECTED_CHECKSUMS in model_integrity.py.
"""

import os
import sys
import json
import shutil
import hashlib
import subprocess
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES

MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")
TOURNAMENT_DIR = os.path.join(MODELS_DIR, "tournament")
PRODUCTION_DIR = os.path.join(MODELS_DIR, "production")
INTEGRITY_SERVICE_FILE = os.path.join(BASE_DIR, "apps", "api", "app", "services", "model_integrity.py")


def compute_sha256(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=BASE_DIR)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown_commit"


def promote():
    print("=== Flowshield Production Model Promotion ===")
    os.makedirs(PRODUCTION_DIR, exist_ok=True)

    # Source candidate files
    champion_candidate = os.path.join(TOURNAMENT_DIR, "candidate_logisticregression.joblib")
    calibrator_candidate = os.path.join(TOURNAMENT_DIR, "calibrator_isotonic.joblib")
    preprocessor_source = os.path.join(MODELS_DIR, "v2_preprocessor.joblib")

    if not os.path.exists(champion_candidate):
        raise FileNotFoundError(f"Champion candidate not found at {champion_candidate}")
    if not os.path.exists(calibrator_candidate):
        raise FileNotFoundError(f"Calibrator candidate not found at {calibrator_candidate}")
    if not os.path.exists(preprocessor_source):
        raise FileNotFoundError(f"Preprocessor not found at {preprocessor_source}")

    # 1. Copy to production versioned artifacts
    prod_champion = os.path.join(PRODUCTION_DIR, "flood_risk_champion.joblib")
    prod_calibrator = os.path.join(PRODUCTION_DIR, "flood_risk_calibrator.joblib")
    prod_preprocessor = os.path.join(PRODUCTION_DIR, "flood_risk_preprocessor.joblib")

    shutil.copy2(champion_candidate, prod_champion)
    shutil.copy2(calibrator_candidate, prod_calibrator)
    shutil.copy2(preprocessor_source, prod_preprocessor)

    # 2. Copy to active runtime artifacts in ml/models/
    runtime_model = os.path.join(MODELS_DIR, "v2_selected_model.joblib")
    runtime_calibrator = os.path.join(MODELS_DIR, "v2_calibrator.joblib")
    runtime_preprocessor = os.path.join(MODELS_DIR, "v2_preprocessor.joblib")

    if os.path.abspath(champion_candidate) != os.path.abspath(runtime_model):
        shutil.copy2(champion_candidate, runtime_model)
    if os.path.abspath(calibrator_candidate) != os.path.abspath(runtime_calibrator):
        shutil.copy2(calibrator_candidate, runtime_calibrator)
    if os.path.abspath(preprocessor_source) != os.path.abspath(runtime_preprocessor):
        shutil.copy2(preprocessor_source, runtime_preprocessor)

    # 3. Calculate Checksums
    checksums = {
        "v2_selected_model.joblib": compute_sha256(runtime_model),
        "v2_calibrator.joblib": compute_sha256(runtime_calibrator),
        "v2_preprocessor.joblib": compute_sha256(runtime_preprocessor),
    }

    # 4. Create decision pipeline manifest
    pipeline_info = {
        "model_id": "flowshield-flood-risk-v2",
        "model_name": "Mandi Basin Flash Flood Decision Support Champion",
        "algorithm": "LogisticRegression(C=0.1, class_weight='balanced', solver='liblinear')",
        "calibration": "IsotonicRegression(out_of_bounds='clip')",
        "threshold": 0.08,
        "features": CANONICAL_FEATURE_NAMES,
        "feature_count": len(CANONICAL_FEATURE_NAMES),
        "model_artifact": "v2_selected_model.joblib",
        "calibrator_artifact": "v2_calibrator.joblib",
        "preprocessor_artifact": "v2_preprocessor.joblib",
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "checksums": checksums,
        "governance": "PS ID 26192 Certified Scientific Pipeline",
    }

    decision_pipeline_path = os.path.join(MODELS_DIR, "v2_decision_pipeline.json")
    with open(decision_pipeline_path, "w", encoding="utf-8") as f:
        json.dump(pipeline_info, f, indent=2)

    checksums["v2_decision_pipeline.json"] = compute_sha256(decision_pipeline_path)

    # Update pipeline_info with its own checksum and save
    pipeline_info["checksums"] = checksums
    with open(decision_pipeline_path, "w", encoding="utf-8") as f:
        json.dump(pipeline_info, f, indent=2)
    # Recalculate manifest hash
    checksums["v2_decision_pipeline.json"] = compute_sha256(decision_pipeline_path)

    # 5. Write Production Model Manifest
    prod_manifest_path = os.path.join(PRODUCTION_DIR, "MODEL_MANIFEST.json")
    with open(prod_manifest_path, "w", encoding="utf-8") as f:
        json.dump(pipeline_info, f, indent=2)

    print("Calculated Checksums:")
    for k, v in checksums.items():
        print(f"  {k}: {v}")

    # 6. Update EXPECTED_CHECKSUMS in model_integrity.py
    with open(INTEGRITY_SERVICE_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    start_token = "EXPECTED_CHECKSUMS: Dict[str, str] = {"
    end_token = "}\n"

    start_idx = content.find(start_token)
    if start_idx == -1:
        raise ValueError(f"Could not locate EXPECTED_CHECKSUMS in {INTEGRITY_SERVICE_FILE}")

    end_idx = content.find(end_token, start_idx) + len(end_token)

    new_dict_str = "EXPECTED_CHECKSUMS: Dict[str, str] = {\n"
    for k, v in checksums.items():
        new_dict_str += f'    "{k}": "{v}",\n'
    new_dict_str += "}\n"

    new_content = content[:start_idx] + new_dict_str + content[end_idx:]

    with open(INTEGRITY_SERVICE_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Updated EXPECTED_CHECKSUMS in {INTEGRITY_SERVICE_FILE}")

    # 7. Run Verification Test
    import apps.api.app.services.model_integrity as mi_mod
    mi_mod.EXPECTED_CHECKSUMS.clear()
    mi_mod.EXPECTED_CHECKSUMS.update(checksums)

    from apps.api.app.services.model_integrity import model_integrity_checker
    model_integrity_checker.model = None
    model_integrity_checker.calibrator = None
    model_integrity_checker.preprocessor = None
    model_integrity_checker.manifest = None

    state, details = model_integrity_checker.verify_integrity(enforce_checksums=True)
    print(f"Model Integrity State: {state.value}")
    if state.value != "MODEL_READY":
        print("Verification Details:", json.dumps(details, indent=2))
        raise RuntimeError(f"Integrity check failed after promotion: {details.get('errors')}")

    print("Promotion completed successfully! Pipeline is MODEL_READY.")


if __name__ == "__main__":
    promote()
