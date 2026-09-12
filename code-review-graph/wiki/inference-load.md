# inference-load

## Overview

Directory-based community: ml/inference

- **Size**: 4 nodes
- **Cohesion**: 0.0278
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| load_inference_artifacts | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py | 38-90 |
| compute_topographic_factor | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py | 93-98 |
| validate_physical_telemetry | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py | 101-143 |
| predict_flood_risk | Function | C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py | 146-287 |

## Execution Flows

- **setup_test_db** (criticality: 0.69, depth: 6)
- **reset_simulation** (criticality: 0.68, depth: 5)
- **step_simulation** (criticality: 0.67, depth: 4)
- **ingest_custom_telemetry** (criticality: 0.67, depth: 3)
- **sync_live_telemetry** (criticality: 0.66, depth: 3)
- **get_village_future_risk_timeline** (criticality: 0.63, depth: 3)
- **get_regional_forecast_risk_summary** (criticality: 0.63, depth: 3)
- **run_prediction** (criticality: 0.60, depth: 3)
- **get_current_model_status** (criticality: 0.56, depth: 1)
- **run_verification** (criticality: 0.55, depth: 2)
- *... and 2 more flows.*

## Dependencies

### Outgoing

- `get` (20 edge(s))
- `float` (12 edge(s))
- `append` (11 edge(s))
- `clip` (7 edge(s))
- `exists` (7 edge(s))
- `max` (6 edge(s))
- `join` (6 edge(s))
- `round` (5 edge(s))
- `load` (4 edge(s))
- `FileNotFoundError` (2 edge(s))
- `isnan` (2 edge(s))
- `predict_proba` (2 edge(s))
- `min` (1 edge(s))
- `open` (1 edge(s))
- `isinstance` (1 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/ml/inference/predict.py` (6 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/model_admin.py::get_current_model_status` (1 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scripts/verify_all_ai_steps.py::run_verification` (1 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/ai.py::compute_ai_risk` (1 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/services/future_risk_service.py::FutureRiskService.predict_future_risk_timeline` (1 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/services/prediction_service.py::PredictionService.predict_full` (1 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/services/timeline_service.py::TimelineService._project_multi_horizons` (1 edge(s))
