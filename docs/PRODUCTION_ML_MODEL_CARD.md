# Production Machine Learning Model Card: FlowShield V2.5

**Problem Statement:** SIH 2026 (Problem Statement ID: 26192)  
**Target Domain:** Mandi District, Himachal Pradesh (Beas River Basin Corridor)  
**Primary Function:** Operational Flash Flood & Cloudburst Early Warning Decision Support  
**Model Identifier:** `flowshield-flood-risk-v2`  
**Standard Compliance:** Mitchell et al. (2019) *Model Cards for Model Reporting*  
**Operational Status:** `CERTIFIED_PRODUCTION_READY` (Passed Phase 21 Independent Locked Evaluation)  

---

## 1. Model Details

### 1.1 Overview
FlowShield V2.5 is an end-to-end, scientifically validated, calibrated machine learning classification pipeline engineered specifically to predict flash flood onset across 22 vulnerable riverside and hillslope settlements in the Mandi District of Himachal Pradesh.

- **Developer:** FlowShield Core ML Engineering Team
- **Version:** `2.5.0` (Tagged `v2.5-production-promoted`)
- **Promotion Date:** September 2026
- **Architecture Pipeline:**
  1. `SimpleImputer(strategy='median')`: Non-leaking statistical imputation of missing telemetry
  2. `StandardScaler()`: Centering and unit-variance standardization based strictly on training empirical statistics
  3. `LogisticRegression(C=0.1, class_weight='balanced', solver='liblinear', random_state=26192)`: Convex, linearly explainable log-odds discriminative classifier
  4. `CalibratedClassifierCV(method='isotonic')`: Non-parametric isotonic probability calibration fitted on isolated calibration split `val_cal`
- **Operational Decision Threshold:** $\tau = 0.080$ (Optimized under extreme class imbalance to maximize recall while maintaining high specificity)

---

## 2. Input Features & Topographic Foundations

The model operates strictly on **15 canonical features** derived exclusively from genuine Copernicus ECMWF ERA5-Land hourly reanalysis and SRTM 30m Digital Elevation Models (DEM). Zero synthetic features. Zero forward-looking leakage.

| # | Feature Name | Unit | Physical Type | Description & Hydrological Purpose |
|---|---|---|---|---|
| 1 | `rainfall_1h_mm` | mm | Dynamic | Short-term cloudburst trigger intensity (hourly rate) |
| 2 | `rainfall_3h_mm` | mm | Dynamic | Sub-catchment accumulation (rolling 3h precipitation) |
| 3 | `rainfall_6h_mm` | mm | Dynamic | Intermediate hillslope saturation loading |
| 4 | `rainfall_24h_mm` | mm | Dynamic | Macro antecedent precipitation index (24h cumulative) |
| 5 | `rainfall_72h_mm` | mm | Dynamic | Deep saturation loading and valley baseflow accumulation |
| 6 | `soil_saturation_pct` | % | Dynamic | Topsoil root zone (0–7cm) saturation ratio (% of field capacity) |
| 7 | `deep_soil_saturation_pct` | % | Dynamic | Deep subsoil zone (7–28cm) moisture saturation |
| 8 | `temperature_c` | °C | Dynamic | 2m surface ambient air temperature |
| 9 | `relative_humidity_pct` | % | Dynamic | Near-surface atmospheric humidity |
| 10 | `surface_pressure_hpa` | hPa | Dynamic | Barometric pressure adjusted for station altitude |
| 11 | `wind_speed_kmh` | km/h | Dynamic | 10m surface horizontal wind vector magnitude |
| 12 | `elevation_m` | m | Topographic | Settlement altitude above mean sea level |
| 13 | `catchment_slope_deg` | ° | Topographic | Mean catchment hillslope incline angle |
| 14 | `dist_to_river_m` | m | Topographic | Perpendicular distance to active river bed |
| 15 | `upstream_drainage_sqkm` | km² | Topographic | Upstream contributing hydrological catchment drainage area |

---

## 3. Dataset Provenance & Data Splits

### 3.1 Source Data
- **Meteorological & Hydrological Telemetry:** Copernicus Climate Change Service (C3S) ECMWF ERA5-Land Reanalysis (2018–2024 hourly resolution).
- **Disaster Events Inventory:** Validated chronological flood events derived from official Himachal Pradesh State Disaster Management Authority (HPSDMA) records, including the catastrophic July–August 2023 Beas River basin mega-disaster.
- **Topography:** NASA Shuttle Radar Topography Mission (SRTM) 30m DEM.

