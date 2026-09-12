# Flowshield — Training Data & Target Legitimacy Audit

**Audit Date**: September 2026  
**Project**: Flowshield (SIH 2026, PS ID: 26192)  
**Location Focus**: Beas River Basin, Mandi District, Himachal Pradesh  
**Core Constraint**: Zero synthetic/fabricated data. Only verified public datasets and scientifically defensible targets.

---

## 1. Inventory of Inspected Public Datasets

We audited all files in `data/real/` collected from verified public scientific repositories:

| Dataset File | Source / Origin | Sample Count / Resolution | Primary Attributes |
|---|---|---|---|
| `mandi_era5_hourly_raw.csv` | ECMWF Copernicus Climate Change Service (ERA5-Land via Open-Meteo) | 15,624 hourly observations across 7 Mandi hydrological nodes (July–Aug 2023, July 2022) | Precipitation, rain, soil moisture ($0-7\text{cm}, 7-28\text{cm}$), temperature, humidity, surface pressure, wind speed |
| `mandi_real_hydrology_features.csv` | Engineered physical hydrology dataset | 15,624 rows $\times$ 30 columns | Antecedent rolling rainfall ($1\text{h}, 3\text{h}, 6\text{h}, 24\text{h}, 72\text{h}$), topsoil and deep soil saturation %, slope, elevation, river distance, drainage area, flood occurrence |
| `indofloods/floodevents_indofloods.csv` | IIT Gandhinagar & National Hydrology Project (Zenodo DOI: `10.5281/zenodo.14584654`, BAMS 2025) | 4,548 historical flood events across 155 Indian gauge basins (1967–2023) | Peak flood level ($m$), peak discharge ($m^3/s$), flood volume, event duration, time to peak, recession time |
| `indofloods/catchment_characteristics_indofloods.csv` | IIT Gandhinagar INDOFLOODS | 155 catchments $\times$ 108 characteristics | Drainage area, stream order, sinuosity index, relief ratio, elongation ratio, circularity |
| `indofloods/metadata_indofloods.csv` | Central Water Commission (CWC) | 220 gauge stations | Gauge ID, warning level, danger level, coordinates, river basin, privacy status (`Open` vs `Restricted`) |
| `beas_basin_historical_floods.csv` | HiFlo-DAT (Bath Spa Univ / Natural Hazards 2021) & HPSDMA Disaster Bulletins | 7 major disaster events (1995–2023) | Event start/end, location, flood type, peak discharge, casualties, bridges damaged, key landmarks inundated |

---

## 2. Feature vs. Target Legitimacy Audit

### 2.1 Legitimate Features (Approved for ML Input)
Features must represent physical antecedent conditions available at the moment of prediction without future leakage:
1. **Antecedent Rainfall Accumulation**:
   - `rainfall_1h_mm`: Immediate rainfall intensity.
   - `rainfall_3h_mm`: Short-term convective accumulation (flash flood / cloudburst trigger).
   - `rainfall_6h_mm`: Intermediate basin saturation accumulation.
   - `rainfall_24h_mm`: Daily antecedent precipitation index.
   - `rainfall_72h_mm`: Macro antecedent moisture loading.
2. **Soil Moisture Saturation**:
   - `soil_saturation_pct`: Topsoil layer ($0-7\text{cm}$) saturation ratio relative to field capacity ($0.45 \, m^3/m^3$).
   - `deep_soil_saturation_pct`: Subsurface layer ($7-28\text{cm}$) saturation ratio.
3. **Atmospheric Forcing Variables**:
   - `temperature_c`: 2m air temperature (affects evaporation and convective lapse rate).
   - `relative_humidity_pct`: Atmospheric vapor saturation.
   - `surface_pressure_hpa`: Barometric depression indicator.
   - `wind_speed_kmh`: Surface atmospheric circulation velocity.
4. **Static Geomorphology & Topography (SRTM 30m / DEM)**:
   - `elevation_m`: Absolute altitude above MSL.
   - `catchment_slope_deg`: Terrain incline (controls surface runoff velocity vs infiltration).
   - `dist_to_river_m`: Euclidean distance to main river reach.
   - `upstream_drainage_sqkm`: Upstream catchment drainage area contributing flow.

### 2.2 Features Excluded Due to Leakage or Unavailability
- **River Stage Height & Discharge**: Excluded as general input features because CWC sub-hourly telemetry is restricted by the Government of India across northern transboundary basins. Relying on them as mandatory inputs would cause inference failure in real operations.
- **Future Rolling Precipitation**: Any metric computed using $t+k$ ($k > 0$) is strictly prohibited.
- **Post-Disaster Impact Indicators**: Casualties, infrastructure loss, road closures, and shelter occupancies occur during/after the event and cannot be used for predictive modeling.

---

## 3. Target Classification Matrix (Strict Non-Fabrication)

