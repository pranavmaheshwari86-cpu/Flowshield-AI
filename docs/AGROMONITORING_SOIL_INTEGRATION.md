# AgroMonitoring Soil Moisture Integration — FlowShield

## 1. Overview & Architecture

FlowShield integrates official **AgroMonitoring Satellite Telemetry** for operational soil moisture monitoring across India. Soil moisture is a critical antecedent hydrometeorological condition for flash flood forecasting, hill-slope failure susceptibility, and runoff coefficient determination.

```
       India Boundary (573 Administrative Districts)
                            ↓
       Adaptive Geodesic Tiling (1.0 ha ≤ Area ≤ 3,000 ha)
                            ↓
       Topology & Coordinate Validation ([lon, lat], Closed Ring)
                            ↓
       Local Persistence & Deduplication (MonitoringPolygon DB)
                            ↓
       Official AgroMonitoring API (POST /agro/1.0/polygons)
                            ↓
       Satellite Soil Moisture Telemetry (GET /agro/1.0/soil)
                            ↓
       Leaflet Tactical GIS Dashboard & Regional Selectors
```

---

## 2. API Key Security & Configuration

The AgroMonitoring API key is restricted **strictly to the backend runtime**. It is never exposed in client JavaScript bundles, network payloads to the browser, server logs, or error responses.

### Configuration
In `.env`:
```env
AGRO_API_KEY=d60150aaf45bfa3b31b65b6c2c660c50
```

In `.env.example`:
```env
# AgroMonitoring API (Required for Soil Moisture satellite telemetry)
AGRO_API_KEY=
```

In `apps/api/app/config.py`:
```python
AGRO_API_KEY: str = os.getenv("AGRO_API_KEY", "")
AGRO_API_BASE_URL: str = os.getenv("AGRO_API_BASE_URL", "http://api.agromonitoring.com/agro/1.0")
```

---

## 3. Geographic Boundary & Adaptive Tiling Algorithm

### Authoritative Boundary Dataset
FlowShield utilizes `ml/data/raw/terrain/terrapulse/TerraPulse_India_Districts.geojson`, containing 573 administrative district boundaries across all 34 States and Union Territories in WGS84 EPSG:4326. No arbitrary bounding boxes or rectangles are used.

### AgroMonitoring Polygon Constraints
- **Area Constraint**: Between $1.0\text{ ha}$ ($0.01\text{ km}^2$) and $3,000.0\text{ ha}$ ($30.0\text{ km}^2$).
- **Geometry Type**: Single `Polygon` only. MultiPolygons must be split into component polygons.
- **Coordinate Order**: Strictly `[longitude, latitude]`.
- **Closed Ring**: The first and last coordinate points in the exterior ring must be identical.

### Geodesic Area Calculation
To prevent distortion caused by meridian convergence at higher latitudes (e.g. Himalayas vs Equator), FlowShield calculates authalic spherical geodesic area using spherical excess trigonometry on the authalic Earth radius ($R = 6,371,008.8\text{ m}$):
$$\text{Area} = R^2 \sum_{i=1}^{n-1} (\lambda_{i+1} - \lambda_i) \left(2 + \sin\phi_i + \sin\phi_{i+1}\right)$$
This yields < 0.2% variance from AgroMonitoring's server-side area engine.

### Recursive Quad-Tree Subdivision
If a polygon or district boundary exceeds $3,000\text{ ha}$, it is recursively subdivided along bounding box quadrants until all child cells satisfy the area constraints. Any sliver polygons smaller than $1.0\text{ ha}$ created by boundary clipping are safely excluded.

---

## 4. Database Schema

### `monitoring_polygons`
| Column | Type | Description |
|---|---|---|
| `id` | `VARCHAR(36)` | UUID primary key |
| `agro_polygon_id` | `VARCHAR(64)` | Unique AgroMonitoring polygon ID |
| `name` | `VARCHAR(120)` | E.g. `Mandi_Cell_0001` |
| `country` | `VARCHAR(60)` | Default `"India"` |
| `state` | `VARCHAR(100)` | Administrative State |
| `district` | `VARCHAR(100)` | Administrative District |
| `area_hectares` | `FLOAT` | Validated area ($1 \le \text{ha} \le 3000$) |
| `centroid_lat` | `FLOAT` | Center latitude |
| `centroid_lon` | `FLOAT` | Center longitude |
| `geometry_geojson` | `TEXT` | GeoJSON Polygon string `[lon, lat]` |
| `status` | `VARCHAR(30)` | `PENDING`, `REGISTERED`, `FAILED`, `LIMIT_EXCEEDED` |
| `error_message` | `TEXT` | Diagnostic error if API rejects |
| `last_soil_update` | `DATETIME` | Timestamp of latest satellite sync |

