# scripts-parse

## Overview

Directory-based community: ml/scripts

- **Size**: 9 nodes
- **Cohesion**: 0.0444
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| parse_args | Function | C:/Users/Pranav/Desktop/Flowshield/ml/scripts/evaluate_model.py | 26-34 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/ml/scripts/evaluate_model.py | 37-94 |
| parse_args | Function | C:/Users/Pranav/Desktop/Flowshield/ml/scripts/promote_model.py | 29-33 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/ml/scripts/promote_model.py | 36-96 |
| parse_args | Function | C:/Users/Pranav/Desktop/Flowshield/ml/scripts/rollback_model.py | 26-29 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/ml/scripts/rollback_model.py | 32-82 |
| run_full_pipeline | Function | C:/Users/Pranav/Desktop/Flowshield/ml/scripts/run_pipeline.py | 31-124 |
| parse_args | Function | C:/Users/Pranav/Desktop/Flowshield/ml/scripts/train_model.py | 29-36 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/ml/scripts/train_model.py | 39-78 |

## Execution Flows

- **run_full_pipeline** (criticality: 0.64, depth: 1)
- **main** (criticality: 0.51, depth: 1)
- **main** (criticality: 0.47, depth: 1)
- **main** (criticality: 0.43, depth: 1)
- **main** (criticality: 0.43, depth: 1)

## Dependencies

### Outgoing

- `print` (33 edge(s))
- `info` (25 edge(s))
- `add_argument` (14 edge(s))
- `exists` (9 edge(s))
- `error` (8 edge(s))
- `Path` (7 edge(s))
- `load` (6 edge(s))
- `exit` (6 edge(s))
- `dump` (6 edge(s))
- `copy2` (5 edge(s))
- `read_csv` (4 edge(s))
- `ArgumentParser` (4 edge(s))
- `mkdir` (4 edge(s))
- `len` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/src/evaluation/evaluator.py::ModelEvaluator` (3 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/ml/scripts/evaluate_model.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/scripts/promote_model.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/scripts/rollback_model.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/scripts/train_model.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/scripts/run_pipeline.py` (2 edge(s))
