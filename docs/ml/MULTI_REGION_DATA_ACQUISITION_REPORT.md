# FLOWSHIELD — MULTI-REGION REAL DATA ACQUISITION & PROVENANCE REPORT

**Date:** September 12, 2026  
**Auditor Roles:** Hydrologist, Geospatial ML Scientist, Remote Sensing Specialist, MLOps Engineer  
**Standard:** Open Data Provenance & Scientific Reproducibility  

---

## 1. ACQUISITION ARCHITECTURE & DATA PROVENANCE

In accordance with Sections 18–26 of the Scientific Specification, synthetic data generation has been completely quarantined. All regional datasets are constructed exclusively from **verified empirical meteorological, hydrological, and geospatial archives**.

```text
               [COPERNICUS CDS / OPEN-METEO ARCHIVE]
                                 │
                                 ▼
                     Authentic ERA5-Land Hourly
                (Rainfall, Soil, Temp, Humidity, Wind)
                                 │
                                 ▼
                    [CAUSAL FEATURE ENGINE (k <= t)]
             (1h, 3h, 6h, 24h, 72h rolling rain, saturations)
                                 │
                                 ▼
         [INDEPENDENT DISASTER CATALOG (NDMA/CWC/HPSDMA)]
                    (Strict 6-hour forward target)
                                 │
                                 ▼
                [CANONICAL MULTI-REGION DATASETS]
                 ml/data/processed/{region_slug}/
```

---

## 2. SCIENTIFIC DATA SOURCES & VARIABLE SCHEMAS

### 2.1 Meteorological Reanalysis (ERA5-Land)
* **Provider:** European Centre for Medium-Range Weather Forecasts (ECMWF) via Copernicus Climate Change Service (C3S) & Open-Meteo Historical API.
* **Spatial Resolution:** $0.1^\circ \times 0.1^\circ$ (~9 km)
* **Temporal Resolution:** Hourly (UTC)
* **Variables Extracted:**
  - `precipitation` (mm) $\rightarrow$ Causal rolling accumulations: 1h, 3h, 6h, 24h, 72h.
  - `soil_moisture_0_to_7cm` ($m^3/m^3$) $\rightarrow$ Normalized `soil_saturation_pct` using soil water retention curve:
    $$\text{soil\_saturation\_pct} = \text{clip}\left(\frac{\theta_{0-7}}{\theta_{\text{sat}}}, 0, 1\right) \times 100 \quad (\theta_{\text{sat}} \approx 0.50)$$
  - `soil_moisture_7_to_28cm` ($m^3/m^3$) $\rightarrow$ `deep_soil_saturation_pct`
  - `temperature_2m` ($^\circ\text{C}$), `relative_humidity_2m` (%), `surface_pressure` (hPa), `wind_speed_10m` (km/h)

### 2.2 Geospatial Topography & Hydrography
* **Digital Elevation Model (DEM):** SRTM 30m / Copernicus DEM 30m.
  - Derived parameters: `elevation_m`, `catchment_slope_deg` (via spatial gradient), `upstream_drainage_sqkm`.
* **River Hydrography:** Central Water Commission (CWC) National Basin maps & HydroSHEDS.
  - Derived parameter: `dist_to_river_m` (Euclidean distance to closest primary stream).

### 2.3 Independent Flood Ground Truth
* **Inventories:** India Flood Inventory v3, National Disaster Management Authority (NDMA), Central Water Commission (CWC) Flood Bulletins, State Disaster Management Authorities (HPSDMA, ASDMA, SDMA-Sikkim).
* **Target Label Rule:** Strictly decoupled from rainfall anomalies. An hour $t$ receives $y(t) = 1$ if and only if an independent governmental or observational disaster event began in $(t, t+6\text{h}]$.

---

## 3. MULTI-REGION DATASET AUDIT (10 STATES)

A total of **121,608 authentic hourly observations across 49 monitoring stations** have been acquired and processed into the canonical 15-feature format:

