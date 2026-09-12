def test_simulation_workflow(client):
    # 1. Start simulation
    start_res = client.post("/api/v1/simulation/start", json={"scenario": "GRADUAL_MONSOON", "seed": 26192})
    assert start_res.status_code == 200
    start_data = start_res.json()
    assert start_data["status"] == "RUNNING"
    assert start_data["current_stage"] == 0

    # 2. Step through several steps
    step1_res = client.post("/api/v1/simulation/step")
    assert step1_res.status_code == 200
    step1_data = step1_res.json()
    assert step1_data["substep"] == 1
    assert step1_data["villages_updated"] >= 20

    # 3. Advance to heavy rain / saturation stages
    for _ in range(7):
        client.post("/api/v1/simulation/step")

    state_res = client.get("/api/v1/simulation/state")
    assert state_res.status_code == 200
    state_data = state_res.json()
    assert state_data["current_substep"] == 8
    assert state_data["current_stage"] == 2  # Stage 2: Saturation

    # 4. Verify alerts exist
    alerts_res = client.get("/api/v1/alerts")
    assert alerts_res.status_code == 200

    # 5. Reset simulation
    reset_res = client.post("/api/v1/simulation/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "RESET_SUCCESSFUL"

    # Verify state reset
    post_reset_state = client.get("/api/v1/simulation/state").json()
    assert post_reset_state["current_stage"] == 0
    assert post_reset_state["current_substep"] == 0