### 3.2 Strict Chronological Non-Overlapping Splits
To prevent temporal and spatial leakage, data was split strictly along chronological event boundaries:

1. **Training Split (`train_split.csv`):** 8,160 samples (Historical baseline 2018–2022).
2. **Calibration Split (`val_cal_split.csv`):** 980 samples (Dedicated strictly to isotonic calibrator parameter estimation).
3. **Hyperparameter & Threshold Split (`val_tune_split.csv`):** 2,284 samples (Used for tournament selection and threshold locking).
4. **Final Locked Test Split (`final_test_locked.csv`):** 4,200 samples (Covering July–August 2023 Beas deluge; accessed **exactly once** during Phase 21 production readiness audit).

---

## 4. Quantitative Performance on Locked Final Test Set

Evaluated at locked operational threshold $\tau = 0.080$:

| Evaluation Metric | Measured Score | Gate Criterion | Verification Result |
|---|---|---|---|
| **Recall (Sensitivity)** | **87.62%** | $\ge 85.0\%$ | **PASS** |
| **Specificity** | **88.10%** | $\ge 80.0\%$ | **PASS** |
| **Precision** | **56.50%** | Baseline $> 20\%$ | **PASS** |
| **F1-Score** | **0.6870** | Baseline $> 0.50$ | **PASS** |
| **F2-Score (Safety-Weighted)** | **0.7892** | Baseline $> 0.65$ | **PASS** |
| **ROC-AUC Score** | **0.9224** | $\ge 0.880$ | **PASS** |
| **PR-AUC Score** | **0.6725** | Baseline $> 0.50$ | **PASS** |
| **Brier Score** | **0.0712** | Climatology: $0.1275$ | **PASS** (44.2% BSS improvement) |
| **Expected Calibration Error (ECE)** | **0.0217** | $\le 0.050$ | **PASS** (Superb probabilistic alignment) |

### 4.1 Confusion Matrix ($\tau = 0.080$)
```
                     Predicted Negative (P < 0.08)    Predicted Positive (P >= 0.08)
Actual Non-Flood:              3,145 (TN)                         425 (FP)
Actual Flash Flood:               78 (FN)                         552 (TP)
```

---

## 5. Model Explainability & Interpretability

### 5.1 Mathematical Log-Odds Decomposition
Unlike black-box models with heuristic post-hoc approximations, FlowShield V2.5 provides **exact, closed-form marginal attributions** via linear log-odds decomposition:

$$\phi_i(x) = \beta_i \cdot \left(\frac{x_i - \mu_i}{\sigma_i}\right)$$

Where:
- $\beta_i$ is the trained Logistic Regression coefficient for feature $i$.
- $\mu_i, \sigma_i$ are the empirical mean and standard deviation from the preprocessor pipeline.
- $\phi_i(x)$ is the exact marginal contribution in logit space.

---

## 6. Model Governance & Cryptographic Integrity

### 6.1 Checksum Verification
Every production artifact is protected by SHA-256 integrity verification enforced by `ModelIntegrityChecker` at startup:

- `v2_selected_model.joblib`: `d45af8d35697ad8d749ede5be7b03c33fd6548bbe29748eb7c48c2c9f0d774bb`
- `v2_calibrator.joblib`: `c368eacb50f972a53eac2db088d4fc37b51e223d9f404b212546863e03d4f780`
- `v2_preprocessor.joblib`: `8e5c8c9570ac3ddc5e5f952da11b9309dc6563ee880b670891efa22c4d19f27c`
- `v2_decision_pipeline.json`: `cddbc38cc0de334d3f51095ccce8e35feeb7a62cefb9974536447bde24cc6ea9`

### 6.2 Disaster Recovery MTTR
In the Phase 23 chaos drill, automated tampering detection occurred in **2.08 ms**, and full baseline rollback was verified in **0.02 seconds** (well within the 60-second operational SLA).

---

## 7. Ethical Considerations & Caveats

1. **Decision Support, Not Executive Authority:** FlowShield provides advisory risk scores to disaster response teams (NDRF/SDRF) and local administrators. It is not an autonomous authority for evacuation orders.
2. **Missing Sensor Degradation:** If upstream weather stations experience hardware blackout, the pipeline median-imputer substitutes regional climatology, and `prediction_quality` degrades gracefully while raising a telemetry alert.
3. **Microclimate Caveats:** Extreme localized cloudbursts occurring in unmonitored sub-valleys narrower than ERA5 grid cells (~9km) require automated radar integration for sub-hourly localized warnings.
