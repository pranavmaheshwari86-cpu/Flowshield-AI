# Flowshield Subsystem Dependency Matrix

**Version**: 4.0.0 (Predictive Risk & Multi-Horizon Timeline)  
**Generated**: September 2026  
**System Architecture**: Flowshield Multi-Hazard Decision Support System (SIH 2026 PS ID 26192)

---

## 1. Interaction Matrix

The matrix below depicts cross-subsystem dependencies, protocols, and coupling classifications across Flowshield v4.0:

| Source \ Target | Web Frontend (`apps/web`) | API Gateway (`app/routers`) | Domain Services (`app/services`) | ML Subsystem (`ml/`) | Database (`app/models`) | Real Data (`data/real`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Web Frontend** | — | REST / JSON & SSE (`HTTP`) | Indirect (via API) | Indirect (via `/api/v1/ai`, `/api/v1/risk`) | None (Decoupled) | None |
| **API Gateway** | Response Payloads | — | Direct Python In-Process Calls | Direct Call via `ai.py` | Direct Dependency Injection (`Session`) | None |
| **Domain Services** | None | Return Pydantic Schemas | Internal Method Invocations | Synchronous Predictor (`RealFloodPredictor`) | SQLAlchemy ORM Sessions / Query | None |
| **ML Subsystem** | None | Schemas (`AIInferenceRequest`) | Exported Risk Scoring | — | Standalone (Config driven) | Ingestion via `pipeline.py` (Pandas) |
| **Database** | None | Data DTOs | ORM Entity State | None | — | Seed scripts read initial catalogs |
| **Scripts & Migrations** | None | Trigger Endpoints | Calls `spatial_service`, `db.init` | Invocations of model training | Direct ORM Insertions / DDL | Raw CSV Preprocessing |

---

## 2. Subsystem Interface Contracts

### 2.1 Web Frontend ↔ API Layer
* **Protocol**: HTTP/1.1 (RESTful JSON APIs) with Server-Sent Events (SSE) for telemetry feeds and adaptive HTTP polling (30s live, 60s normal, 120s degraded) in `TimelineView.tsx`.
* **Authentication**: Bearer JWT tokens with Role-Based Access Control (`admin`, `operator`, `first_responder`, `citizen`).
* **Payload Types**: Strict TypeScript interfaces mirrored from Pydantic schemas in `apps/api/app/schemas/` (`TimelineDetailedResponse`, `VillageResponse`, `AlertResponse`, `RouteResponse`, `HazardAssessmentResponse`).
* **Coupling**: Low (Strict schema contract via OpenAPI spec).

### 2.2 API Routers ↔ Domain Services
* **Protocol**: In-memory Python function invocations with dependency-injected database sessions (`Depends(get_db)`).
* **Error Handling**: Custom `HTTPException` wrappers translating domain exceptions into RFC 7807 Problem Details.
* **Services Involved**: `TimelineService`, `RiskEngine`, `LandslideService`, `RouteService`, `AlertEngine`, `ScenarioRunner`, `ForecastService`.
* **Coupling**: Medium (Clean separation of controller concerns from domain algorithms).

### 2.3 Domain Services ↔ ML Subsystem
* **Bridge Component**: `apps/api/app/services/timeline_service.py`, `prediction_service.py` & `apps/api/app/routers/ai.py`.
* **Inference Pattern**: Multi-horizon (+1h to +48h) predictions with Platt/Isotonic calibrated probabilities and P10-P90 uncertainty quantiles.
* **Latency Guarantee**: Synchronous inference < 25ms per spatial catchment node.
* **Coupling**: Low (Adapter design pattern; model can be retrained or replaced without modifying API contracts).

### 2.4 Multi-Hazard Landslide Service ↔ Risk & Alert Engine
* **Protocol**: Internal domain evaluation (`landslide_service.assess_village_landslide_risk`).
* **Methodology**: Empirical rainfall-slope threshold modeling (GSI / Caine 1980) incorporating 24h/72h antecedent precipitation and topographic slope.
* **Advisory Disclaimer**: All responses carry explicit `status="PROTOTYPE_EMPIRICAL_THRESHOLD"` and `is_ml_model=False` to prevent misrepresentation.

### 2.5 ML Pipeline ↔ Real Data Layer
* **Data Sources**:
  * `data/real/mandi_era5_hourly_raw.csv` (15,624 hourly meteorological observations).
  * `data/real/mandi_real_hydrology_features.csv` (15 canonical hydrologic and soil features).
  * `data/real/indofloods/` (catchment characteristics and historical flood events).
  * `data/real/beas_basin_historical_floods.csv` (Beas basin flood events).
* **Ingestion Strategy**: Deterministic event-based holdout splitting (`FloodEventHoldoutSplitter`), ensuring no temporal or event leakage between train and test sets.
* **Coupling**: Strict data provenance validation (`DATASET_PROVENANCE.md`).

---

## 3. Detected Community Alignment (from `code-review-graph`)

From our automated Louvain/Leiden community detection (`code-review-graph/`):
1. **Community 42 (`assets-props`)**: 2,486 nodes — React component tree, Command Center, Timeline Workspace (`TimelineView.tsx`), Responder Console (`ResponderPage.tsx`), and Citizen portal.
2. **Community 43 (`providers-risk`)**: 465 nodes — Central backend hub containing 17 routers, timeline engine, multi-horizon forecasts, domain services, risk engine, route service, and alert lifecycle.
3. **Community 35 (`scripts-migrate`)**: 18 nodes — Schema expansion scripts, database seeding, and data harvesters.
4. **Community 41 (`training-compute`)**: 8 nodes — ML training loops, model calibration, and threshold optimization.
5. **Community 34 (`ml-evaluate`)**: 5 nodes — Baseline evaluation and metric generation.
6. **Community 36 (`terra-pulse-sih-clean`)**: 4 nodes — Satellite SAR flood label generation and terrain DEM validation.
7. **Community 38 (`inference-load`)**: 4 nodes — Real ML inference pipeline (`ml/inference/predict.py`).
8. **Community 39 (`preprocessing-load`)**: 4 nodes — Data scaling and event holdout splits.
9. **Community 37 (`evaluation-evaluate`)**: 2 nodes — Threshold sweep and safety metrics.
10. **Community 40 (`retraining-retrain-pipeline`)**: 2 nodes — Model retraining and drift evaluation.

---

## 4. Coupling & Architectural Invariants

* **Invariant 1 (Decoupled Frontend)**: Frontend never accesses filesystem, SQLite/PostgreSQL, or raw ML binaries directly.
* **Invariant 2 (Stateless Inference)**: `RealFloodPredictor.predict()` is purely functional given the feature vector; no persistent state is altered during inference.
* **Invariant 3 (Fallback Reliability)**: If ML model artifact loading fails or input features have severe NaNs, the API automatically falls back to deterministic CWC/IMD hydrologic threshold rules, preserving high availability.
* **Invariant 4 (Concurrency Safety)**: Multi-threaded alert evaluations are protected by database unique constraints (`village_id`, `dedup_key`, `status`) and in-memory attribute caching.
* **Invariant 5 (Off-Network Resilience)**: Evacuation route solver projects off-network coordinates to the nearest navigable road node, preventing route calculation crashes.
* **Invariant 6 (Strict No Fake Data in Production Timeline)**: All metrics, trend vectors, exceedance probabilities, and infrastructure counts in Timeline mode originate from live SQLite database models, calibrated ML inference, real CWC gauge telemetry, and numerical weather model feeds.
* **Invariant 7 (Continuous Lead-Time Linear Interpolation)**: Continuous piecewise linear interpolation calculates exact fractional hours until threshold crossings (`WATCH: 25`, `HIGH: 50`, `CRITICAL: 75`), replacing discrete bucketing.
