# scripts-catalog

## Overview

Directory-based community: scripts

- **Size**: 12 nodes
- **Cohesion**: 0.0156
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| fetch_open_meteo_period | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/collect_real_open_data.py | 139-181 |
| collect_era5_data | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/collect_real_open_data.py | 184-209 |
| engineer_hydrological_features | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/collect_real_open_data.py | 212-264 |
| process_himalayan_flood_catalog | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/collect_real_open_data.py | 267-309 |
| compile_catalog | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/compile_historical_flood_inventory.py | 152-158 |
| validate_river_gauge | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/ingest_user_data.py | 22-31 |
| validate_aws_telemetry | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/ingest_user_data.py | 33-40 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/ingest_user_data.py | 42-68 |
| compute_voronoi_catchments | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py | 36-81 |
| seed_initial_observations_and_baseline_predictions | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py | 84-173 |
| seed_database | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py | 176-326 |
| run_verification | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/verify_all_ai_steps.py | 29-150 |

## Execution Flows

- **setup_test_db** (criticality: 0.70, depth: 4)
- **reset_simulation** (criticality: 0.68, depth: 3)
- **main** (criticality: 0.53, depth: 1)
- **run_verification** (criticality: 0.51, depth: 2)

## Dependencies

### Outgoing

- `print` (52 edge(s))
- `join` (26 edge(s))
- `get` (16 edge(s))
- `len` (14 edge(s))
- `exists` (10 edge(s))
- `add` (9 edge(s))
- `load` (8 edge(s))
- `round` (6 edge(s))
- `first` (6 edge(s))
- `filter` (6 edge(s))
- `query` (6 edge(s))
- `commit` (6 edge(s))
- `open` (6 edge(s))
- `sum` (5 edge(s))
- `read_csv` (5 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/scripts/collect_real_open_data.py` (7 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/ingest_user_data.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/compile_historical_flood_inventory.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/verify_all_ai_steps.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/conftest.py::setup_test_db` (1 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/services/simulation_engine.py::SimulationEngine.reset_simulation` (1 edge(s))
