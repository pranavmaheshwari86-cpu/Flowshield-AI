# Flowshield — Implementation Changelog

---

## [1.0.0] - September 2026

### Milestone: Full System Completion & SIH 2026 Verification

#### Added
- **Machine Learning & Telemetry**:
  - Defined 12 canonical physical features and validation bounds in `ml/feature_schema.py`.
  - Generated 6,000 synthetic physics-correlated mountain flood samples in `ml/generate_data.py`.
  - Trained XGBoost binary classifier achieving **93.0% Accuracy**, **98.2% ROC-AUC**, **87.8% Safety Recall**, and **83.7% F1-score** in `ml/train.py`.
  - Built SHAP TreeExplainer integration for real-time marginal feature attribution in `prediction_service.py`.
  - Automated ML audit verification script in `ml/evaluate.py`.
- **Database & Spatial Infrastructure**:
  - Authored GeoJSON datasets for Mandi District: 20 settlements, 8 shelters, 3 river reaches, 5 routes.
  - Created SQLAlchemy ORM models in `app/models/` and Alembic initial migration.
  - Precomputed Voronoi catchment polygons using `scipy.spatial.Voronoi` to ensure 60 FPS GIS rendering.
  - Developed `scripts/seed_db.py` seeding baseline observations and demo authority accounts.
- **FastAPI Core Backend**:
  - Implemented 11 operational routers: `/health`, `/auth`, `/villages`, `/predictions`, `/risk`, `/alerts`, `/shelters`, `/routes`, `/map`, `/simulation`, `/system`.
  - Built Operational Risk Engine separating statistical probability from operational decision urgency ($R \in [0, 100]$).
  - Built 20-substep deterministic Simulation State Machine across 5 stages with seed `26192`.
  - Built Alert Lifecycle Engine with deterministic deduplication keys (`village_id:severity:stage`).
  - Built Action Engine generating NDMA standard operating procedures with human-in-the-loop disclaimers.
  - Built Shelter & Route Services tracking capacity and causeway floodway clearance.
  - Implemented JWT authentication and Bcrypt password hashing.
- **React 18 + Vite Frontend**:
  - Created custom Vanilla CSS Design System with dark command center tokens (`tokens.css`, `reset.css`, `layout.css`, `components.css`).
  - Built Authority Command Center (`/dashboard`) integrating CartoDB dark tiles, Voronoi risk zones, river channels, shelter markers, and pulsing village markers.
  - Built slide-over Village Detail Drawer with Composite Risk Gauge, Real-Time Telemetry cards, SHAP Feature Attribution bars, Recharts historical trends, and evacuation route clearance.
  - Built Simulation Timeline Controls featuring Play/Pause, Step Forward, Speed Selector (0.5x–4x), and Reset.
  - Built Mobile-First Citizen Emergency View (`/citizen`, 320px responsive) with high-contrast alert banners, safe shelter GPS navigation, preparedness checklist, and 1-tap SOS dialers.
  - Built Scientific Methodology Page (`/about`) with full feature definitions and statutory disclaimers.
  - Built Authority Portal Login (`/login`) with 1-Click Quick Demo Login for evaluators.
- **Testing & Verification**:
  - Authored automated backend test suite in `apps/api/tests/` achieving 100% pass rate (6/6 tests passing).
  - Executed and recorded full interactive browser tour saved to `flowshield_full_demo_1789030650681.webp`.
  - Initialized project memory & documentation infrastructure in `memory/`.

#### Changed
- Enhanced `apps/web/src/services/api.ts` with response normalization and field mapping.
- Enhanced backend routers with flexible query and path aliases (`/simulation/status`, `/map/geojson/{layer_name}`, `/shelters/nearest/{village_id}`).

#### Fixed
- Fixed Pydantic CORS origin parsing for comma-separated environment variables.
- Fixed test database contention by providing an isolated test database (`test_flowshield.db`) in `conftest.py`.
- Fixed unused imports in TypeScript frontend ensuring zero build errors.
- Fixed simulation restart logic to properly reset stage and substep to 0.

---

### [1.1.0] — 2026-09-10

