# retraining-retrain-pipeline

## Overview

Directory-based community: ml/retraining

- **Size**: 2 nodes
- **Cohesion**: 0.0132
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| RetrainPipeline | Class | C:/Users/Pranav/Desktop/Flowshield/ml/retraining/retrain_pipeline.py | 50-194 |
| run_retrain | Function | C:/Users/Pranav/Desktop/Flowshield/ml/retraining/retrain_pipeline.py | 55-194 |

## Execution Flows

- **trigger_model_retraining** (criticality: 0.56, depth: 1)

## Dependencies

### Outgoing

- `float` (9 edge(s))
- `round` (7 edge(s))
- `len` (5 edge(s))
- `int` (4 edge(s))
- `get` (4 edge(s))
- `join` (3 edge(s))
- `dump` (3 edge(s))
- `exists` (2 edge(s))
- `isoformat` (2 edge(s))
- `info` (2 edge(s))
- `fillna` (2 edge(s))
- `astype` (2 edge(s))
- `fit` (2 edge(s))
- `now` (1 edge(s))
- `read_csv` (1 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/ml/retraining/retrain_pipeline.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/apps/api/app/routers/model_admin.py::trigger_model_retraining` (1 edge(s))