In accordance with Step 2, every potential target in the system is explicitly categorized:

| Target Variable | Classification | Legitimacy for Supervised ML | Rationale & Evidence |
|---|---|---|---|
| `flood_occurred` (0 / 1) | **Derived from Authoritative Observations** | **APPROVED for Model A** | Mapped directly to verified disaster timelines published in official Himachal Pradesh State Disaster Management Authority (HPSDMA) and Central Water Commission (CWC) post-disaster flood bulletins for Mandi District (July 8–11, 2023 and August 13–15, 2023). Negative hours represent verified non-flood periods (July 2022 baseline control). |
| `continuous_river_stage_m` | **Unavailable in Public Domain** | **NOT APPROVED** | Central Water Commission classifies sub-hourly river stage sensor telemetry for the Beas Basin as "Restricted". Fabricating continuous river stages would violate scientific integrity. |
| `alert_tier` (`WATCH` / `WARNING` / `CRITICAL`) | **Heuristic (Decision Rule)** | **NOT APPROVED as ML Target** (Approved as Decision Engine Rule) | Alert levels are administrative operational thresholds established by NDMA Standard Operating Procedures, not naturally occurring phenomena. They must be derived from calibrated ML probability and vulnerability via the Operational Risk Engine, not predicted as arbitrary class labels. |
| `citizen_call_urgency` | **Unavailable in Public Domain** | **NOT APPROVED** | No emergency call transcripts exist in open repositories. Model C must use LLM extraction + deterministic rule triage with human operator verification, not a pseudo-supervised classifier. |
| `duplicate_incident_pair` | **Unavailable in Public Domain** | **NOT APPROVED** | No paired duplicate disaster dispatch reports exist in public archives. Model D must use text embedding cosine similarity, not fabricated binary duplicate labels. |

---

## 4. Join Integrity & Leakage Prevention

### 4.1 Permissible Joins
- Joining static terrain features (`elevation_m`, `catchment_slope_deg`, `dist_to_river_m`, `upstream_drainage_sqkm`) to hourly time-series observations on `station_id`.
- Mapping documented historical disaster time intervals (ISO 8601 timestamps) to hourly meteorological time-series on `(time >= start_time) & (time <= end_time)`.

### 4.2 Prohibited Leaking Joins
- **Downstream River Catchment Joins**: Joining national INDOFLOODS daily peak discharge from peninsular river basins (e.g. Cauvery, Krishna) into Mandi local hourly training would introduce severe spatial mismatch and covariate contamination.
- **Post-Event Attribute Joins**: Merging post-disaster damage valuations or death tolls into pre-event hourly records.

---

## 5. Dataset Balance & Sampling Statistics

In `data/real/mandi_real_hydrology_features.csv`:
- **Total Genuine Hourly Records**: 15,624 hours across 7 monitoring stations.
- **Negative Class (`flood_occurred == 0`)**: 14,525 hours (92.97%).
- **Positive Class (`flood_occurred == 1`)**: 1,099 hours (7.03%).
- **Imbalance Ratio**: Approximately $13.2 : 1$.
- **Station Representation**: 2,232 hours each across 7 distinct topographic zones:
  1. `MND_URBAN_01`: Mandi Urban (Beas Main Valley) — 760m
  2. `PND_DAM_02`: Pandoh (Pandoh Dam / Catchment) — 890m
  3. `AUT_JNC_03`: Aut (Larji / Tirthan Confluence) — 1,050m
  4. `THL_GRG_04`: Thalout (Beas River Gorge) — 980m
  5. `JGN_VLY_05`: Jogindernagar (Upper Valley) — 1,220m
  6. `DHR_KHD_06`: Dharampur (Son Khad Catchment) — 900m
  7. `SDR_BSN_07`: Sundernagar (Suketi Khad Basin) — 860m

---

## 6. Train / Test Split Strategy (Strict Temporal/Event Holdout)

To prevent temporal leakage (where random splitting places $t$ in train and $t+1$ in test, artificially inflating metrics through autocorrelation in 72-hour rainfall):

1. **Test Set (Held-Out Mega Disaster Event)**:
   - Time window: **July 1, 2023 to July 25, 2023** (covers the historic July 8–11 catastrophe, 637 positive flood hours, 4,200 total hours across 7 stations).
   - This tests whether a model trained on general monsoon conditions and a separate event can predict an entirely unseen catastrophic disaster!
2. **Training Set**:
   - Baseline Control: **July 1, 2022 to July 31, 2022** (5,208 normal monsoon hours, 0 flood events).
   - Event Wave 2: **July 26, 2023 to August 31, 2023** (covers the August 13–15 cloudburst disaster wave, 462 positive flood hours, 6,216 total hours).
   - Total Training Samples: 11,424 hours.

This split guarantees **complete event isolation** with zero overlap in disaster episodes between training and testing.