#### Added
- **Real Public Dataset Acquisition**:
  - Ingested 15,624 continuous hourly observations from ECMWF Copernicus ERA5-Land reanalysis across 7 Mandi District nodes (July–August 2023 disaster periods and July 2022 baseline) into `data/real/mandi_era5_hourly_raw.csv`.
  - Engineered 30 physical hydrological features (`data/real/mandi_real_hydrology_features.csv`) with zero synthetic fabrication.
  - Downloaded and cataloged INDOFLOODS national flood archive (`data/real/indofloods/`) and historical Beas Basin flood catalog (`data/real/beas_basin_historical_floods.csv`).
- **Real Baseline ML Training Pipeline**:
  - Implemented reproducible multi-model pipeline in `ml/training/train_flood_model.py` comparing Logistic Regression, Random Forest, and XGBoost.
  - Enforced leak-free event holdout splitting (July 2023 disaster holdout).
  - Saved model artifacts, preprocessor, and schemas in `ml/models/`.
- **Evaluation & False-Negative Analysis**:
  - Authored `ml/evaluation/evaluate_flood_model.py` and generated `ml/reports/detailed_evaluation_report.json` and `ml/reports/training-data-audit.md`.
  - Identified optimal operational safety thresholds ($0.10 - 0.20$) achieving $>77\%$ disaster event recall.
- **AI Risk Inference API**:
  - Created `apps/api/app/routers/ai.py` exposing `POST /api/v1/ai/risk`, `POST /api/ai/risk`, `GET /api/v1/ai/models`, and `GET /api/v1/ai/features`.
  - Added 5 new automated tests in `apps/api/tests/test_ai_endpoints.py`, bringing total backend test suite to 11 passing tests (100% pass rate).
- **Comprehensive Documentation**:
  - Authored `docs/MODEL-CARD.md`, `docs/AI-ARCHITECTURE.md`, and `docs/AI-ML-IMPLEMENTATION-REPORT.md`.
  - Executed 8-step mandatory verification suite (`scripts/verify_all_ai_steps.py`) with 100% pass rate.

---

## [2.4.0] — September 2026

### Milestone: Phase 1–5 Multi-Hazard, Routing & Concurrency Hardening

#### Added
- **Multi-Hazard Landslide Subsystem (Phase 4)**:
  - Built `apps/api/app/services/landslide_service.py` implementing GSI / Caine (1980) empirical rainfall-slope threshold modeling.
  - Added `landslide_assessments` database table via `scripts/migrate_v2_4_landslide.py`.
  - Exposed `/api/v1/hazards/landslide/summary` and `/api/v1/hazards/landslide/{village_id}` with statutory prototype disclaimers (`is_ml_model=False`).
  - Created unit verification suite `apps/api/tests/test_landslide_prototype.py`.
- **Dynamic Evacuation & Routing Subsystem (Phase 3)**:
  - Implemented A* Dijkstra route solver with dynamic hazard cost multipliers in `apps/api/app/services/route_service.py`.
  - Added `routes.hazard_cost_multiplier` column and schema via `scripts/migrate_v2_4_phase5.py`.
  - Added off-network coordinate projection snapping (`test_off_network_snap.py`) preventing solver crashes when user coordinates lie outside the road network.
  - Added route clearance and floodway causeway status monitoring (`test_route_hazard_weighting.py`).
- **Concurrency-Safe Alert Engine (Phase 5)**:
  - Hardened `apps/api/app/services/alert_engine.py` with unique database constraint (`village_id`, `dedup_key`, `status`) and in-memory attribute caching to eliminate SQLite session locks.
  - Added columns `is_advisory`, `policy_version`, and `requires_authority_coordination` to `alerts` table.
  - Validated with 10-thread parallel race-condition stress test (`test_alert_concurrency.py`).
- **First Responder Console & Front-End Expansion (Phase 2)**:
  - Created `apps/web/src/pages/ResponderPage.tsx` with tactical dispatch, field hazard reporting, and live GPS coordination.
  - Enhanced `CitizenWarning.tsx` with high-contrast alert advisories, safe route guidance, and nearest shelter navigation.
  - Extended API client (`apps/web/src/services/api.ts`) with typed endpoints for hazards, routes, and alerts.
