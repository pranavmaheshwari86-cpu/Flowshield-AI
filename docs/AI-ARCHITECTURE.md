# Flowshield — AI & Decision Support Architecture (V2)

**Version**: 2.0.0 (Production Calibrated Blueprint)  
**Pipeline Identifier**: `flowshield-flood-risk-v2`  
**Standard**: Decision-Support Only / Human-in-the-Loop Governance / Zero Hallucinated Telemetry  
**Hackathon**: Smart India Hackathon 2026 (PS ID: 26192)  

---

## 1. Core Architectural Paradigm

Flowshield adheres to the **Human-Centered Decision Support Principle**:

> **AI recommends, quantifies, and explains; the human Emergency Operations Center (EOC) Commander verifies and authorizes.**

Under no circumstances does an algorithmic output autonomously trigger irreversible actions (e.g. forced community evacuations, reservoir floodgate manipulations, or siren dispatches) without operator confirmation.

---

## 2. Component Separation & V2 Calibrated Decision Pipeline

```
                                FLOWSHIELD AI (V2)
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        ▼                               ▼                               ▼
  Data Quality Guardrail          GIS Engine                     LLM Extraction
 (Validates Telemetry &         (SRTM 30m DEM,                  (Unstructured
  Trips INSUFFICIENT_DATA)       Voronoi Polygons)               Citizen Reports)
        │                               │                               │
        ▼ (If Valid)                    │                               │
  V2 ML Inference Pipeline              │                               │
 ┌─────────────────────────┐            │                               │
 │ Logistic Regression     │            │                               │
 │ (L2 Regularized)        │            │                               │
 └───────────┬─────────────┘            │                               │
             ▼                          │                               │
 ┌─────────────────────────┐            │                               │
 │ Isotonic Calibration    │            │                               │
 │ (Brier 0.028, ECE 0.000)│            │                               │
 └───────────┬─────────────┘            │                               │
             ▼                          │                               │
 ┌─────────────────────────┐            │                               │
 │ Operational Threshold   │            │                               │
 │ (tau = 0.08, Recall>88%)│            │                               │
 └───────────┬─────────────┘            │                               │
             │                          │                               │
             └──────────────────────────┼───────────────────────────────┘
                                        ▼
                               Explainable Triage
                    (Attributions + Operational Risk Index)
                                        │
                                        ▼
                                   EOC Operator
                             (Command Center Review)
                                        │
                                        ▼
                                   Final Action
                         (Alert Dispatch / Prepositioning)
```

---

## 3. Subsystem Functional Breakdown

### 3.1 Subsystem 1: V2 Calibrated ML Flood Risk Classifier (`ml/`)
- **Selected Architecture**: L2-regularized Logistic Regression calibrated via non-parametric **Isotonic Regression** (trained and calibrated on spatial holdout stations: Pandoh Dam and Dharampur Khad).
- **Operational Threshold**: $\tau = 0.08$ frozen to minimize False Negative Rate (FNR = 11.59%, Catastrophe Recall = 88.41% on July 2023 holdout).
- **Input**: 15 canonical physical parameters (1h, 3h, 6h, 24h, 72h rainfall accumulations, topsoil & deep soil moisture saturation %, temperature, pressure, humidity, wind velocity, slope, elevation, river distance, drainage area).
- **Output**: Calibrated flood probability $P_{\text{cal}} \in [0, 1]$, statistical confidence metric, and deterministic physical coefficient attributions.
- **Data Quality Safety Guardrail**: Evaluates physical feasibility. If sensor telemetry is corrupted, negative, or missing without baseline fallback, trips directly to `INSUFFICIENT_DATA` safety state.

### 3.2 Subsystem 2: GIS & Spatial Voronoi Engine (`apps/api/app/services/spatial_service.py`)
- **Engine**: PostGIS 3.4 (production) / SciPy Voronoi & Shapely (local SQLite fallback).
- **Input**: Settlement coordinates, river geometries, Digital Elevation Model (SRTM 30m), safe shelter coordinates.
- **Output**: Voronoi catchment polygons, topographic susceptibility index $T$, distance to river $D_{\text{river}}$, shortest safe evacuation routing graph.
- **Role**: Translates raw point sensor readings into continuous spatial risk zones.

### 3.3 Subsystem 3: LLM Information Extraction & Citizen Report Triage
- **Engine**: Open-source / API-based LLM with deterministic regex and keyword fallback.
- **Input**: Unstructured citizen emergency messages, SOS SMS, or field observer transcripts.
- **Output**: Structured JSON containing:
  - Extracted location / landmark
  - Incident category (e.g., `RIVER_OVERFLOW`, `LANDSLIDE_BLOCKAGE`, `WATERLOGGING`)
  - Deterministic urgency rating (1–5) based on keywords (`trapped`, `rising fast`, `submerged`)
- **Safety Boundary**: LLM is strictly used for **information parsing and translation**, NOT for final emergency triage decisions.

### 3.4 Subsystem 4: Explainable Triage & Operational Risk Engine (`risk_engine.py`)
- **Mathematical Formula**:
  $$R = 0.45 P_{\text{hazard}} + 0.25 T + 0.20 V - 0.05 P + 0.15 (P_{\text{hazard}} \cdot T)$$
  Where:
  - $P_{\text{hazard}}$ = Calibrated flood probability scaled relative to operational threshold $\tau = 0.08$
  - $T$ = Topographic susceptibility factor based on slope, river distance, and elevation
  - $V$ = Vulnerability factor based on population density and housing quality
  - $P$ = Preparedness factor based on nearby shelter capacity and warning lead time
- **5-Tier Operational Risk Hierarchy**:
  1. `INSUFFICIENT_DATA`: Sensor telemetry corrupt/invalid.
  2. `LOW`: Baseline seasonal flow ($R < 25$, $P_{\text{cal}} < 0.04$).
  3. `WATCH`: Catchment priming detected ($25 \le R < 50$ or $0.04 \le P_{\text{cal}} < 0.08$).
  4. `HIGH`: Operational threshold breached ($50 \le R < 75$ or $P_{\text{cal}} \ge 0.08$).
  5. `CRITICAL`: Immediate emergency inundation danger ($R \ge 75$ or $P_{\text{cal}} \ge 0.50$).

---

## 4. Edge Execution & Micro-Latency Profile

The V2 decision pipeline delivers exceptional computational performance:
- **Model Artifact Size**: **0.97 KB** (compared to 150 KB for XGBoost and 775 KB for Random Forest).
- **Inference Latency**: **0.088 ms (P50)** / **0.169 ms (P95)** on commodity CPU.
- **Throughput**: $> 11,000$ risk predictions per second per core.
- **Edge Feasibility**: Fully deployable onto solar-powered micro-gateways (Raspberry Pi, ESP32 cellular RTUs) directly alongside river stations.
