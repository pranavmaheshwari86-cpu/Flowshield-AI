# Flowshield — SIH 8-Minute Evaluation Demo Script

## Preparation
1. Ensure the stack is running: `docker compose up` or local processes active.
2. Open browser at `http://localhost:5173`.
3. Verify the live status bar reads: `API: Online`, `DB: Online`, `Model: Loaded`.

---

## 8-Minute Step-by-Step Script

| Time | Phase | Actions & Visual Presentation | Speaking Points for Evaluators |
|---|---|---|---|
| **0:00 - 1:00** | Introduction & Problem Statement | - Start on Landing Page.<br>- Highlight Problem Statement ID 26192.<br>- Point to the 12-step environmental intelligence pipeline diagram. | "In flash-flood disasters, prediction alone is not enough. Flowshield closes the loop from raw multi-source telemetry to operational risk, SHAP explainability, GIS visualization, alert lifecycle, and citizen warning." |
| **1:00 - 2:00** | Baseline Regional Overview | - Click **"Demo Mode Quick Access"**.<br>- Command Center opens.<br>- Show 20 Himalayan settlements in Mandakini Valley.<br>- All indicators are green (LOW risk).<br>- Select "Kedarnath Settlement" to show baseline telemetry (Rainfall: 6.2 mm, River: 1.4 m, Risk Score: 12). | "We disclose clearly that this baseline is synthetic demonstration data. The system operates on real PostGIS spatial queries, not static mockups." |
| **2:00 - 3:30** | Precipitation Inception | - In the Simulation Console, select **"Gradual Monsoon Escalation"** (Seed 26192).<br>- Click **"Start Simulation"**.<br>- Step through Substeps 0–7.<br>- Low-lying riverbank settlements transition to Amber (MODERATE). | "Notice that higher-elevation settlements stay green while riverbank villages react immediately. The simulation models real spatial hydrological heterogeneity." |
| **3:30 - 5:00** | Soil Saturation & First Warning | - Advance through Substeps 8–11.<br>- Soil moisture exceeds 80%.<br>- Settlements near rivers turn Orange (HIGH).<br>- First HIGH Alert triggers in the Alert Feed.<br>- Point to the trigger headline: *"Catchment soil saturation exceeded 80% with sustained rainfall"*. | "Alerts are evaluated and deduplicated on the backend. Repeated telemetry checks do not spam the operator." |
| **5:00 - 6:00** | Model Explainability with SHAP | - Open the Village Detail Drawer.<br>- Highlight the SHAP Feature Attribution chart.<br>- Show how River Surge Rate (+0.28) and Soil Saturation (+0.24) top the attribution list. | "We show operators why the model evaluated high risk using SHAP TreeExplainer values, labeled strictly as predictive contributors rather than physical causes." |
| **6:00 - 7:00** | Critical Inundation & Closed-Loop Action | - Advance through Substeps 12–19.<br>- Multiple settlements enter Red (CRITICAL).<br>- Action Engine activates: *"Initiate Evacuation Protocol — Activate Primary Shelters"*.<br>- Check nearest shelter: occupancy climbs to 85% with incoming evacuees.<br>- Route assessment marks low-lying causeway route as **BLOCKED (Flooded)** and directs traffic to the upland bypass. | "This proves our complete pipeline: predictions trigger operational actions, shelters adjust capacity, and flood hazards dynamically update route assessments." |
| **7:00 - 7:45** | Citizen Warning Mode | - Switch tab to `/citizen` (view at mobile width 320px).<br>- Show bold red hazard banner: *"CRITICAL FLOOD WARNING"*, simple safety instructions, nearest shelter card with 1-tap call button, and emergency helplines (NDRF 1078, 112). | "Citizens are not overwhelmed with machine learning metrics. They receive actionable, high-contrast, life-safety guidance on any mobile device." |
| **7:45 - 8:00** | Recovery & Conclusion | - Return to Dashboard.<br>- Click **"Reset Simulation"**.<br>- All villages return to green; alerts resolve.<br>- Conclude presentation. | "Flowshield is built on a clean modular monolith that can immediately ingest real-world IMD and CWC API feeds. Thank you." |
