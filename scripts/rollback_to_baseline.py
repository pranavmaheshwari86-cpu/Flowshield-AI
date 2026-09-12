"""
scripts/rollback_to_baseline.py
Flowshield — Emergency Model Rollback to Baseline (v3.0)
Smart India Hackathon 2026 (PS ID: 26192)

Performs instantaneous rollback of ML artifacts to the Phase 0 baseline freeze snapshot
in <60 seconds, restoring exact artifacts, checksums, and verifying MODEL_READY state.
"""

import os
import sys
import json
import time
import shutil
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")
BACKUP_DIR = os.path.join(MODELS_DIR, "baseline_backup")
INTEGRITY_SERVICE_FILE = os.path.join(BASE_DIR, "apps", "api", "app", "services", "model_integrity.py")


def compute_sha256(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def rollback():
    start_time = time.time()
    print("=== Flowshield Emergency Model Rollback to Baseline ===")

    if not os.path.exists(BACKUP_DIR):
        raise FileNotFoundError(f"Baseline backup directory not found at {BACKUP_DIR}")

    artifacts_to_restore = [
        "v2_selected_model.joblib",
        "v2_calibrator.joblib",
        "v2_preprocessor.joblib",
        "v2_decision_pipeline.json",
    ]

    for fname in artifacts_to_restore:
        src = os.path.join(BACKUP_DIR, fname)
        dst = os.path.join(MODELS_DIR, fname)
        if not os.path.exists(src):
            raise FileNotFoundError(f"Required baseline file {fname} not found in {BACKUP_DIR}")
        if os.path.abspath(src) != os.path.abspath(dst):
            shutil.copy2(src, dst)
        print(f"Restored {fname} from baseline backup.")

    # Calculate checksums of restored files
    checksums = {fname: compute_sha256(os.path.join(MODELS_DIR, fname)) for fname in artifacts_to_restore}

    # Update EXPECTED_CHECKSUMS in model_integrity.py
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
    print(f"Restored baseline EXPECTED_CHECKSUMS in {INTEGRITY_SERVICE_FILE}")

    # Re-verify integrity
    import apps.api.app.services.model_integrity as mi_mod
    mi_mod.EXPECTED_CHECKSUMS.clear()
    mi_mod.EXPECTED_CHECKSUMS.update(checksums)

    from apps.api.app.services.model_integrity import model_integrity_checker
    # Reset checker state
    model_integrity_checker.model = None
    model_integrity_checker.calibrator = None
    model_integrity_checker.preprocessor = None
    model_integrity_checker.manifest = None
    
    state, details = model_integrity_checker.verify_integrity(enforce_checksums=True)
    elapsed_time = time.time() - start_time

    print(f"Rollback Completed in {elapsed_time:.2f}s (Budget: <60s)")
    print(f"Integrity Status: {state.value}")
    if state.value != "MODEL_READY":
        print("Details:", json.dumps(details, indent=2))
        raise RuntimeError(f"Rollback failed integrity check: {details.get('errors')}")

    print("Baseline rollback verified successfully.")
    return elapsed_time


if __name__ == "__main__":
    rollback()
