# Flowshield — Domain Business Rules & Operational Constraints

---

## 1. Physical Hydrology Bounds & Canonical Features (15 Features)

All environmental telemetry ingested into the ML pipeline or received from field sensors must satisfy strict physical validity bounds. Out-of-bounds readings trigger validation rejection or automated capping:

| Feature Name | Unit | Valid Range | Physical Description & Mountain Relevance | Provenance Category |
|---|---|---|---|---|
| `precip_1h_mm` | mm | $0.0 - 150.0$ | Short-term precipitation burst indicating localized cloudburst activity. | Observed (ERA5 / Rain Gauge) |
| `precip_3h_mm` | mm | $0.0 - 300.0$ | Cumulative rainfall over sub-catchment runoff concentration times. | Observed (Accumulation) |
| `precip_6h_mm` | mm | $0.0 - 450.0$ | Extended mountain precipitation accumulating in tributary ravines. | Observed (Accumulation) |
| `precip_12h_mm` | mm | $0.0 - 550.0$ | Half-day heavy orographic rainfall. | Observed (Accumulation) |
| `precip_24h_mm` | mm | $0.0 - 700.0$ | Antecedent daily rainfall saturating deeper soil layers. | Observed (Accumulation) |
| `precip_48h_mm` | mm | $0.0 - 900.0$ | Two-day storm event accumulation. | Observed (Accumulation) |
| `precip_72h_mm` | mm | $0.0 - 1200.0$ | Multi-day monsoon depression accumulation. | Observed (Accumulation) |
| `soil_moisture_0_to_7cm` | $\text{m}^3/\text{m}^3$ | $0.0 - 0.70$ | Volumetric surface soil moisture. High values eliminate infiltration. | Observed (ERA5 / Soil Sensor) |
| `soil_moisture_7_to_28cm` | $\text{m}^3/\text{m}^3$ | $0.0 - 0.70$ | Intermediate root-zone soil saturation. | Observed (ERA5) |
| `soil_moisture_28_to_100cm` | $\text{m}^3/\text{m}^3$ | $0.0 - 0.70$ | Deep sub-surface soil moisture reservoir. | Observed (ERA5) |
| `soil_saturation_proxy` | index | $0.0 - 1.0$ | Normalized composite of multi-layer soil saturation. | Derived (Hydrologic Formula) |
| `antecedent_precipitation_index_api` | mm | $0.0 - 250.0$ | $API_t = P_t + k \cdot API_{t-1}$ ($k=0.85$), decaying runoff potential. | Derived (Decay Constant) |
| `slope_degrees` | degrees | $0.0 - 75.0$ | Hillside gradient from DEM. Steeper slopes accelerate flood wave arrival. | Static Catchment GIS |
| `elevation_m` | meters | $300 - 4,500$ | Station/village altitude affecting orographic enhancement. | Static Catchment GIS |
| `upstream_catchment_area_km2`| $\text{km}^2$ | $1.0 - 50,000$| Contributing hydrologic drainage area above gauge reach. | Static Catchment GIS |

### 1.1 Data Provenance Categorization Constraints
In strict accordance with SIH 2026 data integrity guidelines:
- **`observed`**: Direct instrument readings from rain gauges, river radar gauges, or ERA5 reanalysis grid cells.
- **`derived`**: Scientifically validated calculations (e.g., API decay formula, spatial Voronoi weightings).
- **`heuristic`**: Rule-based estimations used only when telemetry is partially occluded.
- **`unavailable`**: Explicitly flagged when telemetry is down; **never** backfilled with fabricated values.

### 1.2 Decision Threshold Calibration
The XGBoost flood classification model employs a cost-sensitive decision threshold of **$\tau = 0.42$** (rather than default 0.50) to optimize the balance between high recall ($>85\%$) on life-threatening flash floods and low false alarms ($<15\%$).

---

## 2. Decoupling ML Probability from Operational Risk

