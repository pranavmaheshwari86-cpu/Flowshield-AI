# Flowshield — REST API Specification

All application endpoints are served under the prefix: `/api/v1`.

Interactive OpenAPI documentation is available locally at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 1. Authentication & Security Headers

Authority endpoints require a Bearer token in the `Authorization` header:
```http
Authorization: Bearer <jwt_access_token>
```
Tokens are generated via `/api/v1/auth/login` and signed using HMAC-SHA256 (`HS256`).

---

## 2. Endpoints Catalog

### 2.1 System Health & Observability

#### `GET /api/v1/health`
- **Purpose**: Liveness and readiness probe for container orchestrators and load balancers.
- **Response** (`200 OK`):
```json
{
  "status": "healthy",
  "database": "healthy",
  "model": {
    "loaded": true,
    "version": "xgb-v1.0.0-20260910-082823"
  },
  "system": "Flowshield Environmental Intelligence Core"
}
```

#### `GET /api/v1/system/status`
- **Purpose**: System telemetry metadata, observation freshness, model version, and simulation status.
- **Response** (`200 OK`):
```json
{
  "api": "online",
  "database": "online",
  "model": {
    "status": "loaded",
    "version": "xgb-v1.0.0",
    "feature_count": 12
  },
  "telemetry": {
    "villages_monitored": 20,
    "total_observations": 20,
    "latest_observation_time": "2026-09-10T08:35:00+00:00",
    "source_type": "Demonstration Telemetry Network",
    "data_provenance": "Synthetic Physics-Correlated Himalayan Basin Simulation"
  },
  "simulation": {
    "status": "RUNNING",
    "scenario": "GRADUAL_MONSOON",
    "stage": 0,
    "substep": 0
  },
  "timestamp": "2026-09-10T08:45:00+00:00"
}
```

---

### 2.2 Authority Authentication

#### `POST /api/v1/auth/login`
- **Request Body**:
```json
{
  "username": "demo",
  "password": "flowshield2026"
}
```
- **Response** (`200 OK`):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "role": "OFFICER",
  "username": "demo",
  "full_name": "District Emergency Commander"
}
```

#### `GET /api/v1/auth/me`
- **Headers**: `Authorization: Bearer <token>`
- **Response** (`200 OK`): User profile object (`id`, `username`, `role`, `full_name`).

---

### 2.3 Villages & Catchment Settlements

#### `GET /api/v1/villages`
- **Query Parameters**:
  - `basin` (optional string): Filter by basin (e.g. `Beas Basin`).
  - `risk_tier` (optional string): Filter by tier (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`, `SEVERE`).
- **Response** (`200 OK`): Array of `VillageResponse` objects:
```json
[
  {
    "id": "7b8e...",
    "name": "Pandoh",
    "tehsil": "Sadar",
    "district": "Mandi",
    "state": "Himachal Pradesh",
    "population": 2840,
    "elevation": 890.0,
    "slope": 26.5,
    "distance_to_river": 120.0,
    "historical_flood_frequency": 4,
    "vulnerability_index": 0.65,
    "latitude": 31.6724,
    "longitude": 77.0145,
    "risk_score": 18.4,
    "risk_level": "LOW",
    "trend": "STABLE",
    "has_active_alert": false,
    "latest_observation_time": "2026-09-10T08:35:00+00:00",
    "created_at": "2026-09-10T08:30:00+00:00"
  }
]
```

#### `GET /api/v1/villages/{village_id}`
- **Purpose**: Full detailed view for the Command Center slide-over drawer.
- **Response** (`200 OK`): `VillageDetailResponse` containing:
  - `current_conditions`: 1h/3h/6h/24h rain, intensity, soil moisture %, river level, surge rate, quality score.
  - `top_contributors`: Array of SHAP feature attributions (`feature_name`, `display_name`, `shap_value`, `contribution_direction`).
  - `historical_risk_trend`: Last 10 risk snapshots for Recharts plotting.
  - `active_alerts`: Active dispatches for this village.
  - `recommended_actions`: NDMA standard operating procedures.
  - `nearest_shelter`: Designated evacuation center with distance and capacity.
  - `evacuation_route`: Primary route with blockage status.

---

### 2.4 Machine Learning & Predictions

