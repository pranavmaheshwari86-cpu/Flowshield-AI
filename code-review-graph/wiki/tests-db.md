# tests-db

## Overview

Directory-based community: tests

- **Size**: 37 nodes
- **Cohesion**: 0.0000
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| setup_test_db | Function | C:/Users/Pranav/Desktop/Flowshield/tests/conftest.py | 22-33 |
| client | Function | C:/Users/Pranav/Desktop/Flowshield/tests/conftest.py | 37-39 |
| db_session | Function | C:/Users/Pranav/Desktop/Flowshield/tests/conftest.py | 43-48 |
| test_negative_rainfall_rejected | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_adversarial_telemetry.py | 10-18 |
| test_out_of_bounds_physical_values_rejected | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_adversarial_telemetry.py | 21-35 |
| test_null_and_empty_payload_graceful_handling | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_adversarial_telemetry.py | 38-46 |
| test_sql_injection_resilience | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_adversarial_telemetry.py | 49-66 |
| test_prompt_injection_and_unicode_resilience | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_adversarial_telemetry.py | 69-83 |
| ensure_artifacts | Function | C:/Users/Pranav/Desktop/Flowshield/tests/test_ml_pipeline.py | 19-20 |
| test_15_feature_inference_valid_vectors | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_ml_pipeline.py | 23-76 |
| test_missing_feature_imputation_graceful | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_ml_pipeline.py | 79-91 |
| test_extreme_value_handling | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_ml_pipeline.py | 94-118 |
| test_feature_attribution_determinism | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_ml_pipeline.py | 121-154 |
| test_model_integrity_validation | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_ml_pipeline.py | 157-176 |
| test_model_registry_loads_all_ten_regions | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_multi_region.py | 56-73 |
| test_regional_predictions_all_ten_regions | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_multi_region.py | 76-96 |
| test_backward_compatibility_default_region | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_multi_region.py | 99-114 |
| test_model_adapter_regional_inference | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_multi_region.py | 117-132 |
| test_api_regions_list_endpoint | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_multi_region.py | 135-144 |
| test_api_region_detail_and_model_info_endpoints | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_multi_region.py | 147-173 |
| test_api_predict_regional_endpoint | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_multi_region.py | 176-204 |
| repo_root | Function | C:/Users/Pranav/Desktop/Flowshield/tests/test_regional_data.py | 22-23 |
| test_all_ten_regions_present_and_resolvable | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_regional_data.py | 26-43 |
| test_region_config_files_valid_and_complete | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_regional_data.py | 46-96 |
| test_canonical_15_feature_contract | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_regional_data.py | 99-125 |
| test_schema_hash_deterministic | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_regional_data.py | 128-133 |
| test_feature_vector_validation | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_regional_data.py | 136-166 |
| test_no_synthetic_training_data | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_scientific_integrity.py | 26-36 |
| test_label_provenance | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_scientific_integrity.py | 39-45 |
| test_target_predictor_independence | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_scientific_integrity.py | 48-74 |
| test_temporal_causality | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_scientific_integrity.py | 77-93 |
| test_missing_telemetry_insufficient_data | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_scientific_integrity.py | 96-108 |
| test_unsupported_region_rejection | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_scientific_integrity.py | 111-114 |
| test_feature_schema | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_scientific_integrity.py | 117-121 |
| test_probability_range | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_scientific_integrity.py | 124-135 |
| test_artifact_sha256_verification | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_scientific_integrity.py | 138-156 |
| test_full_20_step_simulation_regression | Test | C:/Users/Pranav/Desktop/Flowshield/tests/test_simulation_regression.py | 12-90 |

## Execution Flows

- **setup_test_db** (criticality: 0.73, depth: 10)

## Dependencies

### Outgoing

- `len` (19 edge(s))
- `json` (14 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py::predict_flood_risk` (12 edge(s))
- `post` (10 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py::ModelRegistry.get` (9 edge(s))
- `exists` (6 edge(s))
- `get` (6 edge(s))
- `isinstance` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/services/model_integrity.py::ModelIntegrityChecker.verify_integrity` (3 edge(s))
- `str` (2 edge(s))
- `any` (2 edge(s))
- `lower` (2 edge(s))
- `raises` (2 edge(s))
- `all` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py::predict_flood_risk_regional` (2 edge(s))

### Incoming

- `len` (19 edge(s))
- `json` (14 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py::predict_flood_risk` (12 edge(s))
- `post` (10 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py::ModelRegistry.get` (9 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_scientific_integrity.py` (9 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_multi_region.py` (7 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_ml_pipeline.py` (6 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_regional_data.py` (6 edge(s))
- `exists` (6 edge(s))
- `get` (6 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_adversarial_telemetry.py` (5 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/conftest.py` (3 edge(s))
- `isinstance` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/services/model_integrity.py::ModelIntegrityChecker.verify_integrity` (3 edge(s))