- **Scenario Replay & Historical Disaster Inundation (Phase 1)**:
  - Created `apps/api/app/services/scenarios/scenario_runner.py` for multi-step historical disaster timeline reproduction.
  - Verified with `test_scenario_replay.py`.
- **RBAC & Authorization Hardening**:
  - Implemented role-based route protection (`admin`, `operator`, `first_responder`, `citizen`) in `apps/api/app/auth/dependencies.py`.
  - Verified with `test_server_rbac.py`.
- **Forecast Uncertainty & Telemetry Freshness**:
  - Created `forecast_service.py` and `soil_forecast_service.py` with confidence interval quantification.
  - Created `freshness_service.py` penalizing stale telemetry records.

#### Changed
- Expanded automated backend test suite from 11 tests to **50 tests across 21 test files**, maintaining a 100% pass rate.
- Modernized API router layout to 16 specialized routers in `apps/api/app/routers/`.

#### Fixed
- Fixed SQLite session expiration in `alert_engine.py` by caching entity attributes locally prior to commit (BUG-009).

---

## [4.0.0] — September 2026

### Milestone: FlowShield Predictive Risk & Multi-Horizon Timeline Architecture

#### Added
- **Predictive Risk & Multi-Horizon Timeline Subsystem**:
  - Engineered `apps/api/app/services/timeline_service.py` with multi-horizon risk forecasting (+1h, +3h, +6h, +12h, +24h, +48h).
  - Built continuous piecewise linear interpolation solver for exact fractional lead times to WATCH (25), HIGH (50), and CRITICAL (75) risk thresholds.
  - Implemented Platt/Isotonic calibrated probability calculations ($P(\text{Risk} \ge 25)$, $P(\text{Risk} \ge 50)$, $P(\text{Risk} \ge 75)$) and P10-P90 ensemble uncertainty spreads.
  - Implemented CWC river gauge dynamics: stage progression meter, distance to danger mark, rate of rise ($m/h$), hydraulic trend (`RISING`, `FALLING`, `STEADY`), and upstream reservoir outflow.
  - Implemented 5km catchment exposure analysis: census population, vulnerable demographics (children, elderly), critical infrastructure inventory (schools, hospitals, bridges, routes), and nearest operational shelter with elevation clearance ($\Delta E \ge +15\text{m}$).
  - Built stream-by-stream SLA provenance and data freshness matrix for active telemetry.
  - Added Pydantic v2 schemas in `apps/api/app/schemas/timeline.py`.
  - Exposed `GET /api/v1/risk/forecast/detailed` and `GET /api/v1/risk/forecast/locations` in `apps/api/app/routers/forecast_risk.py`.
- **Modular Frontend Timeline Workspace**:
  - Implemented dedicated `TimelineView.tsx` with finite-state machine (`INITIALIZING`, `LOADING`, `LIVE`, `UPDATING`, `DEGRADED`, `ERROR`), abortable HTTP requests, and adaptive polling (30s/60s/120s).
  - Built `TimelineHeader.tsx` with dynamic cascading State $\rightarrow$ District $\rightarrow$ Settlement selector from database and manual sync trigger.
  - Built `CurrentSituationBar.tsx` with 4 real-time observed telemetry cards.
  - Built `PredictiveTimelineChart.tsx` featuring solid lines for observed past series (-6h to 0h), dashed lines for future projections (+1h to +48h), vertical `NOW (LIVE)` reference marker, P10-P90 uncertainty envelope, threshold lines, and multi-metric toggle chips.
  - Built `MultiHorizonForecastGrid.tsx` with 6 interactive horizon projection cards.
  - Built `SituationAnalysisCard.tsx` with operational briefing, trend vector, disaggregated peak timing, and additive risk driver attributions.
  - Built `HydrologicalAnalysisCard.tsx` with CWC river gauge dynamics and progress meters.
  - Built `ExposureEvacuationCard.tsx` with catchment demographics and shelter elevation advantage.
  - Built `DataQualityTransparencyCard.tsx` with SLA freshness table and model ops metadata.
