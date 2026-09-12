# providers-risk

## Overview

Directory-based community: apps/api

- **Size**: 465 nodes
- **Cohesion**: 0.1186
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| run_migrations_offline | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/env.py | 22-32 |
| run_migrations_online | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/alembic/env.py | 34-49 |
| Settings | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/config.py | 7-60 |
| assemble_cors_origins | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/config.py | 36-41 |
| Config | Class | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/config.py | 57-60 |
| get_db | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/database.py | 23-29 |
| haversine_distance_km | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/database.py | 32-44 |
| lifespan | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/main.py | 35-48 |
| root | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/main.py | 100-107 |
| global_exception_handler | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/app/main.py | 111-115 |
| setup_test_db | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/conftest.py | 18-29 |
| client | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/conftest.py | 33-35 |
| db_session | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/conftest.py | 39-44 |
| test_ai_risk_inference_with_coords_and_timestamp | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_ai_endpoints.py | 13-35 |
| test_ai_risk_inference_compatibility_path | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_ai_endpoints.py | 38-50 |
| test_ai_risk_inference_with_feature_overrides | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_ai_endpoints.py | 53-69 |
| test_ai_risk_insufficient_data_safety_state | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_ai_endpoints.py | 72-84 |
| test_ai_models_endpoint | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_ai_endpoints.py | 87-97 |
| test_ai_features_metadata | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_ai_endpoints.py | 100-107 |
| test_ai_status_endpoint | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_ai_intelligence.py | 13-20 |
| test_ai_explanation_english | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_ai_intelligence.py | 23-49 |
| test_ai_explanation_hindi | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_ai_intelligence.py | 52-73 |
| test_web_intelligence_feed | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_ai_intelligence.py | 76-85 |
| test_alert_concurrency_stress_test | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_alert_concurrency.py | 16-80 |
| worker_task | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_alert_concurrency.py | 33-55 |
| test_open_meteo_provider_metadata | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_data_providers.py | 17-30 |
| test_open_meteo_provider_normalization_fallback | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_data_providers.py | 33-45 |
| test_cwc_river_gauge_provider_matched_and_unmonitored | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_data_providers.py | 48-77 |
| test_historical_replay_provider_semantic_integrity | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_data_providers.py | 80-100 |
| test_precipitation_forecast_honest_uncertainty | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_forecast_uncertainty.py | 11-36 |
| test_soil_moisture_forecast_prototype_baseline | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_forecast_uncertainty.py | 39-57 |
| test_freshness_evaluation_lifecycle | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_freshness_evaluation.py | 15-43 |
| test_system_status_degradation_tier | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_freshness_evaluation.py | 46-56 |
| test_future_risk_forecast_endpoint | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_future_risk.py | 13-35 |
| test_future_risk_summary | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_future_risk.py | 38-45 |
| test_health_check | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_health.py | 1-8 |
| test_landslide_empirical_prototype_labeling | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_landslide_prototype.py | 12-33 |
| test_landslide_invalid_slope_handling | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_landslide_prototype.py | 36-51 |
| test_geojson_layers | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_map_data.py | 1-14 |
| test_model_status_endpoint | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_mlops_retrain_drift.py | 13-21 |
| test_system_drift_endpoint | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_mlops_retrain_drift.py | 24-31 |
| test_submit_verified_outcome | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_mlops_retrain_drift.py | 34-49 |
| test_list_verified_outcomes | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_mlops_retrain_drift.py | 52-58 |
| test_model_integrity_verification_passes | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_model_integrity.py | 15-26 |
| test_model_integrity_checksum_mismatch_handling | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_model_integrity.py | 29-47 |
| mock_compute | Function | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_model_integrity.py | 35-38 |
| test_canonical_feature_count_and_threshold | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_model_integrity.py | 50-58 |
| test_national_summary | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_national_and_historical.py | 1-9 |
| test_national_river_gauges | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_national_and_historical.py | 12-21 |
| test_historical_events | Test | C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_national_and_historical.py | 24-33 |

*... and 415 more members.*

## Execution Flows

- **setup_test_db** (criticality: 0.69, depth: 6)
- **reset_simulation** (criticality: 0.68, depth: 5)
- **step_simulation** (criticality: 0.67, depth: 4)
- **ingest_custom_telemetry** (criticality: 0.67, depth: 3)
- **sync_live_telemetry** (criticality: 0.66, depth: 3)
- **get_village_future_risk_timeline** (criticality: 0.63, depth: 3)
- **get_regional_forecast_risk_summary** (criticality: 0.63, depth: 3)
- **get_optional_user** (criticality: 0.61, depth: 1)
- **run_prediction** (criticality: 0.60, depth: 3)
- **get_village_detail** (criticality: 0.58, depth: 1)
- *... and 16 more flows.*

## Dependencies

### Outgoing

- `get` (265 edge(s))
- `float` (227 edge(s))
- `round` (154 edge(s))
- `Column` (133 edge(s))
- `query` (126 edge(s))
- `len` (86 edge(s))
- `filter` (83 edge(s))
- `max` (71 edge(s))
- `first` (64 edge(s))
- `append` (62 edge(s))
- `BaseModel` (56 edge(s))
- `String` (56 edge(s))
- `json` (49 edge(s))
- `Depends` (48 edge(s))
- `min` (47 edge(s))

### Incoming

- `json` (45 edge(s))
- `len` (37 edge(s))
- `get` (31 edge(s))
- `post` (18 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/schemas/timeline.py` (16 edge(s))
- `query` (15 edge(s))
- `first` (11 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/seed_national_flood_data.py::seed_national_flood_data` (10 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/schemas/observation.py` (10 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/services/providers/ai_provider.py` (10 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/services/providers/rainfall_provider.py` (9 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_rainfall_service.py` (9 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/seed_db.py::seed_database` (8 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/ai.py` (8 edge(s))
- `isinstance` (8 edge(s))
