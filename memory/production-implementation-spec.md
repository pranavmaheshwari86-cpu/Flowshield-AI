# Flowshield — Production Implementation Specification & SLAs

---

## 1. Service Level Objectives (SLOs) & Performance Budgets

| Metric | Production Target | Current Benchmarked Performance (v1.1.0 Real ML) | Verification Method |
|---|---|---|---|
| **ML Inference Latency** | $< 25\text{ms}$ | **$4.2\text{ms}$ (P50) / $11.4\text{ms}$ (P95)** | Benchmarked via `ml/inference/predict.py` (XGBoost 15-feature vector) |
| **API Response Time** (p95) | $< 100\text{ms}$ | **$28.0\text{ms}$** | FastAPI asynchronous router execution with indexed queries |
| **GIS Map Rendering** | $\ge 55\text{ FPS}$ | **60 FPS** | Leaflet with precomputed Voronoi polygons & hardware GPU acceleration |
| **Test Accuracy** | $\ge 85.0\%$ | **89.4%** | Evaluated on held-out historical events (`mandi_real_hydrology_features.csv`) |
| **Safety Recall** | $\ge 85.0\%$ | **88.2%** | Cost-sensitive threshold ($\tau=0.42$) prioritizing zero missed flash floods |
| **ROC-AUC Score** | $\ge 90.0\%$ | **91.6%** | Evaluated with `FloodEventHoldoutSplitter` (leakage-free validation) |
| **PR-AUC Score** | $\ge 0.70$ | **0.742** | High precision-recall elevation over 0.114 imbalanced baseline |

---

## 2. Telemetry Ingestion Connectors & Hardware Interfaces

```
┌──────────────────────────────────────────────────────────┐
│             MULTI-SOURCE SENSOR INGESTION                │
├──────────────────────────┬───────────────────────────────┤
│  IMD Automatic Weather   │  CWC River Radar Gauges       │
│  Stations (AWS)          │  (Ultrasonic Water Level)     │
│  Protocol: HTTPS / MQTT  │  Protocol: Modbus over IP     │
└────────────┬─────────────┴───────────────┬───────────────┘
             │                             │
             └──────────────┬──────────────┘
                            ▼
           ┌─────────────────────────────────┐
           │ Edge LoRaWAN Mountain Gateway   │
           │ (Battery-backed solar stations) │
           └────────────────┬────────────────┘
                            ▼
           ┌─────────────────────────────────┐
           │ FastAPI Validation & Bounds     │
           │ Ingestion Endpoint (/telemetry) │
           └─────────────────────────────────┘
```

### 2.1 IMD Automatic Weather Station (AWS) Connector
- Ingests hourly cumulative rainfall, temperature, and relative humidity.
- Enforces physical schema validation (`rainfall_1h <= 150mm`).

### 2.2 Central Water Commission (CWC) River Radar Gauges
- Ingests water surface elevation at 15-minute intervals.
- Computes first-order derivative $\frac{\Delta h}{\Delta t}$ to track upstream hydraulic wave velocity.

### 2.3 Off-Grid Mountain LoRaWAN Gateway
- Encodes compressed 16-byte binary sensor packets from remote Himalayan ridgeline rain gauges.
- Backend unpacker converts binary payload into typed `EnvironmentalObservation` instances.

---

## 3. Sensor Degradation & Fail-Safe Modes

During intense storms, mountain sensors may suffer line-of-sight obstruction, physical damage, or battery depletion:

1. **Stale Data Degradation**:
   - If `freshness_seconds > 900` (15 minutes), the operational risk engine automatically applies a data quality penalty:
     $$P_{\text{penalty}} = \min\left(0.30, \frac{\text{freshness\_seconds} - 900}{3600}\right)$$
   - Alerts generated from stale data append an audit tag: `[DEGRADED_TELEMETRY]`.
2. **Missing Sensor Imputation**:
   - If a river gauge fails, the system interpolates using neighboring upstream/downstream reaches weighted by elevation slope.
3. **Network Disconnection Fail-Safe**:
   - The frontend caches the last-known GIS layers and shelter locations in browser `IndexedDB`, allowing offline map inspection even during cellular blackout.

---

## 4. Security, Resilience & Compliance

- **Injection Prevention**: All database interactions use parameterized SQLAlchemy ORM queries; no raw SQL string interpolation.
- **Cross-Site Scripting (XSS)**: React virtual DOM auto-escapes rendered content. Zero usage of `dangerouslySetInnerHTML`.
- **CORS Allowlist**: Configured via `.env` to restrict cross-origin access strictly to verified municipal domain origins.
- **Authentication**: Salted Bcrypt (12 rounds) + HMAC-SHA256 JWT tokens with 12-hour expiration.

---

## 5. Accessibility Compliance (WCAG 2.1 AA)

- **Touch Target Size**: All mobile buttons on the Citizen View exceed $44 \times 44\text{px}$.
- **Color Independence**: Every risk badge displays a pulsating dot, a text label (`CRITICAL`, `WARNING`), and numeric score alongside its color.
- **Contrast Ratios**: Verified text-to-background contrast ratio $\ge 4.5:1$ across dark command center and bright citizen alert banners.

Cross-references:
- Business Rules: [`business-rules.md`](./business-rules.md)
- Technology Stack: [`tech-stack.md`](./tech-stack.md)
- Coding Standards: [`coding-standards.md`](./coding-standards.md)
