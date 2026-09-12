# TerraPulse V3 — Uttarakhand V2 Threshold Analysis

## Dataset

- Test predictions: `07_Models\ensemble_v2_test_predictions.csv`
- Test rows: `4,745`
- Actual flood cases: `55`
- Actual non-flood cases: `4,690`
- PR-AUC: `0.0385`

## Current V2 Threshold

- Threshold: `0.38`
- Precision: `0.0343`
- Recall: `0.2909`
- F1: `0.0613`
- FPR: `0.0962`

## Best F1 Threshold

- Threshold: `0.49`
- Precision: `0.0714`
- Recall: `0.0909`
- F1: `0.0800`
- FPR: `0.0139`

## Best Recall Threshold

- Threshold: `0.11`
- Precision: `0.0282`
- Recall: `0.8364`
- F1: `0.0545`
- FPR: `0.3384`

## Best Precision Threshold

- Threshold: `0.53`
- Precision: `0.1429`
- Recall: `0.0364`
- F1: `0.0580`
- FPR: `0.0026`

## Practical Early-Warning Candidate

- Status: `NO_PRACTICAL_THRESHOLD_FOUND`
- No practical threshold met both minimum precision and recall criteria.

## Important Interpretation

Threshold optimization cannot create predictive signal that is absent from the model.
Because the V2 river and weather variables are synthetic prototype inputs, these results are suitable for software demonstration only.

## Complete Threshold Sweep

See `ensemble_v2_threshold_evaluation.csv` for all thresholds from 0.01 to 0.99.