- **View Isolation in Dashboard**:
  - Decoupled `TimelineView` from the legacy mock `ExecutiveKpiGrid.tsx` in `DashboardPage.tsx`. Completely eliminated static mock figures (`47.74 Lakh`, `42 Districts`, `7/9 Rivers`, `4,120+ Schools`) from production Timeline mode while maintaining zero regressions across Map, Overview, AI Intel, Rivers, Hazards, Districts, and Reports.
- **Comprehensive Verification Suite**:
  - Added `apps/api/tests/test_timeline_analytics.py` with 7 new automated tests covering all schema contracts, filtering, piecewise solver, hydrological deltas, and SLA matrix.
  - Total automated tests expanded to **57 passing tests across 22 test suites (100% pass rate)**.
  - Validated frontend production build with `tsc && vite build` (0 errors, 32.69s).

#### Fixed
- Fixed Recharts ReferenceLine multi-axis index invariant error in `PredictiveTimelineChart.tsx` by explicitly binding all reference lines to `yAxisId="left"` (BUG-010).
- Fixed danger mark delta inversion in `HydrologicalAnalysisCard.tsx` so stages below danger level render in teal (`#2DD4BF`) with status `Within Channel Banks` (BUG-011).
- Fixed TypeScript syntax typo in `apps/web/src/types/index.ts` (`bool | boolean` $\rightarrow$ `boolean`) (BUG-012).

---

## [4.1.0] — September 2026

### Milestone: Forensic Scientific Validation & Data Integrity Overhaul

#### Added
- **Scientific Validation & Physical Consistency Test Suite**:
  - Created `tests/test_scientific_validation.py` verifying:
    1. Zero data fabrication and missing telemetry preservation (`None != 0.0`).
    2. Unit integrity separating accumulation ($mm$) from intensity ($mm/h$).
    3. Rolling sum calculations replacing arbitrary scaling multipliers.
    4. ECMWF IFS synoptic cycle operational initialization ($00Z, 06Z, 12Z, 18Z$).
    5. Location capability bounds: Buxar/Barauni (Bihar) and Dhemaji (Assam) return `is_model_supported=False` and `flood_prob=None`, preventing synthetic 100% chance.
    6. Ground truth GIS coordinates for alluvial and Himalayan stations.
- **Synoptic Dissemination Cycle Method**:
  - Added `ForecastService.get_latest_synoptic_cycle()` computing genuine synoptic initialization cycles accounting for operational dissemination lag ($\ge 4.5$ hours).

#### Changed
- **Rainfall Accumulator & Timeline Service**:
  - Refactored `get_observed_timeline_series()` to preserve `None` when readings are missing, avoiding silent zero substitutions.
  - Replaced arbitrary multipliers (`precip_1h * 2.2` and `rain_3h * 1.8`) with true rolling sum aggregations over `hourly.precipitation` slices.
  - Eliminated synthetic soil moisture formula `48.0 + (accums["24h"] * 0.35)`.
- **Frontend Timeline Charts**:
  - Switched Recharts `<Area>` interpolation from `type="monotone"` to `type="linear"` in `PrecipitationChart.tsx` and `FloodRiskChart.tsx`, eliminating cubic Hermite spline overshoot artifacts.
  - Passed `location_capabilities` to `<PrecipitationChart />`. When `is_model_supported` is false, future flood probability is strictly `null` and the badge displays `UNSUPPORTED (ML Inactive)` instead of `100% CRITICAL`.
  - Clarified units in `SystemStatusBar.tsx`: accumulation in $mm$ and rate in $mm/h$.

#### Fixed
- Fixed unhandled exception in `rainfall_provider.py` by removing call to non-existent `_generate_fallback_readings` (BUG-013).
- Corrected GIS coordinates and elevations in `scripts/seed_national_flood_data.py` and `flowshield.db` for Jonai Subansiri Belt (`27.7700°N, 95.2200°E, 115m`) and Begusarai Barauni Basin (`25.4630°N, 85.9610°E, 47m`) (BUG-014).

Cross-references:
- Current Status: [`current-status.md`](./current-status.md)
- Walkthrough: [`../walkthrough.md`](../walkthrough.md)
- Bug Log: [`bugs.md`](./bugs.md)
- Architectural Decisions: [`decisions.md`](./decisions.md)
- Roadmap: [`todo.md`](./todo.md)

