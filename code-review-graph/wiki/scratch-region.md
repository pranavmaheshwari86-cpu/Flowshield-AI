# scratch-region

## Overview

Directory-based community: scratch

- **Size**: 19 nodes
- **Cohesion**: 0.0588
- **Dominant Language**: python

## Members

| Name | Kind | File | Lines |
|------|------|------|-------|
| acquire_region | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/acquire_real_regional_data.py | 53-117 |
| acquire_region | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/acquire_tier2_regional_data.py | 36-84 |
| get_hash | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/audit_ml_consolidation.py | 8-16 |
| run_cmd | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/check_git_tracking.py | 6-8 |
| run_cmd | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/deep_audit_part2.py | 6-8 |
| safe_remove_file | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/execute_step2_cleanup.py | 6-13 |
| safe_remove_dir | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/execute_step2_cleanup.py | 15-23 |
| search_ast | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/find_ast_rainfall.py | 7-29 |
| compute_ece | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/hardcore_audit_engine.py | 45-59 |
| evaluate_predictions | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/hardcore_audit_engine.py | 62-96 |
| audit_baselines | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/hardcore_audit_engine.py | 99-148 |
| compute_ece | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/run_full_adversarial_audit.py | 45-58 |
| eval_metrics | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/run_full_adversarial_audit.py | 61-95 |
| predict_bundle_batch | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/run_full_adversarial_audit.py | 98-120 |
| main | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/run_full_adversarial_audit.py | 123-740 |
| evaluate_predictions | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/run_multi_region_scientific_suite.py | 44-69 |
| process_region | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/run_multi_region_scientific_suite.py | 71-183 |
| evaluate_preds | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/run_ultimate_scientific_rebuild.py | 138-165 |
| audit_buxar_telemetry | Function | C:/Users/Pranav/Desktop/Flowshield/scratch/verify_buxar_telemetry.py | 31-190 |

## Execution Flows

- **main** (criticality: 0.69, depth: 4)
- **audit_buxar_telemetry** (criticality: 0.63, depth: 4)
- **acquire_region** (criticality: 0.54, depth: 3)
- **acquire_region** (criticality: 0.54, depth: 3)
- **audit_baselines** (criticality: 0.37, depth: 2)
- **process_region** (criticality: 0.36, depth: 1)

## Dependencies

### Outgoing

- `round` (82 edge(s))
- `float` (70 edge(s))
- `print` (65 edge(s))
- `len` (45 edge(s))
- `int` (28 edge(s))
- `mean` (21 edge(s))
- `append` (17 edge(s))
- `predict_proba` (17 edge(s))
- `sum` (16 edge(s))
- `info` (12 edge(s))
- `astype` (12 edge(s))
- `fit` (12 edge(s))
- `copy` (12 edge(s))
- `lower` (10 edge(s))
- `unique` (10 edge(s))

### Incoming

- `C:/Users/Pranav/Desktop/Flowshield/scratch/run_ultimate_scientific_rebuild.py` (11 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/execute_step2_cleanup.py` (7 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/run_full_adversarial_audit.py` (5 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/audit_ml_consolidation.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/deep_audit_part2.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/hardcore_audit_engine.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/run_multi_region_scientific_suite.py` (3 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/acquire_real_regional_data.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/acquire_tier2_regional_data.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/check_git_tracking.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/find_ast_rainfall.py` (2 edge(s))
- `C:/Users/Pranav/Desktop/Flowshield/scratch/verify_buxar_telemetry.py` (2 edge(s))
