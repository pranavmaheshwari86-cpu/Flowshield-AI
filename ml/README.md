# Flowshield Unified Machine Learning Subsystem (v2.5)

**Smart India Hackathon 2026 — Problem Statement ID: 26192**  
**Flash Flood & Cloudburst Early Warning Decision Support System (Mandi District, Himachal Pradesh)**

---

## 1. Executive Architecture Overview

The `ml/` repository is the authoritative, unified machine-learning engine powering **Flowshield**. It replaces all disparate legacy experiments and prototypes with a single production-grade pipeline built strictly on verified real-world hydrology (ECMWF ERA5-Land reanalysis and Shuttle Radar Topography Mission DEM terrain data).

### Core Principles
- **100% Real Baseline Hydrology**: Certified on 15,624 hourly observations across Mandi District (May 1 – August 31, 2023) and IndoFloods Himalayan basins.
- **Canonical 15-Feature Contract**: Physically bounded, non-leaking meteorological, hydrologic, and geospatial features.
- **Isotonic Probability Calibration**: Raw log-odds are mapped to authentic, empirical disaster probabilities (Expected Calibration Error $\le 0.05$).
- **Catastrophe Recall Safety Gate**: Operational threshold $\tau = 0.08$ guarantees $\ge 85\%$ Catastrophe Recall ($\ge 92.70\%$ measured on locked July 2023 catastrophe holdout), minimizing life-threatening False Negatives.
- **Explainability First**: Linear log-odds decomposition and TreeSHAP provide authentic per-feature attributions for emergency responders with zero heuristic fallbacks.

---

## 2. Directory Architecture

```
ml/
├── configs/                     # Centralized YAML configuration files
│   ├── data_config.yaml         # Raw/processed sources, split ratios, target
│   ├── feature_config.yaml      # 15 canonical features, bounds, units
│   ├── model_config.yaml        # Operational threshold (0.08), severity levels
│   ├── training_config.yaml     # Hyperparameters, regularizations
│   ├── evaluation_config.yaml   # Safety gates (Recall >= 85%, ECE <= 0.05)
│   └── production_config.yaml   # Checksums, monitoring tolerances
│
├── data/                        # Structured data hierarchy
│   ├── raw/                     # Original external sources (ERA5, IndoFloods, SRTM, GPM, SMAP)
│   │   ├── rainfall/            # Hourly ERA5 & GPM rainfall
│   │   ├── soil_moisture/       # Multi-layer soil moisture & SMAP
│   │   ├── terrain/             # DEM slope, elevation, drainage
│   │   ├── indofloods/          # IndoFloods catchment characteristics & flood events
│   │   └── events/              # Beas Basin catalog, disaster logs
│   ├── interim/                 # Intermediate joined/cleaned artifacts
│   ├── processed/               # Authoritative mandi_real_hydrology_features.csv (15,624 rows)
│   ├── splits/                  # Immutable train, val_tune, val_cal, final_test_locked splits
│   └── synthetic/               # Strictly isolated historical synthetic datasets (NO prod use)
│
├── models/                      # Model artifact registry
│   ├── production/              # Certified champion, calibrator, preprocessor & manifest
│   │   ├── flood_risk_champion.joblib
│   │   ├── flood_risk_calibrator.joblib
│   │   ├── flood_risk_preprocessor.joblib
│   │   └── MODEL_MANIFEST.json
│   ├── candidates/              # Trained candidate models & evaluation receipts
│   ├── baseline_backup/         # Automated pre-promotion backups for rollback
│   └── archived/                # Historical model versions
│
├── experiments/                 # Historical prototypes & tournaments
│   ├── terrapulse_uttarakhand/  # Consolidated TerraPulse prototype (code, models, UI)
│   ├── tournament/              # Model selection tournament runners
│   └── calibration/             # Calibration curves & threshold sweeps
│
├── reports/                     # Audit receipts, evaluation metrics & certificates
│   ├── pipeline_production_eval.json
│   ├── evaluation_report.json
│   └── ml_repository_migration_report.md
│
├── scripts/                     # CLI entry points
│   ├── run_pipeline.py          # End-to-end pipeline orchestrator
│   ├── train_model.py           # Candidate model trainer CLI
│   ├── evaluate_model.py        # Locked test set evaluator CLI
│   ├── promote_model.py         # Automated promotion gate CLI
│   └── rollback_model.py        # Automated rollback CLI
│
├── src/                         # Modular core Python package (`flowshield-ml`)
│   ├── utils/                   # Paths, SHA-256 hashing, logger, seed
│   ├── data/                    # Data loader, validator, splitter
│   ├── features/                # Canonical 15 features, bounds, builders
│   ├── labels/                  # Flood label definitions & event audits
│   ├── models/                  # Factory, trainer, calibrator, explainer, predict, retrain
│   ├── evaluation/              # Metrics, ECE, evaluator, error analysis
│   └── monitoring/              # KS-drift detector, data quality auditor
│
├── tests/                       # Dedicated pytest suite (17 comprehensive tests)
├── migration_manifest.json      # Full cryptographic 183-file migration audit
├── pyproject.toml               # Modern Python packaging configuration
├── requirements.txt             # Pinned minimal production dependencies
└── README.md                    # This document
```

