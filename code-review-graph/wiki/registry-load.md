# registry-load

## Overview

Directory-based community: ml/registry

- **Size**: 42 nodes
- **Cohesion**: 0.2639
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| compute_schema_hash | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/feature_contract.py | 90-97 |
| FeatureContract | Class | C:/Users/Pranav/Desktop/Flowshield/ml/registry/feature_contract.py | 100-187 |
| __init__ | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/feature_contract.py | 106-111 |
| feature_count | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/feature_contract.py | 114-115 |
| validate_feature_order | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/feature_contract.py | 117-133 |
| validate_feature_values | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/feature_contract.py | 135-152 |
| validate_dataset_columns | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/feature_contract.py | 154-164 |
| get_ablation_features | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/feature_contract.py | 166-173 |
| to_schema_dict | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/feature_contract.py | 175-187 |
| RegionalModelBundle | Class | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 36-75 |
| __init__ | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 39-55 |
| threshold | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 58-59 |
| model_version | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 62-63 |
| calibration_method | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 66-67 |
| production_status | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 70-71 |
| status | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 74-75 |
| ModelRegistry | Class | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 78-307 |
| __init__ | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 87-91 |
| get | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 93-123 |
| _load_bundle | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 125-162 |
| _load_legacy_bundle | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 164-218 |
| _load_artifact | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 221-231 |
| _load_artifact_optional | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 234-237 |
| _load_json | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 240-244 |
| is_available | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 246-253 |
| get_status | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 255-292 |
| list_all_status | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 294-296 |
| evict | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 298-302 |
| evict_all | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py | 304-307 |
| get_region_config_path | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/region_resolver.py | 64-66 |
| RegionResolver | Class | C:/Users/Pranav/Desktop/Flowshield/ml/registry/region_resolver.py | 69-140 |
| __init__ | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/region_resolver.py | 72-74 |
| is_valid_region | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/region_resolver.py | 76-77 |
| resolve_from_state | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/region_resolver.py | 79-81 |
| get_display_name | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/region_resolver.py | 83-84 |
| list_regions | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/region_resolver.py | 86-91 |
| load_config | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/region_resolver.py | 93-117 |
| get_stations | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/region_resolver.py | 119-122 |
| get_boundary | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/region_resolver.py | 124-127 |
| get_training_period | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/region_resolver.py | 129-132 |
| get_holdout_period | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/region_resolver.py | 134-137 |
| clear_cache | Function | C:/Users/Pranav/Desktop/Flowshield/ml/registry/region_resolver.py | 139-140 |

## Execution Flows

- **setup_test_db** (criticality: 0.73, depth: 10)
- **setup_test_db** (criticality: 0.73, depth: 10)
- **evaluate_all_settlements** (criticality: 0.73, depth: 9)
- **get_village_detail** (criticality: 0.72, depth: 8)
- **reset_simulation** (criticality: 0.72, depth: 9)
- **run_verification** (criticality: 0.72, depth: 6)
- **trigger_village_prediction** (criticality: 0.72, depth: 8)
- **run_full_verification** (criticality: 0.71, depth: 7)
- **main** (criticality: 0.71, depth: 7)
- **get_village_future_risk_timeline** (criticality: 0.71, depth: 7)
- *... and 25 more flows.*

## Dependencies

### Outgoing

- `exists` (12 edge(s))
- `load` (9 edge(s))
- `len` (7 edge(s))
- `get` (7 edge(s))
- `append` (6 edge(s))
- `open` (6 edge(s))
- `ValueError` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_multi_region.py::test_api_region_detail_and_model_info_endpoints` (4 edge(s))
- `FileNotFoundError` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_zero_fabrication.py::test_chaos_13_uncertainty_band_integrity` (3 edge(s))
- `items` (2 edge(s))
- `float` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_regional_data.py::test_feature_vector_validation` (2 edge(s))
- `hexdigest` (2 edge(s))
- `sha256` (2 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/regional_predictions.py::list_regions` (13 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/inference/regional_predictor.py::RegionalFloodPredictor.predict` (9 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/regional_predictions.py::get_region_details` (8 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/run_full_adversarial_audit.py::main` (8 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/train.py::train_region` (6 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/regional_predictions.py::get_region_model_info` (5 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_multi_region.py::test_api_region_detail_and_model_info_endpoints` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/registry/feature_contract.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/regional_predictions.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/regional_predictions.py::predict_regional_flood` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/services/model_registry.py::ModelRegistryService.get_status_overview` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/tests/test_zero_fabrication.py::test_chaos_13_uncertainty_band_integrity` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/registry/region_resolver.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_regional_data.py::test_feature_vector_validation` (2 edge(s))
