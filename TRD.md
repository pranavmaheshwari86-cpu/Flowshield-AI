# Flowshield — Technical Requirements Document (TRD) 

**Predict Early. Act Faster. Save Lives.**

*Smart India Hackathon 2026 · Problem Statement ID: 26192 · Theme: Disaster Management · Category: Software*

---

## 1. System Architecture & Standards

- **Application Pattern**: Modular Monolith.
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, GeoAlchemy2, Alembic, Pydantic v2.
- **Frontend**: React 18, TypeScript, Vite, Leaflet, React-Leaflet, Recharts, Vanilla CSS Design System.
- **Database**: PostgreSQL 16 + PostGIS 3.4 (with SQLite fallback for local developer agility).
- **Machine Learning**: XGBoost (binary:logistic), SHAP (TreeExplainer), Scikit-Learn, Pandas, NumPy.
- **Containerization**: Docker Compose (3 services: `db`, `api`, `web`).

---

## 2. API Specifications

All endpoints serve JSON and adhere to standard HTTP status codes:

- `GET /api/v1/health`: System health, database connection check, loaded model status.
- `GET /api/v1/system/status`: High-level observability status (API, DB, model version, observation count, simulation status).
- `POST /api/v1/auth/login`: Issues JWT bearer access token for authority users.
- `GET /api/v1/villages`: Returns list of 20 Himalayan settlements with current risk score, level, and alert flag.
- `GET /api/v1/villages/{id}`: Returns comprehensive telemetry, prediction, SHAP contributors, risk trend, alerts, and nearest shelter.
- `POST /api/v1/predictions`: Runs on-demand inference with local SHAP feature explanations.
- `GET /api/v1/map/geojson?layers=...`: Serves GeoJSON layers (`villages`, `risk_zones`, `rivers`, `shelters`, `routes`).
- `GET /api/v1/alerts`: Returns active, acknowledged, or resolved warning alerts.
- `POST /api/v1/alerts/{id}/acknowledge`: Updates alert status to ACKNOWLEDGED with audit user.
- `GET /api/v1/shelters/nearest?village_id=...`: Computes nearest shelters using PostGIS `ST_Distance`.
- `GET /api/v1/routes`: Evaluates route safety and flags flood-inundated river crossings.
- `POST /api/v1/simulation/start`: Initializes a simulation scenario.
- `POST /api/v1/simulation/step`: Steps the 20-substep state machine forward, generating telemetry, running ML, updating risk, alerts, shelters, and routes.
- `POST /api/v1/simulation/reset`: Reverts all simulation data and restores baseline green conditions.

---

## 3. Data Provenance & Ethics Policy

1. **Synthetic Data Disclosure**: All simulated observations must explicitly carry `is_simulated = TRUE` and `source = "Demonstration Sensor Network"`.
2. **Predictive Attribution Wording**: Feature attributions computed via SHAP must be titled **"Top Predictive Contributors"**, explicitly disclaiming physical causation.
3. **Human-in-the-Loop Governance**: All recommended actions must bear the statutory disclaimer:  
   *“Decision-support recommendation. Statutory authority remains with the District Disaster Management Officer.”*
