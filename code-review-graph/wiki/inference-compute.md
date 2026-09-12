# inference-compute

## Overview

Directory-based community: ml/inference

- **Size**: 20 nodes
- **Cohesion**: 0.0856
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| ModelExplainer | Class | C:/Users/Pranav/Desktop/Flowshield/ml/inference/explain.py | 29-184 |
| __init__ | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/explain.py | 35-48 |
| _detect_model_family | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/explain.py | 50-58 |
| explain_prediction | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/explain.py | 60-94 |
| _explain_linear | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/explain.py | 96-154 |
| _explain_shap | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/explain.py | 156-184 |
| load_inference_artifacts | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py | 43-98 |
| get_explainer | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py | 101-106 |
| compute_topographic_factor | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py | 109-114 |
| validate_physical_telemetry | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py | 117-159 |
| compute_composite_risk | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py | 162-198 |
| predict_flood_risk_regional | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py | 201-206 |
| predict_flood_risk | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py | 209-365 |
| validate_regional_telemetry | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/regional_predictor.py | 32-48 |
| compute_topographic_factor | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/regional_predictor.py | 51-56 |
| compute_composite_risk | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/regional_predictor.py | 59-97 |
| RegionalFloodPredictor | Class | C:/Users/Pranav/Desktop/Flowshield/ml/inference/regional_predictor.py | 100-262 |
| __init__ | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/regional_predictor.py | 105-107 |
| _get_explainer | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/regional_predictor.py | 109-116 |
| predict | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/regional_predictor.py | 118-262 |

## Execution Flows

- **setup_test_db** (criticality: 0.73, depth: 10)
- **setup_test_db** (criticality: 0.73, depth: 10)
- **evaluate_all_settlements** (criticality: 0.73, depth: 9)
- **get_village_detail** (criticality: 0.72, depth: 8)
- **reset_simulation** (criticality: 0.72, depth: 9)
- **run_verification** (criticality: 0.72, depth: 6)
- **trigger_village_prediction** (criticality: 0.72, depth: 8)
- **run_full_verification** (criticality: 0.71, depth: 7)
- **get_village_future_risk_timeline** (criticality: 0.71, depth: 7)
- **get_regional_forecast_risk_summary** (criticality: 0.71, depth: 7)
- *... and 11 more flows.*

## Dependencies

### Outgoing

- `float` (41 edge(s))
- `get` (33 edge(s))
- `round` (22 edge(s))
- `clip` (18 edge(s))
- `hasattr` (11 edge(s))
- `append` (10 edge(s))
- `max` (9 edge(s))
- `predict_proba` (8 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/registry/model_registry.py::ModelRegistry.get` (8 edge(s))
- `exists` (7 edge(s))
- `join` (6 edge(s))
- `isnan` (5 edge(s))
- `len` (4 edge(s))
- `load` (4 edge(s))
- `transform` (4 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py` (9 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/inference/regional_predictor.py` (5 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/run_ultimate_scientific_rebuild.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/evidence_audit_runner.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_multi_region.py::test_backward_compatibility_default_region` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/run_full_adversarial_audit.py::main` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_ml_pipeline.py::test_15_feature_inference_valid_vectors` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_ml_pipeline.py::test_feature_attribution_determinism` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_multi_region.py::test_regional_predictions_all_ten_regions` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/inference/explain.py` (1 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/services/prediction_service.py::PredictionService._compute_feature_attributions` (1 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/model_admin.py::get_current_model_status` (1 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/evaluate_cross_region_transfer.py` (1 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/evaluate_final_test_set.py::main` (1 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/tests/test_ml_pipeline.py::ensure_artifacts` (1 edge(s))