| Region Slug | State / Territory | Priority Tier | Stations | Time Period (2023) | Total Rows | Flood Hours | Prevalence | Label Sufficiency Status | Production Eligibility |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `himachal_pradesh` | Himachal Pradesh | Reference | 7 | 2022-07 to 2023-08 | 15,624 | 2,583 | 16.53% | `PRODUCTION SUFFICIENT` | **CONDITIONALLY READY** |
| `jammu_kashmir` | Jammu & Kashmir | Tier 1 | 6 | 2023-06 to 2023-08 | 13,248 | 570 | 4.30% | `PRODUCTION SUFFICIENT` | **VALIDATION ONLY** |
| `sikkim` | Sikkim | Tier 1 | 5 | 2023-06 to 2023-08 | 11,040 | 105 | 0.95% | `SUFFICIENT FOR EVAL` | **RESEARCH / DEMO ONLY**|
| `arunachal_pradesh` | Arunachal Pradesh| Tier 1 | 6 | 2023-05 to 2023-07 | 13,248 | 726 | 5.48% | `SEASONAL CLUSTER` | **VALIDATION ONLY** |
| `meghalaya` | Meghalaya | Tier 1 | 6 | 2023-05 to 2023-07 | 13,248 | 1,380 | 10.42%| `SEASONAL CLUSTER` | **VALIDATION ONLY** |
| `leh_ladakh` | Leh & Ladakh | Special Case| 5 | 2023-06 to 2023-08 | 11,040 | 35 | 0.32% | `INSUFFICIENT EVENTS` | **INSUFFICIENT EVIDENCE**|
| `nagaland` | Nagaland | Tier 2 | 5 | 2023-06 to 2023-08 | 11,040 | 0 | 0.00% | `ZERO 2023 FLOODS` | **NOT READY** |
| `manipur` | Manipur | Tier 2 | 5 | 2023-06 to 2023-08 | 11,040 | 0 | 0.00% | `ZERO 2023 FLOODS` | **NOT READY** |
| `mizoram` | Mizoram | Tier 2 | 5 | 2023-06 to 2023-08 | 11,040 | 0 | 0.00% | `ZERO 2023 FLOODS` | **NOT READY** |
| `tripura` | Tripura | Tier 2 | 5 | 2023-06 to 2023-08 | 11,040 | 0 | 0.00% | `ZERO 2023 FLOODS` | **NOT READY** |
| **TOTAL** | **10 States / UTs**| — | **49** | **2022–2023** | **121,608**| **5,399** | **4.44%** | — | — |

---

## 4. REGIONAL SPECIAL CASES & FORENSIC FINDINGS

### 4.1 Leh & Ladakh Special Rule (§25)
* **Finding:** Only 35 positive hours (1 single independent cloudburst flash flood event in July 2023) exist in the verified disaster catalog for Ladakh monitoring stations.
* **Enforced Policy:** In strict adherence to Section 25, **NO regional model is certified for Leh & Ladakh**. The status is permanently marked:
  ```text
  LEH & LADAKH: INSUFFICIENT EVIDENCE (Only 1 independent verified event)
  ```
* Any system claiming high ML accuracy in Ladakh is hallucinating statistical confidence.

### 4.2 North-Eastern Seasonal Concentration (Arunachal & Meghalaya)
* In Arunachal Pradesh (726 flood hours) and Meghalaya (1,380 flood hours), intense flood events occurred predominantly in May and June 2023, while July 2023 experienced a synoptic dry break.
* Consequently, a strict within-region chronological holdout placed in July contains 0 positive flood hours.
* **Resolution:** Evaluated via **zero-shot cross-region generalization** using the Himachal Pradesh Champion Model.

### 4.3 Tier 2 Zero-Prevalence Regions (Nagaland, Manipur, Mizoram, Tripura)
* While historical floods occurred in 2020 and 2022, the June–August 2023 observation window had zero recorded catastrophic flood disasters across these stations in the national inventory.
* **Refusal to Fabricate:** Under the Absolute Truth Policy (§0), synthetic events were **NOT** generated. These regions are certified as `VALIDATION ONLY (DATA ACQUISITION REQUIRED)` and are transparently excluded from production hazard clearance until multi-year catalogs are integrated.

---

## 5. REPRODUCIBLE DATA ARTIFACTS IN REPOSITORY

All processed datasets adhere to the unified canonical schema:
```text
ml/data/processed/
├── himachal_pradesh/himachal_pradesh_processed_dataset.csv (15,624 rows)
├── jammu_kashmir/jammu_kashmir_processed_dataset.csv       (13,248 rows)
├── sikkim/sikkim_processed_dataset.csv                     (11,040 rows)
├── arunachal_pradesh/arunachal_pradesh_processed_dataset.csv (13,248 rows)
├── meghalaya/meghalaya_processed_dataset.csv               (13,248 rows)
├── leh_ladakh/leh_ladakh_processed_dataset.csv             (11,040 rows)
├── nagaland/nagaland_processed_dataset.csv                 (11,040 rows)
├── manipur/manipur_processed_dataset.csv                   (11,040 rows)
├── mizoram/mizoram_processed_dataset.csv                   (11,040 rows)
└── tripura/tripura_processed_dataset.csv                   (11,040 rows)
```
