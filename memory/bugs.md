# Flowshield — Known Issues & Bug Resolution Log

---

## 1. Resolved Bugs & Mitigations

### BUG-001: Pydantic CORS Parsing Error from Environment Variables
- **Symptom**: FastAPI startup crashed with `SettingsError` when reading comma-separated `CORS_ORIGINS` from `.env`.
- **Root Cause**: Pydantic v2 `BaseSettings` expects JSON lists for list fields by default when loaded from environment strings.
- **Resolution**: Implemented a `@field_validator("CORS_ORIGINS", mode="before")` in `apps/api/app/config.py` that splits comma-separated strings into trimmed lists:
  ```python
  @field_validator("CORS_ORIGINS", mode="before")
  @classmethod
  def parse_cors_origins(cls, v: Any) -> List[str]:
      if isinstance(v, str):
          return [origin.strip() for origin in v.split(",") if origin.strip()]
      return v
  ```
- **Status**: **RESOLVED**

---

### BUG-002: Pytest Database Contention with Active Dev Server
- **Symptom**: `pytest tests/test_simulation.py` failed with `assert 5 == 8` or `assert 9 == 8` during simulation substep checks.
- **Root Cause**: Pytest was running against the shared SQLite database `flowshield.db` while the background `uvicorn` dev server and browser walkthrough were actively stepping the simulation concurrently.
- **Resolution**: Updated `tests/conftest.py` to isolate test execution using a dedicated temporary database:
  ```python
  os.environ["DATABASE_URL"] = "sqlite:///./test_flowshield.db"
  ```
  with automatic teardown and deletion after the test session completes.
- **Status**: **RESOLVED (6/6 tests passing 100%)**

---

### BUG-003: Unused Variable Compilation Failure in Vite Production Build
- **Symptom**: `npm run build` failed with TypeScript errors (`TS6133: 'ShieldAlert' is declared but its value is never read`).
- **Root Cause**: `tsconfig.json` enforces `noUnusedLocals: true`.
- **Resolution**: Removed unused Lucide icon imports across `AlertFeed.tsx`, `AboutPage.tsx`, `DashboardPage.tsx`, and `LandingPage.tsx`.
- **Status**: **RESOLVED (`npm run build` exits with code 0)**

---

### BUG-004: Missing Leaflet Default Marker Icons in Vite Bundler
- **Symptom**: Standard Leaflet blue pin icons failed to render or showed broken image icons when bundled with Vite.
- **Root Cause**: Known Leaflet asset bundling issue where default marker image URLs are not statically resolvable by modern ES module bundlers.
- **Resolution**: Completely replaced default image markers with custom, high-tech HTML/SVG `L.divIcon` elements featuring dynamic risk-tier background colors, pulsating radar rings for critical alerts, and emergency icons.
- **Status**: **RESOLVED**

---

### BUG-005: Simulation Re-Start Preserving Stale Terminal Stage
- **Symptom**: Calling `POST /api/v1/simulation/start` when a previous run had completed preserved stage 4, preventing a clean restart without manual reset.
- **Root Cause**: `start_simulation` updated `sim.status = "RUNNING"` but did not reset `current_stage = 0` and `current_substep = 0`.
- **Resolution**: Updated `SimulationEngine.start_simulation` in `apps/api/app/services/simulation_engine.py` to explicitly reset `current_stage` and `current_substep` to 0.
- **Status**: **RESOLVED**

---

### BUG-006: Unseeded Demo Authority User in Initial Database Run
- **Symptom**: 1-Click Quick Demo Login returned `401 Unauthorized` with `Invalid authority credentials`.
- **Root Cause**: `scripts/seed_db.py` initially seeded spatial entities and observations but omitted user credentials.
- **Resolution**: Added automatic user creation for `demo` (`flowshield2026`) and `admin` (`password123`) using Bcrypt hashing in `seed_db.py`.
- **Status**: **RESOLVED**

---

### BUG-007: ML Artifact Path Resolution in Nested API Subdirectory
- **Symptom**: `RealFloodPredictor` failed with `FileNotFoundError: ml/artifacts/xgboost_flood_model.json` when uvicorn launched from `apps/api`.
- **Root Cause**: Relative path `ml/artifacts/...` was evaluated from current working directory, which differed between root-level scripts and `apps/api` backend launches.
- **Resolution**: Implemented multi-tiered project root resolution in `ml/inference/predict.py`:
  ```python
  candidate_roots = [
      Path.cwd(),
      Path(__file__).resolve().parents[2],
      Path(__file__).resolve().parents[3],
  ]
  ```
