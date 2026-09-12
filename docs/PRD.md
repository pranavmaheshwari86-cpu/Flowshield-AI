# Flowshield — Product Requirements Document (PRD)

**Predict Early. Act Faster. Save Lives.**

*Smart India Hackathon 2026 · Problem Statement ID: 26192 · Theme: Disaster Management · Category: Software*

---

## 1. Executive Summary

Flash floods in Himalayan mountainous terrain develop with catastrophic speed, often giving less than 30 to 60 minutes between sudden cloudburst events, rapid catchment saturation, and devastating river surges. Conventional early warning systems often fail because:
1. They display raw probability percentages that mean little to field responders.
2. They do not model spatial risk gradients across varying topography.
3. They fail to explain what physical factors are driving escalating risk.
4. They do not bridge prediction to human action (shelters, routes, warnings).

**Flowshield** bridges this gap through an end-to-end environmental-intelligence-to-action decision pipeline.

---

## 2. Target Personas & User Journeys

### Persona 1: District Disaster Management Authority (DDMA) Commander
- **Need**: Real-time regional overview, early alert detection, interpretable model contributors, operational risk scoring, and automated decision-support action protocols.
- **Journey**:
  1. Opens Authority Command Center (`/dashboard`).
  2. Observes regional catchment status via interactive GIS map and KPI cards.
  3. Receives automated HIGH/CRITICAL alert notification as risk thresholds cross.
  4. Inspects Village Detail Drawer to view SHAP predictive contributors and 10-point historical risk trends.
  5. Reviews and dispatches recommended decision-support actions.
  6. Monitors shelter capacities and evacuation corridor safety.

### Persona 2: Himalayan Valley Citizen / Tourist
- **Need**: Immediate, zero-jargon safety alerts on mobile viewports, clear action checklists, nearest safe shelter locations, and emergency contacts.
- **Journey**:
  1. Opens Citizen Mode (`/citizen`) on mobile (no login required).
  2. Sees bold color-coded hazard banner (*"CRITICAL FLOOD WARNING"*).
  3. Reads 3 essential plain-language instructions (*"Move to higher ground"*, *"Avoid river causeway"*).
  4. Views designated nearest shelter card with walking distance, occupancy status, and 1-tap call button.
  5. Accesses direct emergency phone numbers (NDRF 1078, Police 112).

---

## 3. Core Functional Requirements

1. **Environmental Data Ingestion & Provenance**: Supports multi-source telemetry (Rainfall 1h/3h/6h/24h, Intensity, Soil Saturation, River Level, River Surge Rate) with metadata tracking (`source`, `is_simulated`, `quality_score`, `freshness_seconds`).
2. **Machine Learning Flood Prediction**: Real XGBoost binary classification model with reproducible random seed and strict feature schema contracts.
3. **Predictive Explainability**: Local SHAP TreeExplainer attribution ranking top predictive contributors for every prediction.
4. **Separation of Probability & Operational Risk**: Explicit distinction between statistical flood likelihood and operational decision risk score (0–100) incorporating trend slope and data quality penalties.
5. **GIS Spatial Intelligence**: PostGIS spatial layers (settlements, Voronoi catchment polygons, river networks, relief shelters, evacuation routes).
6. **Deterministic Simulation Engine**: 5 stages, 20 substeps driven by server-side state machine with fixed PRNG seed (`26192`).
7. **Alert Lifecycle & Deduplication**: Automated alert generation, deduplication keys, operator acknowledgement, and auto-resolution.
8. **Shelter & Evacuation Intelligence**: PostGIS `ST_Distance` queries for nearest shelters and dynamic river-crossing route blockage detection.
9. **Two Dedicated Presentation Views**: Desktop Command Center and Mobile-First Citizen Mode.