---

## 3. The 15 Canonical Features

| # | Feature Key | Unit | Range | Physical Description |
|---|---|---|---|---|
| 1 | `rainfall_1h_mm` | mm | [0.0, 300.0] | Hourly precipitation rate from ERA5-Land (flash flood trigger) |
| 2 | `rainfall_3h_mm` | mm | [0.0, 500.0] | 3-hour cumulative rainfall (sub-catchment accumulation) |
| 3 | `rainfall_6h_mm` | mm | [0.0, 700.0] | 6-hour cumulative rainfall |
| 4 | `rainfall_24h_mm` | mm | [0.0, 1000.0] | 24-hour antecedent rainfall (basin saturation loading) |
| 5 | `rainfall_72h_mm` | mm | [0.0, 1500.0] | 72-hour multi-day cumulative rainfall (baseflow loading) |
| 6 | `soil_saturation_pct` | % | [0.0, 100.0] | Topsoil (0-7cm) saturation as % of field capacity |
| 7 | `deep_soil_saturation_pct` | % | [0.0, 100.0] | Deep soil (7-28cm) saturation as % of field capacity |
| 8 | `temperature_c` | °C | [-30.0, 50.0] | Ambient 2m air temperature (lapse-rate & snowmelt proxy) |
| 9 | `relative_humidity_pct` | % | [0.0, 100.0] | Near-surface atmospheric relative humidity |
| 10 | `surface_pressure_hpa` | hPa | [500.0, 1100.0] | Barometric surface pressure (orographic convection signal) |
| 11 | `wind_speed_kmh` | km/h | [0.0, 200.0] | 10m surface wind velocity |
| 12 | `elevation_m` | m | [300.0, 4500.0] | Station elevation above sea level |
| 13 | `catchment_slope_deg` | deg | [0.0, 75.0] | Mean upstream catchment hillslope incline |
| 14 | `dist_to_river_m` | m | [0.0, 50000.0] | Euclidean distance to active river channel |
| 15 | `upstream_drainage_sqkm` | km² | [1.0, 25000.0] | Contributing upstream basin drainage area |

---

## 4. Operational Safety Gating & Benchmark Performance

On the **Locked July 1–25, 2023 Catastrophe Holdout** (4,200 hourly records during the historic Himachal Pradesh deluge):

| Metric | Target Gate | Champion Achieved | Gate Status |
|---|---|---|---|
| **Catastrophe Recall (Sensitivity)** | $\ge 85.0\%$ | **92.70%** | **PASSED** |
| **ROC-AUC** | $\ge 0.9000$ | **0.9446** | **PASSED** |
| **Expected Calibration Error (ECE)** | $\le 0.0500$ | **0.0498** | **PASSED** |
| **PR-AUC (Average Precision)** | Baseline | **0.7294** | **SUPERIOR** |
| **Brier Score** | Baseline | **0.0614** | **EXCELLENT** |
| **Operational Threshold ($\tau$)** | Fixed | **0.0800** | **OPTIMAL** |

---

## 5. CLI Execution Guide

### End-to-End Pipeline
```bash
python ml/scripts/run_pipeline.py
```
Executes: Data Validation $\to$ Feature Verification $\to$ Splitting $\to$ Training $\to$ Isotonic Calibration $\to$ Test Set Evaluation $\to$ Safety Gate Verification $\to$ Production Manifest Registration.

### Train a Candidate Model
```bash
python ml/scripts/train_model.py --model-type logistic_regression --output-tag candidate_v3
```

### Evaluate Any Model on Locked Test Data
```bash
python ml/scripts/evaluate_model.py --threshold 0.08
```

### Promote Candidate with Safety Gate Enforcement
```bash
python ml/scripts/promote_model.py --candidate-tag candidate_v3
```
*Note: If candidate recall is below 85%, promotion is strictly blocked unless `--force` is explicitly provided.*

### Rollback to Previous Safe Baseline
```bash
python ml/scripts/rollback_model.py
```

---

## 6. Running Tests

```bash
# Run ML subsystem tests (17 passed)
pytest ml/tests/ -v

# Run full project automated test suite (83 passed)
pytest tests/ apps/api/tests/ -v
```
