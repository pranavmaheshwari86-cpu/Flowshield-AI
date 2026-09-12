# services-risk

## Overview

Directory-based community: apps/api

- **Size**: 600 nodes
- **Cohesion**: 0.1404
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| run_migrations_offline | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/env.py | 22-32 |
| run_migrations_online | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/env.py | 34-49 |
| upgrade | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/versions/7b1c2b825c38_initial_schema.py | 21-195 |
| downgrade | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/versions/7b1c2b825c38_initial_schema.py | 198-221 |
| upgrade | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/versions/c2d4_v2_4_schema_expansion.py | 18-36 |
| downgrade | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/versions/c2d4_v2_4_schema_expansion.py | 39-56 |
| get_current_user | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/dependencies.py | 13-47 |
| get_optional_user | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/dependencies.py | 50-60 |
| RoleChecker | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/dependencies.py | 63-76 |
| __init__ | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/dependencies.py | 66-67 |
| __call__ | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/dependencies.py | 69-76 |
| hash_password | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/jwt_handler.py | 8-12 |
| verify_password | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/jwt_handler.py | 15-20 |
| create_access_token | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/jwt_handler.py | 23-32 |
| decode_access_token | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/jwt_handler.py | 35-41 |
| Settings | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/config.py | 10-86 |
| resolve_sqlite_path | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/config.py | 25-33 |
| assemble_cors_origins | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/config.py | 51-56 |
| Config | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/config.py | 83-86 |
| get_db | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/database.py | 23-29 |
| haversine_distance_km | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/database.py | 32-44 |
| lifespan | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/main.py | 37-50 |
| root | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/main.py | 106-113 |
| global_exception_handler | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/main.py | 117-121 |
| Alert | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/alert.py | 8-46 |
| LandslideAssessment | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/landslide_assessment.py | 14-28 |
| ModelVersion | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/model_version.py | 16-38 |
| EnvironmentalObservation | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/observation.py | 8-98 |
| rainfall_1h_mm | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/observation.py | 57-58 |
| rainfall_3h_mm | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/observation.py | 61-62 |
| rainfall_6h_mm | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/observation.py | 65-66 |
| rainfall_24h_mm | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/observation.py | 69-70 |
| rainfall_72h_mm | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/observation.py | 73-74 |
| soil_saturation_pct | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/observation.py | 77-78 |
| deep_soil_saturation_pct | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/observation.py | 81-82 |
| temperature_c | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/observation.py | 85-86 |
| relative_humidity_pct | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/observation.py | 89-90 |
| surface_pressure_hpa | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/observation.py | 93-94 |
| wind_speed_kmh | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/observation.py | 97-98 |
| Prediction | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/prediction.py | 8-31 |
| RiskSnapshot | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/risk_snapshot.py | 8-22 |
| River | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/river.py | 7-18 |
| Route | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/route.py | 8-30 |
| Shelter | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/shelter.py | 7-36 |
| available_capacity | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/shelter.py | 29-30 |
| occupancy_percentage | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/shelter.py | 33-36 |
| Simulation | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/simulation.py | 7-21 |
| TelemetrySyncLog | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/telemetry_sync_log.py | 13-22 |
| User | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/user.py | 7-17 |
| VerifiedOutcome | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/verified_outcome.py | 18-41 |

*... and 550 more members.*

## Execution Flows

- **setup_test_db** (criticality: 0.73, depth: 10)
- **setup_test_db** (criticality: 0.73, depth: 10)
- **evaluate_all_settlements** (criticality: 0.73, depth: 9)
- **get_village_detail** (criticality: 0.72, depth: 8)
- **reset_simulation** (criticality: 0.72, depth: 9)
- **trigger_village_prediction** (criticality: 0.72, depth: 8)
- **run_full_verification** (criticality: 0.71, depth: 7)
- **get_village_future_risk_timeline** (criticality: 0.71, depth: 7)
- **get_regional_forecast_risk_summary** (criticality: 0.71, depth: 7)
- **run_prediction** (criticality: 0.71, depth: 7)
- *... and 54 more flows.*

## Dependencies

### Outgoing

- `float` (409 edge(s))
- `get` (365 edge(s))
- `round` (188 edge(s))
- `query` (147 edge(s))
- `Column` (133 edge(s))
- `len` (121 edge(s))
- `filter` (102 edge(s))
- `append` (98 edge(s))
- `max` (93 edge(s))
- `first` (79 edge(s))
- `now` (65 edge(s))
- `BaseModel` (63 edge(s))
- `isoformat` (61 edge(s))
- `min` (57 edge(s))
- `json` (57 edge(s))

### Incoming

- `len` (56 edge(s))
- `json` (53 edge(s))
- `get` (34 edge(s))
- `query` (25 edge(s))
- `timedelta` (22 edge(s))
- `post` (21 edge(s))
- `first` (21 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/schemas/timeline.py` (16 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_zero_fabrication.py` (15 edge(s))
- `filter` (14 edge(s))
- `any` (13 edge(s))
- `commit` (12 edge(s))
- `now` (12 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/seed_national_flood_data.py::seed_national_flood_data` (10 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/schemas/observation.py` (10 edge(s))
