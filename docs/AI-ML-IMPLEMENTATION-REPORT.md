# Flowshield — AI / ML Implementation & Scientific Evaluation Report

**Document ID**: FLOWSHIELD-AI-REPORT-2026-V2  
**Project**: Flowshield (Smart India Hackathon 2026, PS ID: 26192)  
**Author**: Flowshield AI / Hydrological Engineering Team  
**Date**: September 2026  
**Pipeline Identifier**: `flowshield-flood-risk-v2`  
**Status**: V2 Calibrated Pipeline Implemented, Scientifically Selected, and Verified  

---

## 1. Dataset & Provenance

Flowshield strictly uses real, verifiable public datasets (**zero synthetic or fabricated data**):

| Metric / Parameter | Value / Detail |
|---|---|
| **Atmospheric Dataset** | ECMWF Copernicus ERA5-Land Hourly Atmospheric Reanalysis via Open-Meteo Archive API |
| **Topographic Dataset** | NASA SRTM 30m Digital Elevation Model & ISRO Bhuvan Spatial Grids |
| **National Benchmark Archive**| INDOFLOODS (Zenodo DOI: `10.5281/zenodo.14584654`, BAMS 2025) — 4,548 historical flood events across 155 Indian basins |
| **Historical Disaster Catalog**| HiFlo-DAT (DOI: `10.1007/s11069-021-04698-6`) & HPSDMA Disaster Assessment Bulletins (1995–2023) |
| **Total Genuine Records** | **15,624 hourly observations** across 7 hydrological nodes in Mandi District |
| **Class Distribution** | 14,525 non-flood hours (92.97%) vs. 1,099 documented disaster flood hours (7.03%) |
| **Class Imbalance** | ~13.2 : 1 |
| **Geographic Nodes** | Mandi Urban (760m), Pandoh Dam (890m), Aut (1,050m), Thalout (980m), Jogindernagar (1,220m), Dharampur (900m), Sundernagar (860m) |

---

## 2. Leakage-Free 3-Way Dataset Partitioning Protocol

To satisfy rigorous scientific standards, the 15,624 records are partitioned into three strictly decoupled sets:

```
Total Real Observations: 15,624 Hourly Rows (7 Mandi Stations)
├── Final Test Set (Untouched Temporal Holdout): 4,200 rows (26.9%)
│   ├── Period: July 1–25, 2023 (Historical Catastrophe Peak)
│   ├── Stations: All 7 Mandi Basin Stations
│   └── Purpose: Single, final, unbiased audit of frozen winner
│
└── Development Set: 11,424 rows (73.1%)
    ├── Period: July 2022 Baseline + July 26–August 31, 2023 (Post-Peak & Cloudburst Wave)
    ├── Spatial Split:
    │   ├── Training Subset (5 Stations): 8,160 rows (71.4% of Dev)
    │   │   └── Stations: Mandi Urban, Aut Junction, Thalot Gorge, Joginder Nagar, Sadar Basin
    │   └── Validation Holdout (2 Stations): 3,264 rows (28.6% of Dev)
    │       └── Stations: Pandoh Dam (PND_DAM_02), Dharampur Khad (DHR_KHD_06)
    └── Purpose: Train models on 5 stations; calibrate and pick threshold on 2 unseen stations
```

### Partitioning Guarantees:
- **Zero Spatial Leakage:** Models are evaluated on validation stations (Pandoh Dam reservoir and Dharampur gorge) that are never observed during training.
- **Zero Temporal Leakage:** The July 1–25, 2023 catastrophe period was frozen and untouched until all models, calibrators, and thresholds were permanently selected.

---

## 3. Candidate Benchmark & Calibration Study

Three classifier families were trained and tested across three calibration regimes (Raw, Platt Sigmoid, and Isotonic Regression) on the unseen spatial validation set:

### Validation Matrix Summary (3,264 rows across Pandoh Dam & Dharampur):

| Model | Calibration Variant | ROC-AUC | PR-AUC | Brier Score | ECE | Op. Recall | Op. FNR | Op. FPR | Op. Threshold |
|---|---|---|---|---|---|---|---|---|---|
| **Logistic Regression** | **Raw** | 0.9250 | 0.4240 | 0.0671 | 0.0899 | 0.8507 | 0.1493 | 0.1636 | 0.19 |
| | **Sigmoid** | 0.9250 | 0.4240 | 0.0305 | 0.0109 | 0.8657 | 0.1343 | 0.1709 | 0.04 |
| | **Isotonic** | **0.9250** | **0.4240** | **0.0287** | **0.0004** | **0.8657** | **0.1343** | **0.1684** | **0.08** |
| **Random Forest** | **Raw** | 0.8757 | 0.1640 | 0.0529 | 0.0429 | 0.8881 | 0.1119 | 0.2236 | 0.06 |
| | **Sigmoid** | 0.8757 | 0.1640 | 0.0375 | 0.0120 | 1.0000 | 0.0000 | 1.0000 | 0.01 |
| | **Isotonic** | 0.8757 | 0.1640 | 0.0339 | 0.0000 | 0.8806 | 0.1194 | 0.2077 | 0.10 |
| **XGBoost** | **Raw** | 0.8548 | 0.1400 | 0.0719 | 0.0724 | 0.7836 | 0.2164 | 0.2406 | 0.01 |
| | **Sigmoid** | 0.8548 | 0.1400 | 0.0379 | 0.0027 | 1.0000 | 0.0000 | 1.0000 | 0.01 |
| | **Isotonic** | 0.8548 | 0.1400 | 0.0357 | 0.0000 | 0.9776 | 0.0224 | 0.3070 | 0.04 |

