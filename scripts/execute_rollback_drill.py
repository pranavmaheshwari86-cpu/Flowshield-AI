"""
scripts/execute_rollback_drill.py
Flowshield — Disaster Recovery & Rollback Drill Automation (Phase 23)
Smart India Hackathon 2026 (PS ID: 26192)

Executes controlled chaos experiment simulating model corruption,
verifies detection by ModelIntegrityChecker, executes emergency rollback,
validates MTTR < 60s, and re-promotes production champion.
"""

import os
import sys
import json
import time
import shutil
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from apps.api.app.services.model_integrity import model_integrity_checker, ModelIntegrityState
from scripts.rollback_to_baseline import rollback as execute_baseline_rollback
from scripts.promote_model import promote as execute_champion_promotion

MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")
REPORTS_DIR = os.path.join(BASE_DIR, "ml", "reports")
TARGET_FILE = os.path.join(MODELS_DIR, "v2_selected_model.joblib")


def main():
    print("================================================================")
    print(" FLOWSHIELD DISASTER RECOVERY & ROLLBACK DRILL (PHASE 23)")
    print("================================================================")

    # 1. Verify healthy initial state
    init_state, init_details = model_integrity_checker.verify_integrity(enforce_checksums=True)
    assert init_state == ModelIntegrityState.MODEL_READY, f"Initial state must be MODEL_READY, got {init_state}"
    print("Pre-drill Health Check: MODEL_READY")

    # 2. Chaos Injection: Intentionally corrupt model artifact
    print("\n--- INJECTING CONTROLLED ARTIFACT CORRUPTION ---")
    with open(TARGET_FILE, "wb") as f:
        f.write(b"CORRUPTED_MODEL_ARTIFACT_FLOWSHIELD_CHAOS_DRILL_SIMULATION")

    t_corrupt_detect_start = time.perf_counter()
    detect_state, detect_details = model_integrity_checker.verify_integrity(enforce_checksums=True)
    detect_latency_ms = (time.perf_counter() - t_corrupt_detect_start) * 1000.0

    print(f"Tamper Detection Latency: {detect_latency_ms:.2f}ms")
    print(f"Integrity State under Attack: {detect_state.value}")
    assert detect_state == ModelIntegrityState.MODEL_ARTIFACT_INVALID, f"Expected MODEL_ARTIFACT_INVALID, got {detect_state}"
    print("Integrity violation caught successfully!")

    # 3. Trigger Emergency Rollback
    print("\n--- TRIGGERING EMERGENCY ROLLBACK TO PHASE 0 BASELINE ---")
    t_rollback_start = time.time()
    rollback_elapsed = execute_baseline_rollback()
    t_total_rollback = time.time() - t_rollback_start

    print(f"Rollback Execution Completed in {t_total_rollback:.2f}s (Budget: <60s)")
    assert t_total_rollback < 60.0, f"MTTR exceeded 60s budget: {t_total_rollback}s"

    rb_state, rb_details = model_integrity_checker.verify_integrity(enforce_checksums=True)
    assert rb_state == ModelIntegrityState.MODEL_READY, f"Post-rollback state must be MODEL_READY, got {rb_state}"
    print("Post-rollback Health Check: MODEL_READY (Baseline Restored)")

    # 4. Re-promote Champion Model to Production
    print("\n--- RE-PROMOTING V2 PRODUCTION CHAMPION ---")
    t_promo_start = time.time()
    execute_champion_promotion()
    t_promo_elapsed = time.time() - t_promo_start
    print(f"Champion Re-promotion Completed in {t_promo_elapsed:.2f}s")

    final_state, final_details = model_integrity_checker.verify_integrity(enforce_checksums=True)
    assert final_state == ModelIntegrityState.MODEL_READY, f"Final state must be MODEL_READY, got {final_state}"
    print("Final Production Health Check: MODEL_READY (V2 Champion Active)")

    # 5. Write Rollback Drill Report
    drill_report = {
        "drill_id": "DRILL-DR-CHAOS-PHASE23",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "experiment": "Simulated catastrophic model artifact bit-rot & checksum invalidation",
        "detection": {
            "detection_latency_ms": round(detect_latency_ms, 2),
            "state_detected": detect_state.value,
            "errors_flagged": detect_details.get("errors", []),
        },
        "recovery": {
            "mttr_seconds": round(t_total_rollback, 2),
            "mttr_budget_seconds": 60.0,
            "status": "RECOVERY_SUCCESSFUL",
            "restored_baseline_state": rb_state.value,
        },
        "re_promotion": {
            "re_promotion_seconds": round(t_promo_elapsed, 2),
            "final_production_state": final_state.value,
        },
        "verdict": "DRILL_PASSED_DISASTER_RECOVERY_VERIFIED",
    }

    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, "rollback_drill_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(drill_report, f, indent=2)

    print(f"\nWrote Disaster Recovery Drill Report to: {report_path}")
    print("ALL DISASTER RECOVERY & ROLLBACK GATES VERIFIED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