#### `POST /api/v1/predictions/predict`
- **Purpose**: On-demand XGBoost flood probability prediction with SHAP explainability.
- **Request Body**:
```json
{
  "village_id": "7b8e...",
  "rainfall_1h": 45.0,
  "rainfall_3h": 85.0,
  "rainfall_6h": 120.0,
  "rainfall_24h": 180.0,
  "rainfall_intensity": 55.0,
  "soil_moisture": 78.5,
  "river_level": 7.8,
  "river_level_change": 0.85,
  "elevation": 890.0,
  "slope": 26.5,
  "distance_to_river": 120.0,
  "historical_flood_frequency": 4,
  "quality_score": 0.95,
  "freshness_seconds": 30
}
```
- **Response** (`200 OK`):
```json
{
  "village_id": "7b8e...",
  "flood_probability": 0.784,
  "confidence_score": 0.93,
  "risk_tier": "CRITICAL",
  "top_shap_factors": [
    {
      "feature_name": "rainfall_3h",
      "display_name": "Rainfall (3h Accumulation)",
      "value": 85.0,
      "shap_value": 0.325,
      "contribution_direction": "increases_risk"
    }
  ],
  "data_quality_penalty_applied": false,
  "model_version": "xgb-v1.0.0",
  "inference_latency_ms": 11.4,
  "created_at": "2026-09-10T08:45:00+00:00"
}
```

---

### 2.5 Operational Risk Engine

#### `POST /api/v1/risk/calculate`
- **Purpose**: Computes operational composite risk score $R \in [0, 100]$ separating probability from operational urgency.
- **Request Body**: `{ "village_id": "...", "flood_probability": 0.78, "river_level_change": 0.85, "vulnerability_index": 0.65, "data_quality_score": 0.95, "freshness_seconds": 30 }`
- **Response** (`200 OK`): Composite risk score, tier, and weighted factor breakdown.

---

### 2.6 Emergency Alerts & Lifecycle

#### `GET /api/v1/alerts`
- **Query Parameters**:
  - `status` (optional string): Filter by status (`ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`).
  - `severity` (optional string): Filter by severity (`WATCH`, `ADVISORY`, `WARNING`, `CRITICAL`).
- **Response** (`200 OK`): Array of active alerts with headlines, trigger reasons, and lead times.

#### `POST /api/v1/alerts/{alert_id}/acknowledge`
- **Request Body**: `{ "acknowledged_by": "District EOC Commander" }`
- **Response** (`200 OK`): Updated alert record with `status: "ACKNOWLEDGED"` and timestamp.

---

### 2.7 Shelters & Evacuation Routing

#### `GET /api/v1/shelters`
- **Response** (`200 OK`): Array of shelters with capacity, occupancy, elevation, medical readiness, and phone numbers.

#### `GET /api/v1/shelters/nearest`
- **Query Parameters**: `village_id` (string), `limit` (int, default 3).
- **Alternative Path**: `GET /api/v1/shelters/nearest/{village_id}`
- **Response** (`200 OK`): Shelters sorted by proximity and elevation safety advantage.

#### `GET /api/v1/routes`
- **Response** (`200 OK`): Evacuation corridors with clearance status (`CLEAR`, `CAUTION`, `BLOCKED`) and blockage reasons.

#### `GET /api/v1/routes/village/{village_id}`
- **Response** (`200 OK`): Selected primary route and alternate evacuation routes.

---

### 2.8 GIS Map Layers

#### `GET /api/v1/map/geojson`
- **Query Parameters**: `layers=villages,risk_zones,rivers,shelters,routes`
#### `GET /api/v1/map/geojson/{layer_name}`
- **Supported layer names**: `villages`, `zones` / `risk_zones`, `rivers`, `shelters`, `routes`.
- **Response** (`200 OK`): GeoJSON `FeatureCollection` with feature geometries and risk properties.

---

