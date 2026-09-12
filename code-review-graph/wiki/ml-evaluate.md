# ml-evaluate

## Overview

Directory-based community: ml

- **Size**: 5 nodes
- **Cohesion**: 0.0162
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| evaluate_model | Function | C:/Users/Pranav/Desktop/Flowshield/ml/evaluate.py | 14-54 |
| generate_synthetic_dataset | Function | C:/Users/Pranav/Desktop/Flowshield/ml/generate_data.py | 18-141 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/ml/generate_data.py | 144-156 |
| compute_file_hash | Function | C:/Users/Pranav/Desktop/Flowshield/ml/train.py | 36-42 |
| train_pipeline | Function | C:/Users/Pranav/Desktop/Flowshield/ml/train.py | 45-191 |

## Execution Flows

- **train_pipeline** (criticality: 0.52, depth: 1)

## Dependencies

### Outgoing

- `print` (30 edge(s))
- `round` (19 edge(s))
- `clip` (16 edge(s))
- `join` (10 edge(s))
- `uniform` (8 edge(s))
- `float` (8 edge(s))
- `len` (7 edge(s))
- `dirname` (4 edge(s))
- `mean` (4 edge(s))
- `normal` (4 edge(s))
- `open` (3 edge(s))
- `makedirs` (3 edge(s))
- `sum` (3 edge(s))
- `exists` (2 edge(s))
- `load` (2 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/ml/generate_data.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/train.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/ml/evaluate.py` (2 edge(s))
