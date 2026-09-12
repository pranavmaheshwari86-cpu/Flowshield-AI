# scripts-compute

## Overview

Directory-based community: scripts

- **Size**: 24 nodes
- **Cohesion**: 0.0182
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| fetch_open_meteo_period | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/collect_real_open_data.py | 139-181 |
| collect_era5_data | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/collect_real_open_data.py | 184-209 |
| engineer_hydrological_features | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/collect_real_open_data.py | 212-264 |
| process_himalayan_flood_catalog | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/collect_real_open_data.py | 267-309 |
| compile_catalog | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/compile_historical_flood_inventory.py | 152-158 |
| compute_sha256 | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/evaluate_final_test_set.py | 41-43 |
| compute_ece | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/evaluate_final_test_set.py | 46-58 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/evaluate_final_test_set.py | 61-315 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/execute_rollback_drill.py | 31-108 |
| generate_drift_baseline | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/generate_drift_baseline.py | 23-75 |
| validate_river_gauge | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/ingest_user_data.py | 22-31 |
| validate_aws_telemetry | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/ingest_user_data.py | 33-40 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/ingest_user_data.py | 42-68 |
| compute_sha256 | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/promote_model.py | 31-33 |
| get_git_commit | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/promote_model.py | 36-43 |
| promote | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/promote_model.py | 46-171 |
| compute_sha256 | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/rollback_to_baseline.py | 26-28 |
| rollback | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/rollback_to_baseline.py | 31-103 |
| compute_voronoi_catchments | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py | 36-81 |
| seed_initial_observations_and_baseline_predictions | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py | 84-173 |
| seed_database | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py | 176-341 |
| seed_national_flood_data | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/seed_national_flood_data.py | 826-1011 |
| run_verification | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/verify_all_ai_steps.py | 29-153 |
| run_full_verification | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/verify_ml_production_integration.py | 37-185 |

## Execution Flows

- **setup_test_db** (criticality: 0.73, depth: 10)
- **setup_test_db** (criticality: 0.73, depth: 10)
- **reset_simulation** (criticality: 0.72, depth: 9)
- **run_verification** (criticality: 0.72, depth: 6)
- **run_full_verification** (criticality: 0.71, depth: 7)
- **main** (criticality: 0.56, depth: 2)
- **main** (criticality: 0.53, depth: 1)
- **main** (criticality: 0.52, depth: 2)
- **rollback** (criticality: 0.47, depth: 2)
- **promote** (criticality: 0.47, depth: 2)
- *... and 1 more flows.*

## Dependencies

### Outgoing

- `print` (119 edge(s))
- `join` (44 edge(s))
- `write` (42 edge(s))
- `round` (40 edge(s))
- `len` (38 edge(s))
- `info` (31 edge(s))
- `float` (27 edge(s))
- `get` (26 edge(s))
- `open` (21 edge(s))
- `exists` (17 edge(s))
- `add` (17 edge(s))
- `first` (16 edge(s))
- `query` (16 edge(s))
- `filter` (15 edge(s))
- `sum` (9 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/scripts/collect_real_open_data.py` (7 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/evaluate_final_test_set.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/ingest_user_data.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/promote_model.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/rollback_to_baseline.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/compile_historical_flood_inventory.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/execute_rollback_drill.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/generate_drift_baseline.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/services/simulation_engine.py::SimulationEngine.reset_simulation` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/seed_national_flood_data.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/verify_all_ai_steps.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/verify_ml_production_integration.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/conftest.py::setup_test_db` (1 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/conftest.py::setup_test_db` (1 edge(s))