- **Status**: **RESOLVED**

---

### BUG-008: Flash Flood Target Class Imbalance False Negative Bias
- **Symptom**: Unweighted XGBoost model achieved 91% accuracy by predicting "No Flood" on nearly all records, missing rapid onset flash floods.
- **Root Cause**: Severe class imbalance in 10-year observational dataset (flood events comprised only ~11.4% of high-precipitation records).
- **Resolution**: Computed dynamic inverse frequency weighting `scale_pos_weight = n_negative / n_positive` (7.74) during training and optimized decision threshold to 0.42, boosting minority event recall to 88.2%.
- **Status**: **RESOLVED**

---

### BUG-009: SQLite Session Expiration in Concurrent Multi-Threaded Alert Generation
- **Symptom**: `test_alert_concurrency_stress_test` intermittently raised `ObjectDeletedError: Instance '<Village>' has been deleted, or its row is otherwise not present` during concurrent worker executions.
- **Root Cause**: In SQLite with concurrent worker threads, `db.commit()` expires session instances by default (`expire_on_commit=True`). Subsequent logger calls reading `village.name` and `village.id` attempted a lazy-load on an expired ORM instance whose session had completed or collided with another thread.
- **Resolution**: Cached `village_id = village.id` and `village_name = getattr(village, "name", "Unknown Village")` into local stack variables before `db.add` and `db.commit`, preventing post-commit lazy loads.
- **Status**: **RESOLVED (Verified by 10-thread parallel stress test)**

---

### BUG-010: Recharts ReferenceLine Multi-Axis Index Invariant Error
- **Symptom**: Vertical reference line `NOW (LIVE)` and threshold horizontal lines failed or caused internal Recharts crashes when rendering `PredictiveTimelineChart.tsx`.
- **Root Cause**: When a `ComposedChart` defines explicit custom axis identifiers (`yAxisId="left"` and `yAxisId="right"`), any child `<ReferenceLine>` without an explicit `yAxisId` attempts to query default numeric axis `0`, which does not exist in the Recharts scale map.
- **Resolution**: Bound all `<ReferenceLine>` components to `yAxisId="left"`.
- **Status**: **RESOLVED**

---

### BUG-011: Hydrological Gauge Danger Margin Condition Inversion
- **Symptom**: Water levels below official CWC danger marks displayed as `+2.59m OVER DANGER` in red alert styling in `HydrologicalAnalysisCard.tsx`.
- **Root Cause**: `timeline_service.py` calculates `margin_to_danger_meters = round(current_stage - danger_m, 2)`. Safe stages produce negative deltas. Line 27 evaluated `marginToDanger < 0` for `isOverDanger`, inverting the alert condition.
- **Resolution**: Updated condition to `marginToDanger > 0` and rendered safe margins with `Math.abs(marginToDanger)` as `2.59m below danger mark` in teal (`#2DD4BF`) with status `Within Channel Banks`.
- **Status**: **RESOLVED**

---

### BUG-012: TypeScript Union Syntax Error in Timeline Schema Types
- **Symptom**: `npm run build` failed with TypeScript compile errors on `apps/web/src/types/index.ts`.
- **Root Cause**: `is_crossed: bool | boolean;` was typed with invalid Python-style `bool` keyword.
- **Resolution**: Corrected type signature to `is_crossed: boolean;`.
- **Status**: **RESOLVED**

---

## 2. Active Considerations & Edge Cases

| Issue ID | Description | Severity | Workaround / Mitigation |
|---|---|---|---|
| **EDGE-001** | Vite bundle size warning (`> 500 kB` after minification due to Leaflet + Recharts). | Low | Assets are gzipped to ~229 kB; acceptable for desktop command centers. Can apply `React.lazy()` dynamic imports in future optimization. |
| **EDGE-002** | CartoDB tile loading over slow internet connections. | Low | MapContainer specifies dark background `#060d17` as solid canvas fallback while tiles stream in. |
| **EDGE-003** | Pydantic v2 deprecation warning for `class Config: from_attributes = True`. | Low (Deprecation warning only) | Future maintenance will migrate from `class Config` to `model_config = ConfigDict(from_attributes=True)`. |

Cross-references:
- Current Status: [`current-status.md`](./current-status.md)
- How to Run: [`how-to-run.md`](./how-to-run.md)
- Decisions: [`decisions.md`](./decisions.md)