### Final Model Decision Matrix (Safety-Weighted Composite Scoring):
```
Rank 1: logistic_regression_isotonic (Score: 0.7199) -> SELECTED WINNER
Rank 2: logistic_regression_sigmoid  (Score: 0.7085)
Rank 3: xgboost_isotonic             (Score: 0.6690)
Rank 4: xgboost_sigmoid              (Score: 0.6480)
Rank 5: random_forest_sigmoid        (Score: 0.6112)
Rank 6: logistic_regression_raw      (Score: 0.5506)
Rank 7: random_forest_isotonic       (Score: 0.4605)
Rank 8: random_forest_raw            (Score: 0.4029)
Rank 9: xgboost_raw                  (Score: 0.1406)
```

---

## 4. Final Unbiased Test on Untouched July 2023 Catastrophe Holdout

The frozen pipeline (`logistic_regression + isotonic + threshold=0.08`) was evaluated **strictly once** on the untouched 4,200 catastrophe observations (July 1–25, 2023, 630 flood hours):

```
================================================================================
FINAL EVALUATION METRICS — UNTOUCHED JULY 2023 CATASTROPHE SET
================================================================================
Accuracy:                   86.79%
Precision:                  53.61%
Recall (Sensitivity):       88.41%   (Target: >= 85.0% -> PASSED)
F1-Score:                   66.75%
ROC-AUC:                    0.9230
PR-AUC:                     0.6761
Brier Score:                0.0711
False Negative Rate (FNR):  11.59%   (Missed Floods)
False Positive Rate (FPR):  13.50%   (Target: <= 15.0% -> PASSED)

Confusion Matrix:
  True Negatives:  3,088 hours
  False Positives:   482 hours
  False Negatives:    73 hours (MISSED FLOOD HOURS)
  True Positives:    557 hours (DETECTED FLOOD HOURS)

SUMMARY:
  557 of 630 historical flood-positive hours were successfully detected.
  Only 73 hours were missed across all 7 stations during the 25-day catastrophe.
================================================================================
```

---

## 5. System Integration & API Specification

The V2 calibrated decision pipeline is integrated into the production FastAPI application:
- **Inference Endpoint**: `POST /api/v1/ai/risk` (and legacy path `POST /api/ai/risk`)
- **Metadata Endpoints**:
  - `GET /api/v1/ai/models`: Multi-model benchmark metrics, calibration scores, and winning model parameters.
  - `GET /api/v1/ai/features`: 15 canonical physical features with units and metadata.
- **Operational Risk Tiers**:
  - `INSUFFICIENT_DATA`: Triggered by corrupted/out-of-range sensor inputs.
  - `LOW`: Baseline normal operations.
  - `WATCH`: Early catchment priming.
  - `HIGH`: Operational threshold $\tau = 0.08$ exceeded; public warning sirens.
  - `CRITICAL`: Immediate life-safety emergency inundation threat.

### Sample API Response (V2):
```json
{
  "risk_score": 87.6,
  "risk_level": "CRITICAL",
  "flood_probability": 1.0,
  "confidence": 0.98,
  "threshold": 0.08,
  "calibration_method": "isotonic",
  "model_version": "flowshield-flood-risk-v2",
  "model_type": "Calibrated Logistic Regression (Isotonic scaling on ERA5-Land)",
  "explanation": [
    "Calibrated flood probability (100.0%) exceeds operational threshold (8.0%).",
    "High 3-hour rainfall accumulation (98.0 mm).",
    "Excessive 72-hour antecedent saturation rainfall (320.0 mm).",
    "Elevated topsoil saturation (88.5%).",
    "Immediate river channel proximity (45 m)."
  ],
  "status": "operational_v2_validated",
  "topographic_factor": 0.752,
  "data_provenance": {
    "source": "ECMWF Copernicus ERA5-Land Reanalysis & SRTM 30m DEM",
    "spatial_node": "Mandi Basin Grid Node",
    "is_synthetic": false,
    "calibrated_disasters": ["Beas Mega-Disaster (July 2023)", "Mandi Cloudburst Wave (Aug 2023)"],
    "compliance": "Zero fabricated data. Research prototype baseline."
  }
}
```

---

## 6. Verification Status

All 8 mandatory verification gates have passed:
1. **Dataset validation**: PASSED (15,624 real rows, 15 physical features, zero synthetic data).
2. **Training pipeline artifacts**: PASSED (all models + calibrators saved to `ml/models`).
3. **Evaluation report**: PASSED (`v2_decision_pipeline.json` and `metrics_comparison.json`).
4. **Model loading test**: PASSED (`v2_selected_model.joblib` and `v2_calibrator.joblib` deserialized).
5. **Inference test**: PASSED (`predict_flood_risk` outputs valid risk scores and explanations).
6. **Backend integration module**: PASSED (FastAPI router mounted under `/api/v1` and `/api`).
7. **Existing & AI backend tests**: PASSED (12/12 pytest tests passed).
8. **End-to-end live HTTP request**: PASSED (HTTP 200 returned with V2 calibrated payload).
