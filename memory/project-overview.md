# Flowshield — Project Overview

> **“Predict Early. Act Faster. Save Lives.”**

---

## 1. Problem Statement & Hackathon Context

- **Event**: Smart India Hackathon (SIH) 2026
- **Problem Statement ID**: **26192**
- **Theme**: Disaster Management
- **Category**: Software
- **Core Challenge**: **Flash Flood Prediction System for Hilly Regions using Multi-Source Data**

### Mountain Flash Flood Dynamics
In steep Himalayan catchments (such as Himachal Pradesh and Uttarakhand), sudden intense cloudburst precipitation rapidly overwhelms shallow mountain soils. Runoff concentrates into narrow river valleys within 30 to 60 minutes, causing catastrophic debris flows, bridge washouts, and settlement inundation before conventional regional forecast models can warn local responders.

Flowshield solves this critical latency and communication challenge by uniting multi-source physical telemetry, machine learning, local explainability, operational risk modeling, spatial GIS catchments, safe shelter allocations, and clear citizen warnings into an integrated system.

---

## 2. Geographic Target

- **Primary Basin**: Upper Beas River Basin
- **Target District**: Mandi District, Himachal Pradesh, India
- **Monitored Settlements**: 20 critical settlements spanning low-valley riverbanks to steep hillside elevations (480m to 2,450m), including Mandi Urban, Pandoh, Aut, Thalout, Larji, Bali Chowki, Sundernagar, and Joginder Nagar.
- **Critical River Reaches**: Beas Main Stem, Uhl River, Suketi Khad, and Tirthan Stream.
- **Relief Infrastructure**: 8 designated safe community shelters (schools, community halls, temples on safe high contours).
- **Evacuation Corridors**: 5 primary mountain road corridors assessed dynamically for river-crossing causeway submergence.

---

## 3. Target Personas & User Journeys

### Persona 1: District Disaster Management Authority (DDMA) / SDRF Commander
- **Role**: District Magistrate, Disaster Management Officer, SDRF / NDRF Incident Commander.
- **Primary Interface**: **Authority Command Center** ([`how-to-run.md`](./how-to-run.md) -> `/dashboard`).
- **Core Needs**:
  1. Instant regional situational awareness through color-coded GIS catchment polygons.
  2. Actionable operational risk scores (0–100) that separate statistical probability from decision urgency.
  3. Local explainability (SHAP TreeExplainer) to understand *why* the model is escalating risk (e.g., intense 3h rain vs. upstream gauge surge).
  4. Decision-support standard operating procedures (SOPs) with one-click dispatches.
  5. Evacuation corridor monitoring to verify which causeways and bridges are impassable.

### Persona 2: Mountain Settlement Citizen / Tourist
- **Role**: Local village resident, farmer, shopkeeper, or traveler in steep valleys.
- **Primary Interface**: **Citizen Emergency Mode** ([`how-to-run.md`](./how-to-run.md) -> `/citizen`).
- **Core Needs**:
  1. Ultra-fast, zero-jargon mobile view (down to 320px screen width).
  2. High-contrast plain-language status banners: **NORMAL**, **WATCH**, **WARNING**, or **EVACUATE NOW**.
  3. Actionable preparedness checklist (waterproof go-bag, ID safeguarding, utility shutoffs).
  4. Nearest safe high-ground shelter with walking distance and GPS navigation.
  5. One-tap emergency helpline buttons: SDRF (`1070`), District EOC (`1077`), Police (`112`), Ambulance (`108`).

---

## 4. Key Architectural Subsystems

Flowshield is organized as an enterprise modular monolith consisting of seven core subsystems:

1. **Environmental Ingestion & Bounds Engine**: Validates raw sensor streams across 15 canonical physical features (7 accumulation windows, 3 soil moisture depths, API, topography) against strict geological bounds.
2. **Machine Learning & SHAP Explainability**: Trained XGBoost Classifier with inverse class weighting (91.6% ROC-AUC, 88.2% recall on real historical storm events) coupled with real-time TreeExplainer feature attributions and fallback hydrologic heuristics.
3. **Operational Risk Engine**: Formula blending ML probability, river surge rate, vulnerability index, and sensor freshness penalties.
4. **GIS & Spatial Voronoi Engine**: PostGIS spatial layers joined with precomputed Voronoi catchment polygons representing hydrological zones of influence.
5. **Deterministic Simulation State Machine**: 20-substep reproducible scenario engine (seed: `26192`) across 5 meteorological stages from normal baseline to critical inundation.
6. **Alert Lifecycle & SOP Engine**: Threshold evaluation, deduplication keys, operator acknowledgement, and statutory disclaimers.
7. **Shelter & Evacuation Intelligence**: Real-time shelter occupancy tracking and floodway bridge blockage detection.

Cross-references:
- System Architecture: [`architecture.md`](./architecture.md)
- Domain Rules & Formulas: [`business-rules.md`](./business-rules.md)
- Technology Stack: [`tech-stack.md`](./tech-stack.md)
