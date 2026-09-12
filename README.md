# Flowshield — Predict Early. Act Faster. Save Lives.

[![Smart India Hackathon 2026](https://img.shields.io/badge/SIH-2026-blue.svg)](https://sih.gov.in/)
[![Problem Statement ID: 26192](https://img.shields.io/badge/PS_ID-26192-orange.svg)](#)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL PostGIS](https://img.shields.io/badge/PostgreSQL-PostGIS_16-blue.svg)](https://postgis.net/)
[![Scikit-Learn Calibrated ML](https://img.shields.io/badge/ML-Calibrated_Logistic_Regression-blue.svg)](https://scikit-learn.org/)
[![React 18 TypeScript](https://img.shields.io/badge/React-18_--_TypeScript-blue.svg)](https://react.dev/)
[![Status](https://img.shields.io/badge/Status-Production_Certified-success.svg)](#)

> **Smart India Hackathon 2026 · Problem Statement ID: 26192 · Theme: Disaster Management · Category: Software**  
> **Core Problem: Flash Flood Prediction System for Hilly Regions using Multi-Source Data**  
> **Pilot Region:** Mandi District, Himachal Pradesh (Beas River Basin Corridor)

---

## What is Flowshield?

Flowshield is a production-grade environmental intelligence and operational decision-support platform engineered specifically for flash flood and cloudburst disaster response in Himalayan river valleys. Flowshield integrates genuine Copernicus ECMWF ERA5-Land reanalysis, SRTM 30m Digital Elevation Models, and local river gauge telemetry into an **end-to-end, scientifically validated disaster intelligence pipeline**:

```text
ECMWF ERA5-Land & DEM Telemetry (15 Canonical Features)
        ↓
Strict Bounds & Quality Validation (Physical Telemetry Guardrails)
        ↓
Median Imputation & Standardization Pipeline
        ↓
Calibrated ML Model (ROC-AUC: 0.9224, Sensitivity: 87.62% @ τ=0.080)
        ↓
Authentic Marginal Log-Odds Feature Attributions
        ↓
Operational Risk Engine (ML Hazard Ratio + Vulnerability + Freshness)
        ↓
GIS Interactive Decision Visualizations (Precomputed Voronoi Catchments)
        ↓
Early Warning & Alert Engine (Threshold Exceeded, Automatic Deduplication)
        ↓
Tactical Human-in-the-Loop Action Protocols (NDRF / SDRF Evacuation Dispatch)
        ↓
Dynamic Safe Evacuation Routing & Shelter Intake Management
        ↓
Citizen Warning Mode (Mobile-First, High-Contrast 320px Viewport)
```

---

## Production ML System Performance (Verified on Locked Test Set)

Evaluated on the independent, strictly non-overlapping locked final test set (`final_test_locked.csv`, $N=4,200$ samples, 630 historical flood events):

| Metric | Measured Score | Scientific Operational Significance |
|---|---|---|
| **Recall (Sensitivity)** | **87.62%** | Captures 552 of 630 deluge events at $\tau = 0.080$ |
| **ROC-AUC Score** | **0.9224** | Outstanding discriminative ranking power across all cutoffs |
| **Specificity** | **88.10%** | Minimizes false alarm exhaustion during non-flood periods |
| **Expected Calibration Error (ECE)** | **0.0217** | Probabilities correspond directly to observed historical frequencies |
| **Brier Skill Score (BSS)** | **+44.18%** | Massive 44.2% error reduction compared to climatology baseline |
| **Tamper Detection Latency** | **2.08 ms** | Real-time SHA-256 integrity checker intercepts corrupted artifacts |
| **Disaster Recovery MTTR** | **0.02 s** | Instantaneous automated rollback to Phase 0 baseline snapshot (<60s SLA) |

---

## Key Architecture Pillars

1. **100% Real Data Foundations:** Zero synthetic samples in training or validation splits. Derived from Copernicus ECMWF ERA5-Land and official HPSDMA disaster inventories.
2. **Authentic Explainability:** Replaced presentation fictions with exact closed-form marginal log-odds attributions derived directly from model weights.
3. **Decoupled Risk Policy:** Separated pure statistical flood probability ($P_{\text{cal}} \in [0, 1]$) from operational disaster policy scoring ($S_{\text{risk}} \in [0, 100]$) scaled through a normalized hazard ratio.
4. **Deterministic 20-Substep Scenario Engine:** Drives all 22 Mandi settlements through 15-feature weather evolutions (baseline, onset, saturation, peak surge, recession).
5. **Continuous Drift & Covariate Monitoring:** Computes Population Stability Index (PSI) with Laplace smoothing across live 48-hour telemetry windows.

---

## Quick Start (Docker Compose)

Launch the entire stack with a single command:

```bash
docker compose up --build
```

- **Frontend Dashboard**: `http://localhost:5173`
- **FastAPI Documentation**: `http://localhost:8000/docs`
- **System Health Check**: `http://localhost:8000/health`
- **Covariate Drift Report**: `http://localhost:8000/api/v1/system/drift`

### Demo Mode Quick Access
On the login screen, click **"Demo Mode Quick Access"** to automatically authenticate with pre-seeded credentials (`demo` / `flowshield2026`).

---

## Verification & Testing Suite

Run the full unified test suite (83 tests) with zero failures:

```bash
# Run ML pipeline, simulation, and adversarial regression tests
pytest tests/ -v

# Run full API endpoint and integration tests
pytest apps/api/tests/ -v

# Run disaster recovery chaos drill
python scripts/execute_rollback_drill.py
```

---

## Production Documentation Directory

- **[Production ML Model Card](docs/PRODUCTION_ML_MODEL_CARD.md)**: Mitchell et al. (2019) compliance, architecture specifications, and quantitative benchmarks.
- **[Operational Runbook](docs/OPERATIONAL_RUNBOOK.md)**: Day-to-day SRE procedures, drift monitoring, retraining guidelines, and emergency rollback.
- **[Incident Response Guide](docs/INCIDENT_RESPONSE_GUIDE.md)**: P1/P2/P3 severity classifications, escalation matrices, and recovery playbooks.
- **[Final Test Set Certificate](ml/reports/final_production_test_report.md)**: Unbiased locked test evaluation report and cryptographic verification digest.
- **[Rollback Drill Report](ml/reports/rollback_drill_report.json)**: Chaos experiment validation confirming MTTR < 60s.
- **[Technical Requirements Document (TRD)](docs/TRD.md)**: Schemas, PostGIS queries, and security protocols.

---

## License & Team
Developed for **Smart India Hackathon 2026** by Team Flowshield. Released under the MIT License.

