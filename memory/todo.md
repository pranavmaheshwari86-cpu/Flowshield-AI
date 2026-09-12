# Flowshield — Outstanding Work, Priorities & Technical Debt

---

## 1. Completed Milestones

### v1.1.0 Real-Data ML Baseline
- [x] **Verified Public Data Collection**: Harvested 10-year ERA5 hourly meteorological dataset for Mandi district (87,648 hours) and IndoFloods flood catalog (`DATASET_PROVENANCE.md`).
- [x] **15 Canonical Feature Pipeline**: Built `ml/preprocessing/pipeline.py` computing 7 rainfall accumulation horizons, 3 soil moisture layers, API decay, and GIS topography.
- [x] **Data Leakage-Free Splitting**: Implemented `FloodEventHoldoutSplitter` preventing temporal leakage across flood event boundaries.
- [x] **Cost-Sensitive XGBoost Training**: Trained model with inverse class weighting (`scale_pos_weight=7.74`) and threshold optimization ($\tau=0.42$).
- [x] **Comprehensive Model Evaluation**: Implemented `ml/evaluation/evaluate_flood_model.py` producing ROC-AUC (0.916), PR-AUC (0.742), and confusion matrix metrics.
- [x] **Low-Latency Inference Service**: Built `RealFloodPredictor` singleton in `ml/inference/predict.py` (<15ms latency) with deterministic hydrologic fallback.
- [x] **FastAPI Integration**: Added `/api/v1/ai/risk`, `/api/ai/risk`, and `/api/v1/ai/status` endpoints with 100% test pass rate across 11 test suites.

### v2.4.0 Phase 1–5 Multi-Hazard, Routing & Concurrency
- [x] **Multi-Hazard Landslide Subsystem (Phase 4)**: GSI / Caine (1980) empirical rainfall-slope threshold prototype (`landslide_service.py`, `hazard.py`, `test_landslide_prototype.py`).
- [x] **Safe Evacuation Routing (Phase 3)**: Dijkstra A* solver with dynamic hazard cost multipliers and off-network GPS projection (`route_service.py`, `test_off_network_snap.py`, `test_route_hazard_weighting.py`).
- [x] **Concurrency-Safe Alert Engine (Phase 5)**: Atomic database unique index and in-memory attribute caching for multi-worker race conditions (`alert_engine.py`, `test_alert_concurrency.py`).
- [x] **First Responder Command Console (Phase 2)**: Tactical dispatch, field hazard reporting, and live GPS coordination (`ResponderPage.tsx`).
- [x] **Historical Scenario Replay (Phase 1)**: Deterministic disaster replay and timeline reconstruction (`scenario_runner.py`, `test_scenario_replay.py`).
- [x] **Live Data Providers & Connectors**: Open-Meteo ERA5, CWC gauge connectors, and replay engine (`services/providers/`).
- [x] **Server-Side RBAC**: JWT authorization and role separation (`admin`, `operator`, `first_responder`, `citizen`) in `dependencies.py` and `test_server_rbac.py`.
- [x] **Forecast & Soil Uncertainty Quantification**: Confidence interval quantification in `forecast_service.py` and `soil_forecast_service.py`.
- [x] **50-Test Verification Harness**: 21 test suites executing in ~6.2s with 100% pass rate.

---

## 2. High-Priority Technical Debt & Optimizations

- [ ] **Pydantic v2 ConfigDict Modernization**:
  - *Context*: Schema classes in `apps/api/app/schemas/` currently use `class Config: from_attributes = True`, generating Pydantic v2 deprecation warnings in test logs.
  - *Action*: Update schemas to use `model_config = ConfigDict(from_attributes=True)`.
  - *Impact*: Eliminates console deprecation warnings and ensures forward compatibility with Pydantic v3.

- [ ] **Frontend Route Code-Splitting (`React.lazy`)**:
  - *Context*: Vite build outputs bundle warnings because Leaflet and Recharts are bundled together in `index.js`.
  - *Action*: Introduce `React.lazy()` and `Suspense` in `App.tsx` for `/about`, `/citizen`, `/responder`, and `/dashboard`.
  - *Impact*: Reduces initial payload for mobile citizens from ~229 kB (gzipped) to $< 60\text{ kB}$.

- [ ] **Offline Map Tile Caching (IndexedDB / Service Worker)**:
  - *Context*: Citizens in mountain gorges experience total cellular loss during active storms.
  - *Action*: Implement service worker with CacheStorage for Leaflet map tiles and village shelter coordinates.
  - *Impact*: Allows complete offline map and shelter guidance with zero connectivity.

---

## 3. Feature Enhancements & External Integrations

- [ ] **Multilingual Audio Synthesizer (Hindi & Pahari)**:
  - *Action*: Integrate Web Speech API or local audio clips into Citizen Mode to announce emergency status verbally in Hindi and local Himalayan dialects.

- [ ] **DigiLocker Shelter Intake Integration**:
  - *Action*: Implement OAuth 2.0 flow connecting relief camp enrollment to DigiLocker for paperless citizen ID verification. (See [`module-government-ids.md`](./module-government-ids.md)).

- [ ] **Edge LoRaWAN Hardware Packet Decoder**:
  - *Action*: Add binary unpacker service for 16-byte LoRaWAN radio packets transmitted by solar-powered mountain ridge rain gauges.

---

## 4. Quality & Maintenance Backlog

- [ ] **Automated End-to-End Playwright CI Tests**:
  - Set up headless Playwright testing in GitHub Actions to verify simulation step progression and map rendering on pull requests.
- [ ] **PostgreSQL PostGIS Production Benchmark**:
  - Benchmark PostgreSQL connection pooling (`pool_size=20`, `max_overflow=10`) under simulated high-concurrency alert storms.

Cross-references:
- Current Status: [`current-status.md`](./current-status.md)
- Bugs: [`bugs.md`](./bugs.md)
- Decisions: [`decisions.md`](./decisions.md)

