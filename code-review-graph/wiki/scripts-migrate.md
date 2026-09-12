# scripts-migrate

## Overview

Directory-based community: scripts

- **Size**: 18 nodes
- **Cohesion**: 0.0149
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
| migrate | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/migrate_v2_4_landslide.py | 32-40 |
| migrate | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/migrate_v2_4_phase5.py | 19-52 |
| migrate_db | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/migrate_v2_4_prediction_schema.py | 27-54 |
| migrate_db | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/migrate_v2_4_schema.py | 40-65 |
| migrate | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/migrate_v2_4_sync_logs.py | 30-38 |
| compute_voronoi_catchments | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py | 36-81 |
| seed_initial_observations_and_baseline_predictions | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py | 84-173 |
| seed_database | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py | 176-341 |
| seed_national_flood_data | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/seed_national_flood_data.py | 813-998 |
| run_verification | Function | C:/Users/Pranav/Desktop/Flowshield/scripts/verify_all_ai_steps.py | 29-153 |

## Execution Flows

- **setup_test_db** (criticality: 0.69, depth: 6)
- **reset_simulation** (criticality: 0.68, depth: 5)
- **run_verification** (criticality: 0.55, depth: 2)
- **main** (criticality: 0.53, depth: 1)

## Dependencies

### Outgoing

- `print` (69 edge(s))
- `join` (27 edge(s))
- `len` (17 edge(s))
- `get` (17 edge(s))
- `add` (17 edge(s))
- `exists` (15 edge(s))
- `commit` (14 edge(s))
- `execute` (13 edge(s))
- `first` (13 edge(s))
- `filter` (13 edge(s))
- `query` (13 edge(s))
- `round` (11 edge(s))
- `load` (9 edge(s))
- `close` (8 edge(s))
- `open` (6 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/scripts/collect_real_open_data.py` (7 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/ingest_user_data.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/compile_historical_flood_inventory.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/migrate_v2_4_landslide.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/migrate_v2_4_phase5.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/migrate_v2_4_prediction_schema.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/migrate_v2_4_schema.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/migrate_v2_4_sync_logs.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/services/simulation_engine.py::SimulationEngine.reset_simulation` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/seed_national_flood_data.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/verify_all_ai_steps.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/conftest.py::setup_test_db` (1 edge(s))
