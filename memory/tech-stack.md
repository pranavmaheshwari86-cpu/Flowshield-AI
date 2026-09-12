# Flowshield — Technology Stack & Dependencies

---

## 1. Runtime Environments & Languages

| Technology | Version | Purpose |
|---|---|---|
| **Python** | `3.10.11` / `3.12.x` (Host: Windows 11 / Linux Alpine in Docker) | Application backend, ML pipeline, simulation state machine |
| **Node.js** | `v24.16.0` (npm `11.3.0`) | Frontend development tooling, TypeScript compilation, Vite bundling |
| **TypeScript** | `^5.5.3` | Strict type contracts, interfaces, and compile-time verification |

---

## 2. Backend Frameworks & Libraries (`apps/api`, `ml/`)

| Package | Version | Purpose |
|---|---|---|
| **FastAPI** | `^0.115.0` | Asynchronous high-performance REST API framework |
| **Uvicorn** | `^0.30.0` | ASGI web server implementation |
| **SQLAlchemy** | `^2.0.32` | Declarative ORM, relation management, connection pooling |
| **Alembic** | `^1.13.2` | Database schema migrations |
| **Pydantic** | `^2.8.2` | Runtime data validation, bounds checking, serialization |
| **Pydantic-Settings** | `^2.4.0` | Environment variable parsing with field validators |
| **XGBoost** | `^2.1.0` / `3.4.1` | Extreme Gradient Boosting classifier with `scale_pos_weight` |
| **SHAP** | `^0.46.0` | TreeExplainer for local feature contribution attributions |
| **Scikit-Learn** | `^1.5.1` / `1.9.0` | Feature scaling (`StandardScaler`), train/test split, metrics |
| **NumPy** | `^2.0.0` | Vector operations, PRNG simulation seeding, clipping |
| **Pandas** | `^2.2.2` | Telemetry dataset manipulation and CSV serialization |
| **SciPy** | `^1.14.0` | Voronoi tessellation spatial partitioning for catchment boundaries |
| **Requests** | `^2.32.0` | Open-Meteo ERA5 historical climate API connector |
| **Joblib** | `^1.4.2` | Serialized feature scalers and pipeline persistence |
| **PyJWT** | `^2.9.0` | JSON Web Token encoding and decoding for authority session auth |
| **Bcrypt** | `^4.2.0` | Password hashing for emergency responder credentials |
| **GeoAlchemy2** | `^0.15.2` | PostGIS spatial geometry mapping (Geometry columns) |
| **Pytest** | `^9.1.1` | Automated test suite execution |

---

## 3. Frontend Frameworks & Libraries (`apps/web`)

| Package | Version | Purpose |
|---|---|---|
| **React** | `^18.3.1` | UI component library and virtual DOM rendering |
| **React-DOM** | `^18.3.1` | DOM renderer for React |
| **React Router DOM** | `^6.26.0` | Client-side routing (`/`, `/dashboard`, `/citizen`, `/about`, `/login`) |
| **Vite** | `^5.4.1` | Fast frontend build tool, HMR server, and production bundler |
| **Leaflet** | `^1.9.4` | Interactive mobile-friendly GIS mapping library |
| **React-Leaflet** | `^4.2.1` | React bindings for Leaflet map elements |
| **Recharts** | `^2.12.7` | Composable charting library for risk score and river level trendlines |
| **Lucide-React** | `^0.438.0` | Clean, modern feather icon set for dashboard indicators |

---

## 4. Database & Storage Infrastructure

| Technology | Version | Deployment Context | Purpose |
|---|---|---|---|
| **PostgreSQL + PostGIS** | `16-3.4-alpine` | Containerized (`docker-compose.yml`) | Enterprise GIS database with spatial indexing and `ST_Distance` functions |
| **SQLite** | `3.x` | Local Developer Fallback (`flowshield.db`) | Zero-configuration local database with Haversine distance fallback |
| **Joblib** | `^1.4.2` | Local Disk (`ml/models/`) | Compressed serialization for trained model and metadata |

---

## 5. UI/UX & Design System Stack

- **Styling Paradigm**: Vanilla CSS with comprehensive custom CSS Variables (`tokens.css`).
- **Typography**: `Inter` (sans-serif UI) & `JetBrains Mono` (telemetry, coordinates, and metrics) imported via Google Fonts.
- **Color Palette**: Dark Command Center palette:
  - Base: `#060d17` (canvas), `#0a1628` (primary background), `#0f213e` (cards), `#1e355b` (borders).
  - Risk Tiers: `#10b981` (Low), `#f59e0b` (Moderate), `#f97316` (High), `#ef4444` (Critical), `#b91c1c` (Severe).
  - GIS Accents: `#38bdf8` (river reaches), `#06b6d4` (telemetry gauges), `#8b5cf6` (SHAP bars).
- **Responsiveness**: Fluid layout responsive down to 320px for Citizen Emergency Mode.

Cross-references:
- Architecture Details: [`architecture.md`](./architecture.md)
- Coding Standards: [`coding-standards.md`](./coding-standards.md)
- Local Run Commands: [`how-to-run.md`](./how-to-run.md)
