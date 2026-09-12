"""
apps/api/tests/test_scenario_replay.py
Tests deterministic replay reproducibility and cryptographic state hashing (Phase 7).
"""

import pytest
from apps.api.app.database import SessionLocal
from apps.api.app.services.scenarios.scenario_runner import scenario_replay_runner


def test_scenario_replay_cryptographic_reproducibility():
    """
    Executes the 20-substep scenario twice with the same seed (26192).
    Verifies that the logical clock telemetry trace and SHA-256 fingerprint
    are exactly identical across runs.
    """
    db = SessionLocal()
    try:
        run1 = scenario_replay_runner.run_replay(db, steps=20, seed=26192)
        run2 = scenario_replay_runner.run_replay(db, steps=20, seed=26192)

        # Check basic structural metadata
        assert run1["steps"] == 20
        assert run1["seed"] == 26192
        assert run1["decision_threshold"] == 0.08
        assert len(run1["trace"]) == 20

        # Cryptographic fingerprint equivalence
        digest1 = run1["execution_sha256_digest"]
        digest2 = run2["execution_sha256_digest"]
        assert digest1 == digest2, f"Expected deterministic SHA-256 match, got {digest1} vs {digest2}"

        # Test sensitivity: different seed produces distinct digest
        run_diff_seed = scenario_replay_runner.run_replay(db, steps=20, seed=99999)
        assert run_diff_seed["execution_sha256_digest"] != digest1

        # Check trajectory progression across stages
        step0_probs = [s["calibrated_prob"] for s in run1["trace"][0]["settlements"]]
        step19_probs = [s["calibrated_prob"] for s in run1["trace"][19]["settlements"]]
        avg_prob_step0 = sum(step0_probs) / len(step0_probs)
        avg_prob_step19 = sum(step19_probs) / len(step19_probs)

        # Inception stage has significantly lower average probability than critical stage
        assert avg_prob_step0 < avg_prob_step19
        assert avg_prob_step19 >= 0.95

        # Stage 4 (steps 16-19) triggers critical surge alerts
        stage4_severities = [s["severity"] for s in run1["trace"][19]["settlements"]]
        assert "CRITICAL" in stage4_severities
        assert run1["trace"][19]["alerts_triggered"] >= run1["trace"][0]["alerts_triggered"]

    finally:
        db.close()
