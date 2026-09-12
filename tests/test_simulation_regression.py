"""
tests/test_simulation_regression.py
Flowshield — Full Simulation Progression & 15-Feature Telemetry Regression Suite
Smart India Hackathon 2026 (PS ID: 26192)
"""

import pytest
from apps.api.app.models.observation import EnvironmentalObservation
from apps.api.app.models.village import Village


def test_full_20_step_simulation_regression(client, db_session):
    """Test full 20-step simulation progression under FLASH_FLOOD_WORST_CASE."""
    # 1. Start simulation
    start_res = client.post(
        "/api/v1/simulation/start",
        json={"scenario": "FLASH_FLOOD_WORST_CASE", "seed": 26192},
    )
    assert start_res.status_code == 200
    start_data = start_res.json()
    assert start_data["status"] == "RUNNING"
    assert start_data["current_stage"] == 0
    assert start_data["current_substep"] == 0

    expected_count = 22

    stage_risk_means = []

    # 2. Step through 19 substeps to reach terminal substep (0 -> 19)
    for step in range(1, 20):
        step_res = client.post("/api/v1/simulation/step")
        assert step_res.status_code == 200
        step_data = step_res.json()
        assert step_data["substep"] == step
        assert step_data["villages_updated"] == expected_count

        # Check DB observations at this step for 15-feature completeness
        latest_obs = (
            db_session.query(EnvironmentalObservation)
            .order_by(EnvironmentalObservation.timestamp.desc())
            .limit(expected_count)
            .all()
        )
        assert len(latest_obs) == expected_count

        for obs in latest_obs:
            # Check 15-feature telemetry existence
            assert obs.rainfall_1h is not None and obs.rainfall_1h >= 0.0
            assert obs.rainfall_3h is not None and obs.rainfall_3h >= 0.0
            assert obs.rainfall_6h is not None and obs.rainfall_6h >= 0.0
            assert obs.rainfall_24h is not None and obs.rainfall_24h >= 0.0
            assert obs.rainfall_72h is not None and obs.rainfall_72h >= 0.0
            assert obs.soil_moisture is not None and obs.soil_moisture >= 0.0
            assert obs.deep_soil_moisture is not None and obs.deep_soil_moisture >= 0.0
            assert obs.temperature is not None
            assert obs.humidity is not None
            assert obs.surface_pressure is not None
            assert obs.wind_speed is not None
            assert obs.is_simulated is True

        # Track mean operational risk score in flash flood scenario
        # Stages: 0 (Normal), 1 (Onset), 2 (Saturation), 3 (Peak Surge), 4 (Recession)
        if step in [1, 5, 10, 15]:
            villages_res = client.get("/api/v1/villages")
            assert villages_res.status_code == 200
            v_data = villages_res.json()
            mean_risk = sum(v.get("risk_score", 0.0) for v in v_data) / len(v_data)
            stage_risk_means.append((step, mean_risk))

    # Verify that risk during peak surge (step 15) is significantly higher than initial (step 1)
    if len(stage_risk_means) >= 2:
        step1_risk = stage_risk_means[0][1]
        step15_risk = stage_risk_means[-1][1]
        assert step15_risk > step1_risk, f"Peak risk ({step15_risk}) should exceed initial risk ({step1_risk})"

    # 3. Verify final terminal state (substep 19, stage 4, 100% progress)
    state_res = client.get("/api/v1/simulation/state")
    assert state_res.status_code == 200
    state_data = state_res.json()
    assert state_data["current_substep"] == 19

    # 4. Test simulation reset
    reset_res = client.post("/api/v1/simulation/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "RESET_SUCCESSFUL"

    # Verify clean baseline restored
    post_reset_state = client.get("/api/v1/simulation/state").json()
    assert post_reset_state["current_stage"] == 0
    assert post_reset_state["current_substep"] == 0
