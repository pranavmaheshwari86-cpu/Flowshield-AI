# models-model

## Overview

Directory-based community: ml/src

- **Size**: 54 nodes
- **Cohesion**: 0.0469
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| load_processed_features | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/data/loader.py | 16-27 |
| load_splits | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/data/loader.py | 30-45 |
| chronological_split | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/data/splitter.py | 10-27 |
| validate_feature_vector | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/data/validator.py | 11-32 |
| validate_feature_ranges | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/data/validator.py | 35-62 |
| perform_error_analysis | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/evaluation/error_analysis.py | 13-75 |
| ModelEvaluator | Class | C:/Users/Pranav/Desktop/Flowshield/ml/src/evaluation/evaluator.py | 20-96 |
| __init__ | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/evaluation/evaluator.py | 27-35 |
| evaluate | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/evaluation/evaluator.py | 37-96 |
| compute_ece | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/evaluation/metrics.py | 21-51 |
| check_monotonicity | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/evaluation/metrics.py | 54-64 |
| calculate_classification_metrics | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/evaluation/metrics.py | 67-122 |
| build_feature_vector | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/features/builder.py | 12-27 |
| FeatureMatrixBuilder | Class | C:/Users/Pranav/Desktop/Flowshield/ml/src/features/builder.py | 30-49 |
| build_vector | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/features/builder.py | 34-35 |
| build_matrix | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/features/builder.py | 38-49 |
| compute_rolling_rainfall | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/features/rainfall_features.py | 11-31 |
| calculate_soil_saturation | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/features/soil_moisture_features.py | 9-17 |
| haversine_distance_meters | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/features/terrain_features.py | 10-21 |
| audit_label_distribution | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/labels/flood_labels.py | 10-23 |
| fit_calibrator | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/calibrate.py | 10-18 |
| ModelExplainer | Class | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/explain.py | 22-131 |
| __init__ | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/explain.py | 28-41 |
| _detect_model_family | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/explain.py | 43-51 |
| explain_prediction | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/explain.py | 53-131 |
| generate_explanations | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/explain.py | 134-147 |
| create_model | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/factory.py | 17-58 |
| ModelFactory | Class | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/factory.py | 61-64 |
| load_inference_artifacts | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/predict.py | 37-97 |
| get_explainer | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/predict.py | 100-105 |
| predict_flood_risk | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/predict.py | 108-217 |
| generate_manifest | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/registry.py | 15-45 |
| RetrainingPipeline | Class | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/retrain.py | 29-202 |
| __init__ | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/retrain.py | 36-42 |
| run | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/retrain.py | 44-202 |
| train_production_champion | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/models/train.py | 23-65 |
| DataQualityAuditor | Class | C:/Users/Pranav/Desktop/Flowshield/ml/src/monitoring/data_quality.py | 18-107 |
| audit_record | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/monitoring/data_quality.py | 24-68 |
| audit_batch | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/monitoring/data_quality.py | 71-107 |
| DriftMonitor | Class | C:/Users/Pranav/Desktop/Flowshield/ml/src/monitoring/drift_monitor.py | 17-90 |
| __init__ | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/monitoring/drift_monitor.py | 20-28 |
| check_drift | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/monitoring/drift_monitor.py | 30-90 |
| compute_sha256 | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/utils/hashing.py | 11-17 |
| verify_file_sha256 | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/utils/hashing.py | 20-23 |
| get_logger | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/utils/logger.py | 10-23 |
| _find_repo_root | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/utils/paths.py | 14-26 |
| get_repo_root | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/utils/paths.py | 29-31 |
| MLPaths | Class | C:/Users/Pranav/Desktop/Flowshield/ml/src/utils/paths.py | 34-126 |
| region_model_dir | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/utils/paths.py | 79-81 |
| region_data_dir | Function | C:/Users/Pranav/Desktop/Flowshield/ml/src/utils/paths.py | 84-86 |

*... and 4 more members.*

## Execution Flows

- **main** (criticality: 0.71, depth: 7)
- **main** (criticality: 0.70, depth: 6)
- **main** (criticality: 0.70, depth: 6)
- **run_full_pipeline** (criticality: 0.64, depth: 1)
- **verify_file_sha256** (criticality: 0.61, depth: 1)
- **main** (criticality: 0.51, depth: 1)
- **main** (criticality: 0.47, depth: 1)
- **main** (criticality: 0.43, depth: 1)
- **main** (criticality: 0.43, depth: 1)
- **build_vector** (criticality: 0.36, depth: 1)
- *... and 2 more flows.*

## Dependencies

### Outgoing

- `round` (55 edge(s))
- `float` (54 edge(s))
- `len` (37 edge(s))
- `get` (28 edge(s))
- `int` (20 edge(s))
- `exists` (19 edge(s))
- `append` (18 edge(s))
- `sum` (17 edge(s))
- `info` (13 edge(s))
- `dump` (9 edge(s))
- `mean` (8 edge(s))
- `max` (8 edge(s))
- `read_csv` (7 edge(s))
- `predict_proba` (7 edge(s))
- `transform` (6 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/ml/scripts/run_pipeline.py::run_full_pipeline` (7 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/src/models/factory.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/src/utils/paths.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_models.py::test_train_production_champion` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_data.py::test_validate_feature_vector` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/scripts/promote_model.py::main` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/src/evaluation/metrics.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_inference.py::test_model_explainer_linear` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/src/models/predict.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_pipeline.py::test_drift_monitor` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/dataset_builder.py::build_region_dataset` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/train.py::train_region` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/src/data/loader.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/tests/test_data.py::test_load_splits` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/src/data/validator.py` (2 edge(s))