### 2.9 Simulation State Machine

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/simulation/state` & `/status` | Fetches active stage, substep, and progress percentage. |
| `POST` | `/api/v1/simulation/start` | Starts simulation scenario from stage 0. |
| `POST` | `/api/v1/simulation/step` | Advances simulation by exactly 1 substep (0–19). |
| `POST` | `/api/v1/simulation/pause` | Pauses automated progression. |
| `POST` | `/api/v1/simulation/reset` | Resets all telemetry and alerts to baseline normal conditions. |

---

### 2.10 Real Baseline AI & Decision Support API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/ai/risk` & `/api/ai/risk` | Real-data calibrated flood risk evaluation using 15 physical features or spatial nearest interpolation. |
| `GET` | `/api/v1/ai/models` & `/api/ai/models` | Live benchmark comparison of Logistic Regression, Random Forest, and XGBoost models. |
| `GET` | `/api/v1/ai/features` & `/api/ai/features` | Metadata, physical units, and boundaries of the 15 canonical physical features. |

#### Sample Request (`POST /api/v1/ai/risk`):
```json
{
  "latitude": 31.7087,
  "longitude": 76.9320,
  "timestamp": "2023-07-09T10:00:00+05:30"
}
```

#### Sample Response (`200 OK`):
```json
{
  "risk_score": 24.7,
  "risk_level": "WATCH",
  "flood_probability": 0.0004,
  "confidence": 0.95,
  "model_version": "flowshield-xgb-real-v1-20260910",
  "model_type": "XGBClassifier (ERA5-Land validated)",
  "explanation": [
    "Elevated topsoil saturation (86.9%)",
    "Immediate river channel proximity (65 m)"
  ],
  "status": "research_prototype_public_data",
  "topographic_factor": 0.686,
  "data_provenance": {
    "source": "ECMWF Copernicus ERA5-Land Reanalysis & SRTM 30m DEM",
    "spatial_node": "Mandi Urban (Beas Main Valley)",
    "is_synthetic": false,
    "calibrated_disasters": ["Beas Mega-Disaster (July 2023)", "Mandi Cloudburst Wave (Aug 2023)"]
  }
}
```

---

### 2.11 Multi-Hazard Landslide Endpoints (`/api/v1/hazards`)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/hazards/landslide/summary` | District-wide summary of empirical slope instability trigger indices. |
| `GET` | `/api/v1/hazards/landslide/{village_id}` | Village-specific empirical landslide assessment with slope, rainfall, and statutory disclaimer. |

#### Sample Response (`GET /api/v1/hazards/landslide/summary`):
```json
{
  "total_villages_assessed": 20,
  "high_susceptibility_count": 3,
  "methodology": "Empirical Rainfall-Slope Threshold (GSI / Caine 1980)",
  "status": "PROTOTYPE_EMPIRICAL_THRESHOLD",
  "is_ml_model": false,
  "advisory_disclaimer": "This multi-hazard assessment is a heuristic research prototype and must not replace official GSI/SDMA field warnings."
}
```

---

### 2.12 Evacuation & Safe Routing Endpoints (`/api/v1/routes`)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/routes/calculate` | Dijkstra A* safe evacuation path finding with dynamic hazard penalty multipliers and off-network GPS projection. |
| `GET` | `/api/v1/routes` | Lists active evacuation corridors and road clearance status. |

#### Sample Request (`POST /api/v1/routes/calculate`):
```json
{
  "start_lat": 31.7087,
  "start_lon": 76.9320,
  "destination_shelter_id": "shelter-uuid-001"
}
```

---

### 2.13 Shelter & Capacity Endpoints (`/api/v1/shelters`)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/shelters` | Lists all 8 designated emergency relief shelters, capacity, and current occupancy. |
| `GET` | `/api/v1/shelters/nearest/{village_id}` | Finds nearest shelter with capacity and elevation clearance. |

---

### 2.14 Scenario Replay & Historical Timeline (`/api/v1/simulation/scenarios`)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/simulation/scenarios/replay` | Runs historical disaster replay sequence (e.g. July 2023 Beas event). |
| `GET` | `/api/v1/simulation/scenarios` | Lists available historical disaster replay scenarios. |

---

### 2.15 Historical & National Catalog Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/historical/floods` | Catalogs historical Himalayan cloudburst events (1995–2023). |
| `GET` | `/api/v1/national/overview` | IndoFloods basin characteristics and national comparative flood exposure. |

---

### 2.16 Predictive Risk & Multi-Horizon Timeline Endpoints (`/api/v1/risk/forecast`)

