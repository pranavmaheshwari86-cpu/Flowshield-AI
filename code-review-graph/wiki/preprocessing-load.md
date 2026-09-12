# preprocessing-load

## Overview

Directory-based community: ml/preprocessing

- **Size**: 4 nodes
- **Cohesion**: 0.0968
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| load_raw_dataset | Function | C:/Users/Pranav/Desktop/Flowshield/ml/preprocessing/pipeline.py | 27-33 |
| split_by_event_temporal | Function | C:/Users/Pranav/Desktop/Flowshield/ml/preprocessing/pipeline.py | 36-49 |
| build_preprocessor | Function | C:/Users/Pranav/Desktop/Flowshield/ml/preprocessing/pipeline.py | 52-57 |
| prepare_datasets | Function | C:/Users/Pranav/Desktop/Flowshield/ml/preprocessing/pipeline.py | 60-81 |

## Execution Flows

- **main** (criticality: 0.45, depth: 2)
- **main** (criticality: 0.45, depth: 2)

## Dependencies

### Outgoing

- `print` (3 edge(s))
- `reset_index` (2 edge(s))
- `copy` (2 edge(s))
- `len` (2 edge(s))
- `sum` (2 edge(s))
- `mean` (2 edge(s))
- `Pipeline` (1 edge(s))
- `SimpleImputer` (1 edge(s))
- `StandardScaler` (1 edge(s))
- `exists` (1 edge(s))
- `FileNotFoundError` (1 edge(s))
- `read_csv` (1 edge(s))
- `to_datetime` (1 edge(s))
- `fit_transform` (1 edge(s))
- `transform` (1 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/ml/preprocessing/pipeline.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/evaluation/evaluate_flood_model.py::main` (1 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/training/train_flood_model.py::main` (1 edge(s))
