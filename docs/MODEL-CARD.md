# Model Card — Flowshield Flood Risk Model (v2.0-calibrated)

## 1. Model Details
- **Model Name**: Flowshield Real-Data Flood Risk Classifier & Decision Support Engine (V2)
- **Model Identifier**: `flowshield-flood-risk-v2`
- **Selected Architecture**: L2-Regularized Logistic Regression with Isotonic Probability Calibration
- **Benchmarked Candidates**: Logistic Regression, Random Forest (100 trees), XGBoost Classifier
- **Calibration Method**: Non-parametric Isotonic Regression (fitted on spatial holdout: Pandoh Dam & Dharampur)
- **Operational Decision Threshold**: $\tau = 0.08$ (codified to minimize False Negative Rate; Recall $\ge 85\%$)
- **Input Dimension**: 15 canonical physical hydrometeorological & topographic features
- **Output**: Calibrated flood occurrence probability $P \in [0, 1]$, multi-factor operational risk index $R \in [0, 100]$, 5-tier operational risk classification (`LOW`, `WATCH`, `HIGH`, `CRITICAL`, `INSUFFICIENT_DATA`), and deterministic physical feature attributions
- **Release Date**: September 2026
- **Developer**: Flowshield AI / Engineering Team (Smart India Hackathon 2026, PS ID: 26192)

---

## 2. Intended Use & Boundaries
### 2.1 Intended Use
- **Emergency Operations Decision Support**: Assisting District Disaster Management Authorities (DDMA Mandi / HPSDMA) in prioritizing vulnerable settlements during heavy monsoon episodes.
- **Antecedent Risk Screening**: Evaluating cumulative 3h, 6h, 24h, and 72h rainfall loading coupled with soil saturation to assess terrain vulnerability before active cloudburst inundation.
- **Resource Staging**: Providing 6–24 hour advance advisory to preposition NDRF/SDRF teams and prepare community relief shelters.

### 2.2 NOT Intended Use (Explicit Negative Scope)
- **NOT an Autonomous Automated Evacuation Trigger**: AI outputs must never bypass human Emergency Operations Center (EOC) verification.
- **NOT a 15-Minute River Stage Sensor Replacement**: The model is trained on hourly atmospheric reanalysis ($9\text{km}$ grid). It cannot predict sub-hourly ultrasonic water level variations in the absence of local CWC telemetry.
- **NOT an Automated Dam Spillway Gate Controller**: Spillway operations must follow established dam safety protocols and manual hydraulic guidelines.
- **NOT an Individual Citizen Triage Dispatcher**: Public open datasets do not contain incident-level call transcripts; citizen routing relies on deterministic safety SOPs.

---

## 3. Training & Validation Datasets

| Parameter | Specification |
|---|---|
| **Primary Dataset** | ECMWF Copernicus ERA5-Land Hourly Reanalysis via Open-Meteo API |
| **Topographic Source** | NASA SRTM 30m Digital Elevation Model & ISRO Bhuvan |
| **Disaster Ground Truth** | Himachal Pradesh State Disaster Management Authority (HPSDMA) Disaster Reports (July & August 2023) |
| **Benchmark Catalog** | INDOFLOODS (Zenodo DOI: `10.5281/zenodo.14584654`, BAMS 2025) & HiFlo-DAT (DOI: `10.1007/s11069-021-04698-6`) |
| **Total Verified Records** | 15,624 genuine hourly observations across 7 Mandi monitoring stations (Zero fabricated samples) |
| **Class Distribution** | 14,525 negative hours (92.97%) / 1,099 disaster flood hours (7.03%) |
| **Training Split** | 8,160 samples (5 stations: Mandi Urban, Aut, Thalot, Joginder Nagar, Sadar) |
| **Validation Split (Spatial Holdout)** | 3,264 samples (2 holdout stations: Pandoh Dam, Dharampur Khad) |
| **Holdout Test Split (Temporal Holdout)** | 4,200 samples (July 1–25, 2023 historic catastrophe — strictly untouched until final evaluation) |

---

## 4. Input Features (15 Canonical Attributes)