| Method | Path | Query Parameters | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/risk/forecast/detailed` | `village_id` (string, optional), `force_refresh` (bool, default `false`) | Comprehensive operational decision-support payload: observed past (-6h..0h), projected future (+1h..+48h), piecewise threshold lead times, CWC river gauge dynamics, 5km catchment exposure, and SLA provenance matrix. |
| `GET` | `/api/v1/risk/forecast/locations` | None | Returns distinct cascading location hierarchy (states, districts, villages) derived directly from live SQLite database. |

#### Sample Response (`GET /api/v1/risk/forecast/detailed?village_id=...`):
```json
{
  "location": {
    "village_id": "v-mandi-01",
    "village_name": "Pandoh",
    "district": "Mandi",
    "state": "Himachal Pradesh",
    "latitude": 31.67,
    "longitude": 77.04,
    "basin": "Beas River Basin",
    "elevation_m": 850.0
  },
  "current_situation": {
    "current_operational_risk": 32.5,
    "current_operational_tier": "WATCH",
    "observed_rainfall_rate_mm_per_hr": 14.2,
    "cwc_gauge_stage_meters": 3.91,
    "soil_saturation_percentage": 68.4,
    "trend_direction": "RISING",
    "trend_rate_per_hr": 2.4,
    "is_anomaly": false,
    "data_mode": "LIVE"
  },
  "threshold_crossings": [
    {
      "threshold_name": "WATCH",
      "threshold_value": 25.0,
      "is_crossed": true,
      "lead_time_hours": 0.0,
      "estimated_crossing_time": "2026-09-12T02:00:00Z"
    },
    {
      "threshold_name": "HIGH",
      "threshold_value": 50.0,
      "is_crossed": false,
      "lead_time_hours": 5.2,
      "estimated_crossing_time": "2026-09-12T07:12:00Z"
    }
  ],
  "timeline_series": [
    {
      "time_horizon": "NOW",
      "horizon_hours": 0,
      "operational_risk_score": 32.5,
      "risk_tier": "WATCH",
      "p_risk_ge_25": 0.85,
      "p_risk_ge_50": 0.28,
      "p_risk_ge_75": 0.05,
      "risk_p10": 26.0,
      "risk_p50": 32.5,
      "risk_p90": 41.0,
      "rainfall_mm_per_hr": 14.2,
      "river_stage_meters": 3.91,
      "soil_saturation_pct": 68.4,
      "is_observed": true
    }
  ],
  "hydrology": {
    "river_name": "Beas River",
    "gauge_station_name": "Pandoh Dam Outflow CWC Gauge",
    "current_stage_meters": 3.91,
    "warning_mark_meters": 5.5,
    "danger_mark_meters": 6.5,
    "margin_to_danger_meters": -2.59,
    "rate_of_rise_m_per_hr": 0.15,
    "hydraulic_trend": "RISING",
    "upstream_dam_discharge_cumec": 1240.0
  },
  "exposure": {
    "census_population": 4820,
    "vulnerable_population_pct": 28.5,
    "schools_within_5km": 6,
    "hospitals_within_5km": 1,
    "bridges_within_5km": 2,
    "active_evacuation_routes": 2,
    "nearest_shelter_name": "Pandoh Higher Secondary School Relief Center",
    "nearest_shelter_distance_km": 1.4,
    "nearest_shelter_elevation_advantage_m": 22.0
  },
  "data_quality_matrix": [
    {
      "source_name": "IMD Synoptic Automated Weather Station",
      "source_type": "AUTOMATED_WEATHER_STATION",
      "update_frequency_minutes": 15,
      "latency_seconds": 45,
      "is_stale": false,
      "staleness_threshold_minutes": 60,
      "quality_grade": "NOMINAL"
    }
  ]
}
```

---

## 3. Standard Error Responses

Errors follow RFC 7807 problem details convention:
```json
{
  "detail": "Village not found for ID: 7b8e..."
}
```
- `400 Bad Request`: Validation failure or out-of-bounds parameter.
- `401 Unauthorized`: Missing or invalid JWT Bearer token.
- `404 Not Found`: Requested resource (village, shelter, alert) does not exist.
- `422 Unprocessable Entity`: Schema validation failure (Pydantic).