In disaster operations, **Statistical Flood Probability ($P_{\text{ML}}$)** and **Operational Risk Score ($R$)** must never be conflated:
- **$P_{\text{ML}} \in [0, 1]$**: Pure statistical likelihood emitted by the XGBoost classifier based on physical features.
- **$R \in [0, 100]$**: Composite decision index that incorporates real-time hydrological surge velocity, human exposure vulnerability, and sensor degradation penalties.

### Mathematical Formulation:
$$R = \left( 0.40 \cdot P_{\text{ML}} + 0.25 \cdot T_{\text{surge}} + 0.25 \cdot V_{\text{vuln}} - 0.10 \cdot P_{\text{penalty}} \right) \times 100$$

Where:
1. **$P_{\text{ML}}$ (40% Weight)**: XGBoost model inference output.
2. **$T_{\text{surge}}$ (25% Weight)**: River rise velocity normalized to peak surge capacity:
   $$T_{\text{surge}} = \min\left(1.0, \max\left(0.0, \frac{\text{river\_level\_change}}{1.2}\right)\right)$$
3. **$V_{\text{vuln}}$ (25% Weight)**: Settlement vulnerability factor based on elderly population ratio and distance to river.
4. **$P_{\text{penalty}}$ (10% Weight)**: Sensor confidence reduction applied when data is stale or flagged:
   $$P_{\text{penalty}} = 1.0 - \text{quality\_score}$$

---

## 3. Operational Risk Tiers & Action Triggers

| Risk Score ($R$) | Tier Name | System Action & Advisory Protocol |
|---|---|---|
| **$0.0 - 24.9$** | **LOW** | Routine automated monitoring. Normal green advisory on citizen portal. |
| **$25.0 - 49.9$** | **MODERATE** | **Watch Stage**: Field personnel alerted. Automatic telemetry sampling frequency doubles. |
| **$50.0 - 74.9$** | **HIGH** | **Warning Stage**: Relief shelters placed on standby. Orange banner displayed to citizens. Precautionary riverbank clearing advisory. |
| **$75.0 - 89.9$** | **CRITICAL** | **Evacuation Stage**: Red banner triggered. Village sirens activated. SDRF Quick Response Teams deployed. Nearest safe shelters opened. |
| **$90.0 - 100.0$** | **SEVERE** | **Catastrophic Inundation**: Immediate mandatory valley-wide evacuation. Low-lying bridge routes closed. |

---

## 4. Alert Deduplication & Lifecycle State Machine

To prevent alert fatigue and operator confusion during active storm events:
1. **Deduplication Token**: Alerts are keyed by `village_id:severity:stage`. If an active alert already exists for settlement $X$ at severity $S$ during stage $K$, redundant dispatches are suppressed.
2. **State Lifecycle**:
   - `ACTIVE`: Newly triggered alert requiring field operator attention.
   - `ACKNOWLEDGED`: Incident Commander has reviewed and acknowledged dispatch.
   - `RESOLVED`: Hydrological telemetry has fallen back below threshold for 2 consecutive observation cycles.

---

## 5. Shelter Allocation & Elevation Constraints

- **Elevation Safety Rule**: A shelter is only designated safe if its ground elevation is at least **$+25$ meters higher** than the adjacent river reach danger level.
- **Intake Capacity Rule**: When `current_occupancy >= total_capacity`, shelter service routes subsequent evacuees to the next closest safe shelter.
- **Proximity Sorting**: Nearest shelters are ranked using great-circle distance ($ST\_Distance$ in PostGIS, Haversine in SQLite).

---

## 6. Dynamic Evacuation Route Clearance

- **River Crossing Rule**: If any river reach reaches or exceeds its **Danger Level** (e.g., Beas main reach $\ge 8.5$ meters), all evacuation routes with `is_river_crossing = True` along that reach are dynamically updated to:
  - `status = "BLOCKED"`
  - `blockage_reason = "Submerged causeway / river stage exceeds 8.5m danger mark"`