1. `rainfall_1h_mm`: Immediate 1-hour rainfall intensity ($mm$).
2. `rainfall_3h_mm`: Cumulative 3-hour precipitation ($mm$).
3. `rainfall_6h_mm`: Cumulative 6-hour precipitation ($mm$).
4. `rainfall_24h_mm`: Daily antecedent precipitation index ($mm$).
5. `rainfall_72h_mm`: Multi-day antecedent soil loading ($mm$).
6. `soil_saturation_pct`: Topsoil volumetric moisture relative to field capacity ($0-100\%$).
7. `deep_soil_saturation_pct`: Root zone soil moisture ($0-100\%$).
8. `temperature_c`: 2m ambient air temperature ($^\circ\text{C}$).
9. `relative_humidity_pct`: Atmospheric humidity ($0-100\%$).
10. `surface_pressure_hpa`: Barometric surface pressure ($hPa$).
11. `wind_speed_kmh`: 10m horizontal wind velocity ($km/h$).
12. `elevation_m`: Settlement altitude above MSL ($m$).
13. `catchment_slope_deg`: Mean topographic hillslope inclination ($^\circ$).
14. `dist_to_river_m`: Euclidean distance to nearest primary river reach ($m$).
15. `upstream_drainage_sqkm`: Catchment drainage area contributing runoff ($km^2$).

---

## 5. Performance Benchmarks on Unseen July 2023 Catastrophe Holdout

Evaluated strictly once on the 4,200 untouched hourly observations (630 flood-positive hours) from July 1–25, 2023:

| Metric | Selected Frozen Model (`logistic_regression + isotonic`) | Prior Baseline (`xgboost` raw at 0.50) | Operational Safety Requirement |
|---|---|---|---|
| **Disaster Recall (Sensitivity)** | **88.41%** (557 of 630 hours detected) | 29.68% (187 of 630 detected) | $\ge 85.0\%$ (PASS) |
| **False Negative Rate (Missed Floods)** | **11.59%** (73 hours missed) | 70.32% (443 hours missed) | $\le 15.0\%$ (PASS) |
| **False Positive Rate (False Alarms)** | **13.50%** (482 hours) | 1.62% (58 hours) | $\le 15.0\%$ (PASS) |
| **Precision** | **53.61%** | 76.33% | Balance safety vs fatigue |
| **F1-Score** | **0.6675** | 0.4274 | Maximized harmonic mean |
| **ROC-AUC** | **0.9230** | 0.9304 | High discrimination |
| **PR-AUC** | **0.6761** | 0.6719 | Imbalance robustness |
| **Brier Score** | **0.0711** | 0.0820 | Low quadratic probability loss |
| **Inference Latency (P50)** | **0.088 ms** | 0.505 ms | Ultra-low edge execution |
| **Model Artifact Size** | **0.97 KB** | 150.6 KB | Embedded microcontroller ready |

---

## 6. Safety Guardrails & Operational Risk Levels

Flowshield V2 integrates 5 discrete operational safety states:
1. **`INSUFFICIENT_DATA`**: Triggered immediately when sensor feeds exhibit physically impossible values (e.g. negative rainfall, soil saturation $> 100\%$, corrupted telemetry). Prevents blind decisions.
2. **`LOW`** ($R < 25$, $P < 0.04$): Normal baseline seasonal monitoring.
3. **`WATCH`** ($25 \le R < 50$ or $0.04 \le P < 0.08$): Catchment priming detected; response teams put on alert.
4. **`HIGH`** ($50 \le R < 75$ or $P \ge 0.08$): Operational threshold breached; early public alerts dispatched.
5. **`CRITICAL`** ($R \ge 75$ or $P \ge 0.50$): Imminent flood surge; mandatory evacuation staging.

---

## 7. Known Biases & Technical Limitations

1. **Spatial Grid Averaging**: ERA5-Land provides reanalysis over a $\sim 9\text{km}$ grid. Ultra-localized micro-cloudburst cells ($< 2\text{km}$ across) can occur between grid centroids without registering extreme hourly rainfall totals.
2. **Absence of Real-Time River Gauge Feeds**: Because Central Water Commission (CWC) river stage telemetry is classified as "Restricted" in the Beas basin, the model relies on meteorological forcing and topography. When user-provided CWC gauge feeds are connected, streamflow routing accuracy will significantly increase.
3. **Geographic Specificity**: Trained on the steep valleys and high-relief topography of Mandi District (Western Himalayas). Transferring the model directly to flat peninsular floodplains without retraining will produce skewed topographic attributions.
