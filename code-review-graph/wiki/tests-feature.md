# tests-feature

## Overview

Directory-based community: ml/tests

- **Size**: 20 nodes
- **Cohesion**: 0.0054
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| valid_feature_dict | Function | C:/Users/Pranav/Desktop/Flowshield/ml/tests/conftest.py | 21-39 |
| corrupt_feature_dict | Function | C:/Users/Pranav/Desktop/Flowshield/ml/tests/conftest.py | 43-49 |
| sample_feature_df | Function | C:/Users/Pranav/Desktop/Flowshield/ml/tests/conftest.py | 53-61 |
| test_load_processed_features | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_data.py | 13-18 |
| test_load_splits | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_data.py | 21-31 |
| test_validate_feature_vector | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_data.py | 34-49 |
| test_validate_feature_ranges | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_data.py | 52-55 |
| test_canonical_feature_count | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_features.py | 20-24 |
| test_physical_bounds_consistency | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_features.py | 27-33 |
| test_station_coordinates | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_features.py | 36-37 |
| test_feature_matrix_builder_bounds_clipping | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_features.py | 40-50 |
| test_predict_flood_risk_valid | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_inference.py | 11-18 |
| test_predict_flood_risk_insufficient_data | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_inference.py | 21-25 |
| test_model_explainer_linear | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_inference.py | 28-40 |
| test_model_factory_architectures | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_models.py | 16-23 |
| test_train_production_champion | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_models.py | 26-57 |
| test_compute_ece | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_pipeline.py | 16-20 |
| test_calculate_classification_metrics | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_pipeline.py | 23-30 |
| test_data_quality_auditor | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_pipeline.py | 33-41 |
| test_drift_monitor | Test | C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_pipeline.py | 44-64 |

## Execution Flows

No execution flows pass through this community.

## Dependencies

### Outgoing

- `len` (16 edge(s))
- `DataFrame` (5 edge(s))
- `range` (4 edge(s))
- `float` (4 edge(s))
- `sample` (4 edge(s))
- `array` (4 edge(s))
- `dict` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/src/data/loader.py::load_splits` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/src/data/validator.py::validate_feature_vector` (3 edge(s))
- `uniform` (3 edge(s))
- `append` (2 edge(s))
- `any` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/src/models/predict.py::predict_flood_risk` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/src/models/factory.py::ModelFactory.create` (2 edge(s))
- `hasattr` (2 edge(s))

### Incoming

- `len` (16 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_data.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_features.py` (4 edge(s))
- `DataFrame` (4 edge(s))
- `sample` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_pipeline.py` (4 edge(s))
- `array` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/tests/conftest.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/src/data/loader.py::load_splits` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/src/data/validator.py::validate_feature_vector` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_inference.py` (3 edge(s))
- `range` (3 edge(s))
- `float` (3 edge(s))
- `uniform` (3 edge(s))
- `dict` (2 edge(s))
