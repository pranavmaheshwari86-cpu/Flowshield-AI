# services-simulation

## Overview

Directory-based community: apps/api/app

- **Size**: 229 nodes
- **Cohesion**: 0.0906
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| Settings | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/config.py | 7-50 |
| assemble_cors_origins | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/config.py | 36-41 |
| Config | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/config.py | 47-50 |
| get_db | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/database.py | 23-29 |
| haversine_distance_km | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/database.py | 32-44 |
| lifespan | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/main.py | 31-44 |
| root | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/main.py | 91-98 |
| global_exception_handler | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/main.py | 102-106 |
| get_current_user | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/dependencies.py | 13-47 |
| get_optional_user | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/dependencies.py | 50-60 |
| RoleChecker | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/dependencies.py | 63-76 |
| __init__ | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/dependencies.py | 66-67 |
| __call__ | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/dependencies.py | 69-76 |
| hash_password | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/jwt_handler.py | 8-12 |
| verify_password | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/jwt_handler.py | 15-20 |
| create_access_token | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/jwt_handler.py | 23-32 |
| decode_access_token | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/jwt_handler.py | 35-41 |
| Alert | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/alert.py | 8-46 |
| LandslideAssessment | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/landslide_assessment.py | 14-28 |
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
| Village | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/village.py | 8-37 |
| RiskZone | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/models/village.py | 40-50 |
| get_real_hydrology_df | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/ai.py | 34-43 |
| find_nearest_real_observation | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/ai.py | 46-100 |
| compute_ai_risk | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/ai.py | 104-157 |
| get_model_benchmarks | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/ai.py | 161-166 |
| get_canonical_features | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/ai.py | 170-176 |
| list_alerts | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/alerts.py | 15-52 |
| acknowledge_alert | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/alerts.py | 57-81 |

*... and 179 more members.*

## Execution Flows

- **setup_test_db** (criticality: 0.69, depth: 6)
- **reset_simulation** (criticality: 0.68, depth: 5)
- **step_simulation** (criticality: 0.67, depth: 4)
- **sync_live_telemetry** (criticality: 0.66, depth: 3)
- **get_optional_user** (criticality: 0.61, depth: 1)
- **run_prediction** (criticality: 0.60, depth: 3)
- **get_village_detail** (criticality: 0.58, depth: 1)
- **normalize** (criticality: 0.48, depth: 1)
- **compute_ai_risk** (criticality: 0.48, depth: 2)
- **get_weather_forecast** (criticality: 0.45, depth: 2)
- *... and 6 more flows.*

## Dependencies

### Outgoing

- `float` (130 edge(s))
- `get` (119 edge(s))
- `query` (87 edge(s))
- `round` (66 edge(s))
- `filter` (64 edge(s))
- `first` (40 edge(s))
- `append` (38 edge(s))
- `Depends` (37 edge(s))
- `all` (32 edge(s))
- `BaseModel` (32 edge(s))
- `uniform` (32 edge(s))
- `max` (26 edge(s))
- `clip` (26 edge(s))
- `order_by` (23 edge(s))
- `now` (22 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/scripts/seed_national_flood_data.py::seed_national_flood_data` (10 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/schemas/observation.py` (10 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py::seed_database` (8 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py::seed_initial_observations_and_baseline_predictions` (6 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/schemas/village.py` (6 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/ai.py` (5 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/routes.py` (5 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/simulation.py` (5 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/schemas/hazard.py` (5 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/schemas/route.py` (5 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/services/model_integrity.py` (5 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_server_rbac.py::test_roles` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/auth/jwt_handler.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/main.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/schemas/auth.py` (4 edge(s))