- **Routing Engine Guidance**: Command Center and Citizen portals immediately redirect evacuees to alternate high-ridge corridors.

---

## 7. Human-in-the-Loop Governance & Legal Disclaimers

- Automated SOP dispatches (e.g., siren activation, SDRF mobilization) are decision-support recommendations and require explicit human confirmation by a certified Incident Commander.
- All citizen warnings and dashboards prominently display the non-forecast statutory disclosure: *“Flowshield is an operational decision support aid and does not supersede official advisories from the India Meteorological Department (IMD) or Central Water Commission (CWC).”*

---

## 8. Continuous Piecewise Linear Interpolation Solver for Lead-Time to Action

- **Problem Formulation**: Coarse discrete forecast horizons (+1h, +3h, +6h, +12h, etc.) fail to provide the exact hour of impending danger threshold breach.
- **Continuous Mathematical Solution**: Across adjacent forecast horizon points $(t_i, R(t_i))$ and $(t_{i+1}, R(t_{i+1}))$, the exact crossing time $t^*$ for threshold $V_{\text{target}} \in \{25 \text{ (WATCH)}, 50 \text{ (HIGH)}, 75 \text{ (CRITICAL)}\}$ is solved via continuous linear interpolation:
  $$t^* = t_i + \frac{V_{\text{target}} - R(t_i)}{R(t_{i+1}) - R(t_i)} \cdot (t_{i+1} - t_i)$$
- **Operational Precision**: Evaluates exact fractional lead times (e.g. `Lead time: 5.2h until HIGH risk threshold breach`), giving incident commanders precise tactical evacuation windows.

---

## 9. Calibrated Multi-Horizon Forecasting & Exceedance Probabilities

- **Horizon Points**: Projections are generated across 6 distinct tactical planning horizons: `+1h`, `+3h`, `+6h`, `+12h`, `+24h`, and `+48h`.
- **Probability Calibration**: Raw ML classifier outputs are calibrated using Platt scaling and Isotonic regression to produce mathematically sound exceedance probabilities:
  - $P(\text{Risk} \ge 25)$: Probability of reaching WATCH tier.
  - $P(\text{Risk} \ge 50)$: Probability of reaching HIGH danger tier.
  - $P(\text{Risk} \ge 75)$: Probability of reaching CRITICAL emergency tier.
- **Ensemble Quantiles**: Each horizon point computes P10 (10th percentile conservative lower bound), P50 (median operational estimate), and P90 (90th percentile worst-case surge envelope).

---

## 10. Strict "No Fake Data" Rule for Timeline Decision Support

- **Zero Synthetic Telemetry**: In `DATA_MODE=live`, the Timeline interface in `/dashboard` must never render hardcoded or synthetic demonstration numbers (such as static `47.74 Lakh` affected population, `42 Districts`, `7/9 Rivers`, `4,120+ Schools`, or arbitrary static scores).
- **Authoritative Provenance**: Every metric, time-series point, CWC river gauge stage, infrastructure count, and trend vector must originate from:
  1. Live SQLite database tables (`villages`, `observations`, `rivers`, `shelters`, `routes`).
  2. Calibrated ML model inference pipelines (`ml/inference/predict.py`).
  3. Real CWC telemetric gauge stations.
  4. Numerical weather prediction models (ECMWF IFS 0.1° / IMD Synoptic AWS).
- **Failure Transparency**: If telemetry from a station is unavailable or degraded, the system must render an explicit `DEGRADED` or `UNGAUGED BASIN` indicator rather than backfilling fake numbers.

Cross-references:
- Architecture: [`architecture.md`](./architecture.md)
- Walkthrough: [`../walkthrough.md`](../walkthrough.md)
- API Endpoints: [`api.md`](./api.md)
- Government IDs & Credentials: [`module-government-ids.md`](./module-government-ids.md)
