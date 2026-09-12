# Flowshield — Execution & Demonstration Guide

---

## 1. Prerequisites

- **Python**: Version `3.10` or higher (`3.12` recommended).
- **Node.js**: Version `18.0` or higher (`20+` recommended).
- **Package Managers**: `pip` and `npm`.
- **Operating System**: Compatible with Windows, Linux, and macOS.

---

## 2. Initial Setup & Seeding

### Step 2.1: Environment Configuration
Copy the sample environment file to `.env`:
```powershell
cp .env.example .env
```
*(Default settings configure SQLite local fallback and permissive development CORS).*

### Step 2.2: Install Backend Dependencies & Train ML Baseline
```powershell
pip install -r apps/api/requirements.txt
```
To train or re-evaluate the real-data XGBoost flood baseline using 10-year ERA5 and IndoFloods data:
```powershell
# 1. Feature Preprocessing (Generates 15 canonical features)
python ml/preprocessing/pipeline.py

# 2. Train Cost-Sensitive XGBoost Model
python ml/training/train_flood_model.py

# 3. Comprehensive Evaluation & Benchmark Reporting
python ml/evaluation/evaluate_model.py

# 4. Verify Full 8-Step System Integration
python scripts/verify_all_ai_steps.py
```

### Step 2.3: Install Frontend Dependencies
```powershell
cd apps/web
npm install
cd ../..
```

### Step 2.4: Seed Database
Initialize tables, precompute Voronoi polygons, seed 20 Mandi settlements, 8 shelters, 3 river reaches, 5 evacuation corridors, baseline telemetry, and authority users:
```powershell
python scripts/seed_db.py
```

---

## 3. Running Services Locally

### Step 3.1: Start FastAPI Backend
From `apps/api`:
```powershell
cd apps/api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **API Documentation (Swagger UI)**: [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
- **Health Endpoint**: [`http://127.0.0.1:8000/api/v1/health`](http://127.0.0.1:8000/api/v1/health)

### Step 3.2: Start React Frontend
In a separate terminal, from `apps/web`:
```powershell
cd apps/web
npm run dev
```
- **Application URL**: [`http://localhost:5173/`](http://localhost:5173/)

---

## 4. Verification & Testing Commands

### Backend Automated Test Suite
Run from `apps/api`:
```powershell
pytest -v
```
*(Executes all 6 test suites covering health, GeoJSON, predictions, simulation state machine, and village detail endpoints).*

### Frontend Production Build Test
Run from `apps/web`:
```powershell
npm run build
```
*(Performs strict TypeScript compile check and bundles production assets into `dist/`).*

---

## 5. Official 8-Minute Smart India Hackathon Demo Script

Follow this sequence for judging presentations:

1. **Landing Page Overview (Minute 1: Problem & Mission)**:
   - Navigate to `http://localhost:5173/`.
   - Highlight **Problem Statement ID: 26192** (Flash Flood Prediction in Hilly Regions).
   - Point out the **Evaluated ML Performance Card**: 93.0% Accuracy, 98.2% ROC-AUC, $< 15\text{ms}$ latency.
   - Walk through the 5-step data ingestion-to-citizen warning pipeline.

2. **Command Center Situational Awareness (Minute 2–3)**:
   - Click **Launch Authority Command Center** (or navigate to `/dashboard`).
   - Log in using 1-Click Quick Demo Access (`demo` / `flowshield2026`).
   - Demonstrate the dark Leaflet map showing the 20 monitored settlements in Mandi District (Beas Basin).
   - Show the precomputed Voronoi catchment polygons initially colored Green (Low Risk).
   - Review the KPI Cards: At-Risk Population (0), Critical Alerts (0), and All Evacuation Corridors Clear.

3. **Deterministic Simulation Progression (Minute 4–5)**:
   - On the Simulation Controls bar, click **Step** (or toggle **Play Sim**).
   - Watch the progression across the 5 meteorological stages:
     - *Step 1–4*: Normal Baseline $\to$
     - *Step 5–8*: Heavy Monsoon Inception (showers increase to $35\text{mm}$) $\to$
     - *Step 9–12*: Catchment Soil Saturation ($> 85\%$ saturated) $\to$
     - *Step 13–16*: River Surge (Beas River level crosses warning marks) $\to$
     - *Step 17–20*: Critical Inundation & Causeway Blockage.
   - Observe how catchment polygons transition dynamically to Amber, Orange, and flashing Red.

4. **Explainable AI & Village Detail Drawer (Minute 6)**:
   - Click on the **Pandoh** settlement in the sidebar or map.
   - Inspect the slide-over **Village Detail Drawer**:
     - **Operational Risk Gauge**: Score escalates to $\ge 75$ with rising trend indicator.
     - **SHAP TreeExplainer Attributions**: Point out the orange bars demonstrating that 3-hour rainfall accumulation and antecedent soil moisture are the exact drivers of the prediction.
     - **Designated Safe Shelter**: Shows nearest high-ground center with remaining capacity.
     - **Route Clearance**: Shows if the river causeway route is flagged as **BLOCKED**.

5. **Citizen Emergency View & Conclusion (Minute 7–8)**:
   - Click **Citizen Mode** in the navbar (or navigate to `/citizen`).
   - Resize viewport to mobile (320px–375px) to show responsiveness.
   - Display the high-contrast **EVACUATE IMMEDIATELY** alert banner.
   - Review the plain-language preparedness checklist and GPS shelter navigation.
   - Demonstrate the 1-tap emergency dialers for SDRF (`1070`) and District Emergency Center (`1077`).
   - Conclude on **Scientific Methodology** (`/about`) showing the non-forecast disclosures and ethical guardrails.

Cross-references:
- Architecture: [`architecture.md`](./architecture.md)
- Current Status: [`current-status.md`](./current-status.md)
- Deployment: [`deployment.md`](./deployment.md)
