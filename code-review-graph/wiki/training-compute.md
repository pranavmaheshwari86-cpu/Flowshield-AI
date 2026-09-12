# training-compute

## Overview

Directory-based community: ml/training

- **Size**: 14 nodes
- **Cohesion**: 0.0199
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| compute_ece | Function | C:/Users/Pranav/Desktop/Flowshield/ml/training/run_calibration.py | 24-34 |
| check_monotonicity | Function | C:/Users/Pranav/Desktop/Flowshield/ml/training/run_calibration.py | 37-45 |
| run_calibration | Function | C:/Users/Pranav/Desktop/Flowshield/ml/training/run_calibration.py | 48-135 |
| run_threshold_optimization | Function | C:/Users/Pranav/Desktop/Flowshield/ml/training/run_threshold_optimization.py | 22-127 |
| compute_ece | Function | C:/Users/Pranav/Desktop/Flowshield/ml/training/run_tournament.py | 39-49 |
| run_tournament | Function | C:/Users/Pranav/Desktop/Flowshield/ml/training/run_tournament.py | 52-214 |
| compute_ece | Function | C:/Users/Pranav/Desktop/Flowshield/ml/training/study_model_selection.py | 65-86 |
| perform_three_way_split | Function | C:/Users/Pranav/Desktop/Flowshield/ml/training/study_model_selection.py | 89-107 |
| sweep_thresholds | Function | C:/Users/Pranav/Desktop/Flowshield/ml/training/study_model_selection.py | 110-144 |
| compute_full_metrics | Function | C:/Users/Pranav/Desktop/Flowshield/ml/training/study_model_selection.py | 147-175 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/ml/training/study_model_selection.py | 178-747 |
| _make_calibrator | Function | C:/Users/Pranav/Desktop/Flowshield/ml/training/study_model_selection.py | 299-304 |
| calculate_metrics | Function | C:/Users/Pranav/Desktop/Flowshield/ml/training/train_flood_model.py | 51-77 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/ml/training/train_flood_model.py | 80-229 |

## Execution Flows

- **main** (criticality: 0.45, depth: 2)
- **run_calibration** (criticality: 0.36, depth: 1)
- **run_tournament** (criticality: 0.36, depth: 1)
- **main** (criticality: 0.36, depth: 1)

## Dependencies

### Outgoing

- `print` (140 edge(s))
- `round` (72 edge(s))
- `float` (68 edge(s))
- `int` (36 edge(s))
- `join` (31 edge(s))
- `len` (29 edge(s))
- `dump` (24 edge(s))
- `sum` (22 edge(s))
- `predict_proba` (19 edge(s))
- `time` (14 edge(s))
- `open` (12 edge(s))
- `mean` (11 edge(s))
- `max` (11 edge(s))
- `sorted` (11 edge(s))
- `fit` (10 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/ml/training/study_model_selection.py` (7 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/training/run_calibration.py` (4 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/training/run_tournament.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/training/train_flood_model.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/training/run_threshold_optimization.py` (2 edge(s))
