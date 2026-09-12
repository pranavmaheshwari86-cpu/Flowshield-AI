# FlowShield V2.5 — Scientific Validity Sign-Off Report

> **Date**: 2026-09-12  
> **Status**: APPROVED  
> **Sign-Off Authority**: Principal ML Architect & Senior Production Reliability Engineer  

---

### 1. Final Held-Out Test Set Lock Verification
- **Test Set File**: `ml/data/splits/final_test_locked.csv`
- **Expected SHA-256**: `25d58fd2c668357dbd964ca7fb82e12086c2b23c97ddcf386f237e4322bfc8f3`
- **Current SHA-256**: `25d58fd2c668357dbd964ca7fb82e12086c2b23c97ddcf386f237e4322bfc8f3`
- **Integrity Status**: VERIFIED LOCKED & UNTOUCHED
- **Access Rule**: The final test set has NOT been queried during model selection, hyperparameter tuning, calibration fitting, or threshold selection.

---

### 2. Model Selection Tournament Audit
- **Winning Model Family**: `LogisticRegression`
- **Composite Score**: `0.6578`
- **Spatial Generalization Validation**:
  - Validation Split: `val_tune_split.csv` (2 Spatial Holdout Stations: `PND_DAM_02`, `DHR_KHD_06`)
  - ROC-AUC on Spatial Holdout: `0.9318`
  - PR-AUC on Spatial Holdout: `0.4598`
  - Generalization Gap: `0.0471` (Tree models exhibited gap > 0.13)
  - Inference Latency p99: `0.01 ms`

---

### 3. Calibration Architecture Audit
- **Fitting Split**: `val_cal_split.csv` (30% of development spatial holdout, 40 flood events)
- **Evaluation Split**: `val_tune_split.csv` (70% of development spatial holdout, 94 flood events)
- **Selected Calibrator**: `isotonic`
- **Evaluated Brier Score**: `0.0287` (Bar: <= 0.050)
- **Evaluated ECE**: `0.004` (Bar: <= 0.040)
- **Monotonicity**: `True` (zero non-monotonic steps across decision range)

---

### 4. Operational Decision Policy Audit
- **Operational Alert Threshold**: tau = 0.080
- **Combined Spatial Validation Recall**: `0.8657` (Bar: >= 0.850)
- **Combined Spatial Validation FPR**: `0.1684`
- **Disaster Response Tiering**:
  - LOW: P_cal < 0.04
  - WATCH: 0.04 <= P_cal < 0.08
  - HIGH: 0.08 <= P_cal < 0.50
  - CRITICAL: P_cal >= 0.50

---

### 5. Scientific Validity Checklist
- [x] Zero synthetic samples in training or validation pipeline.
- [x] Zero temporal or spatial overlap between train and validation splits.
- [x] Probability calibration fitted on held-out split, eliminating optimistic leakage.
- [x] Model promoted strictly by empirical composite score.
- [x] Final held-out test set verified locked.

**GATE 3 (DECISION VALID) STATUS**: PASSED
