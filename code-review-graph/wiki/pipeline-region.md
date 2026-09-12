# pipeline-region

## Overview

Directory-based community: ml/pipeline

- **Size**: 32 nodes
- **Cohesion**: 0.0402
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| run_feature_ablation | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/ablation.py | 56-130 |
| compute_ece | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/calibrate.py | 27-38 |
| check_monotonicity | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/calibrate.py | 41-47 |
| calibrate_model | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/calibrate.py | 50-153 |
| load_indofloods_events | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/data_sources/indofloods.py | 27-42 |
| load_indofloods_metadata | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/data_sources/indofloods.py | 45-58 |
| load_indofloods_catchments | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/data_sources/indofloods.py | 61-74 |
| filter_events_by_region | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/data_sources/indofloods.py | 77-150 |
| extract_event_dates | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/data_sources/indofloods.py | 153-187 |
| load_reference_events | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/data_sources/indofloods.py | 190-198 |
| fetch_station_era5 | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/data_sources/open_meteo.py | 48-157 |
| fetch_region_era5 | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/data_sources/open_meteo.py | 160-226 |
| load_region_yaml | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/dataset_builder.py | 48-52 |
| _generate_synthetic_climatology_station | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/dataset_builder.py | 55-63 |
| build_region_dataset | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/dataset_builder.py | 66-194 |
| evaluate_model_holdout | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/evaluate.py | 34-161 |
| engineer_features | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/feature_engineering.py | 43-181 |
| IndependentLabeler | Class | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/independent_labeler.py | 25-202 |
| __init__ | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/independent_labeler.py | 34-37 |
| load_disaster_inventory | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/independent_labeler.py | 39-91 |
| get_region_events | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/independent_labeler.py | 93-121 |
| label_station_forecasting | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/independent_labeler.py | 123-202 |
| build_event_windows | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/label_engineering.py | 25-80 |
| apply_flood_labels | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/label_engineering.py | 83-124 |
| prepare_region | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/prepare_data.py | 23-32 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/prepare_data.py | 35-49 |
| split_region_data | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/splitter.py | 25-134 |
| optimize_threshold | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/threshold_optimizer.py | 25-170 |
| train_region | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/train.py | 57-348 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/train.py | 351-359 |
| train_all | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/train_all_regions.py | 30-89 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/train_all_regions.py | 92-93 |

## Execution Flows

- **main** (criticality: 0.71, depth: 7)
- **main** (criticality: 0.70, depth: 6)
- **main** (criticality: 0.70, depth: 6)
- **acquire_region** (criticality: 0.54, depth: 3)
- **acquire_region** (criticality: 0.54, depth: 3)

## Dependencies

### Outgoing

- `get` (64 edge(s))
- `float` (58 edge(s))
- `round` (56 edge(s))
- `info` (47 edge(s))
- `len` (45 edge(s))
- `int` (26 edge(s))
- `copy` (24 edge(s))
- `sum` (23 edge(s))
- `warning` (20 edge(s))
- `to_datetime` (20 edge(s))
- `str` (19 edge(s))
- `DataFrame` (15 edge(s))
- `print` (15 edge(s))
- `append` (12 edge(s))
- `read_csv` (12 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/data_sources/indofloods.py` (6 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/calibrate.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/acquire_real_regional_data.py::acquire_region` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/acquire_tier2_regional_data.py::acquire_region` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/dataset_builder.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/run_ultimate_scientific_rebuild.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/prepare_data.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/train.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/train_all_regions.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/data_sources/open_meteo.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/save_hp_processed.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_scientific_integrity.py::test_target_predictor_independence` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/independent_labeler.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/label_engineering.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/pipeline/ablation.py` (1 edge(s))