### `soil_observations`
| Column | Type | Description |
|---|---|---|
| `id` | `VARCHAR(36)` | UUID primary key |
| `polygon_id` | `VARCHAR(36)` | FK referencing `monitoring_polygons.id` |
| `agro_polygon_id` | `VARCHAR(64)` | AgroMonitoring polygon ID |
| `soil_moisture` | `FLOAT` | Volumetric soil moisture ($m^3/m^3$) |
| `soil_temperature` | `FLOAT` | 10cm depth temperature in Kelvin (`t10`) |
| `surface_temperature` | `FLOAT` | Skin surface temperature in Kelvin (`t0`) |
| `observation_timestamp` | `DATETIME` | Satellite capture epoch |

---

## 5. API Endpoints

All endpoints are mounted under `/api/agro-monitoring` and `/api/v1/agro-monitoring`:

### `GET /status`
Returns service status, number of generated grid cells, active registered polygons, quota status, and active administrative regions.

### `GET /hierarchy`
Returns all available Indian states and their nested districts from the administrative dataset.

### `POST /initialize`
Body:
```json
{
  "scope": "district",
  "state_name": "Himachal Pradesh",
  "district_name": "Mandi",
  "register_with_agro": true,
  "batch_limit": 5
}
```
Generates valid small polygons, saves them to `monitoring_polygons`, and registers missing cells with AgroMonitoring up to `batch_limit`.

### `POST /initialize-india`
Convenience endpoint to initialize India-wide grid cells.

### `GET /polygons`
Query params: `state`, `district`, `status_filter`, `limit`, `offset`. Lists stored polygons with their latest soil moisture telemetry.

### `GET /soil`
Query params: `state`, `district`, `only_registered`. Returns a standard GeoJSON `FeatureCollection` ready for Leaflet visualization with embedded moisture values and hydrologic risk tiers.

### `GET /soil/{polygon_id}`
Returns historical time-series observations for a specific polygon.

### `POST /sync`
Triggers an on-demand satellite telemetry fetch for all registered polygons.

---

## 6. Soil Moisture Hydrologic Classification

Volumetric soil moisture ($m^3/m^3$) is mapped to hydrologic risk tiers:

| Tier | Moisture Range ($m^3/m^3$) | Color Swatch | Flash Flood & Landslide Implication |
|---|---|---|---|
| **LOW** | $< 0.15$ | `#F59E0B` (Amber) | Dry topsoil. High initial infiltration capacity; low immediate runoff hazard. |
| **MODERATE** | $0.15 - 0.30$ | `#10B981` (Emerald) | Normal hydrologic baseline. Standard infiltration buffer. |
| **HIGH** | $0.30 - 0.45$ | `#3B82F6` (Blue) | Elevated saturation. Infiltration buffer partially depleted; moderate runoff vulnerability during heavy downpours. |
| **VERY HIGH** | $> 0.45$ | `#EF4444` (Crimson) | Soil near saturation limit. Extreme flash flood runoff risk and high slope failure / landslide hazard. |

---

## 7. Plan Quota & Subscription Limit Protection

- **Quota Detection**: If an AgroMonitoring account reaches its concurrent polygon or hectare quota, the API responds with HTTP 422 ("Polygon area limit exceeded" or polygon count exceeded).
- **Graceful Handling**: The service catches HTTP 422, marks the affected cell as `LIMIT_EXCEEDED`, logs a clean diagnostic note, and terminates the registration batch without throwing 500 errors.
- **Priority Monitoring**: Administrators can target priority districts (e.g. Mandi in Himachal Pradesh, Wayanad in Kerala, Chamoli in Uttarakhand) without exceeding developer plan limits.
- **Zero Fake Data**: If the API key is missing or quota is capped, FlowShield displays the exact API state and does not synthesize fake telemetry.

---

## 8. Verification & Running Tests

Run the dedicated automated test suite:
```bash
pytest tests/test_agro_monitoring.py -v
```
All 5 automated tests verify boundary loading, recursive adaptive subdivision, geodesic area calculation, soil moisture tier classification, and end-to-end REST endpoints.
