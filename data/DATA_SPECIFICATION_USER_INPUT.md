# Flowshield — User Data Provisioning Specification

**Document Version**: 1.0.0 (Production Data Contract)  
**Target Basin**: Beas River Basin, Mandi District, Himachal Pradesh  
**Purpose**: Specification for user-provided real telemetry to bridge the gap between open-access reanalysis and operational, sub-hourly field-calibrated ML deployment.

---

## 1. Executive Summary & The Public Data Gap

Flowshield has successfully identified and downloaded all publicly available scientific datasets:
1. **ECMWF ERA5-Land Reanalysis** (`data/real/mandi_era5_hourly_raw.csv`): 15,624 hourly observations across 7 Mandi hydrological nodes (Precipitation, Rain, Soil Moisture 0–7cm and 7–28cm, Temperature, Pressure, Relative Humidity, Wind Speed).
2. **INDOFLOODS Archive** (`data/real/indofloods/`): 4,548 observational flood events across India with catchment geomorphology.
3. **HiFlo-DAT & HPSDMA Event Inventories** (`data/real/beas_basin_historical_floods.csv`): Historical disaster occurrences (1995–2023).

### What Public Repositories Do NOT Provide (The Data Gap):
- **CWC River Gauge Telemetry**: Central Water Commission classifies raw sub-hourly continuous stage/discharge feeds in northern transboundary basins (Indus/Beas) as **"Restricted"**. Only aggregated daily bulletins are published publicly.
- **IMD Automatic Weather Station (AWS) 15-Minute Data**: IMD's high-frequency AWS network (Mandi, Sundernagar, Karsog) is gated behind official government credentials or paid meteorological licensing.
- **Dam Spillway Release Telemetry**: Real-time hourly gate discharge logs for Pandoh Dam (BBMB) and Larji Dam (HPSEBL) are internal operational records.

If you have access to proprietary institutional archives, academic partnerships, or field sensors, please provide the datasets described in the exact schemas below.

---

## 2. Telemetry Dataset Specifications

### Dataset A: River Gauge Sensor Telemetry (CWC / WRIS)
- **Primary Use**: Ground-truth target for river stage surge forecasting and hydraulic flood routing.
- **Target Stations in Mandi**:
  - `STN_BEAS_MANDI`: Beas River at Mandi Town (Near Victoria Suspension Bridge / Panchvaktra)
  - `STN_BEAS_PANDOH`: Pandoh Dam Outflow / Beas River Downstream
  - `STN_BEAS_THALOUT`: Beas River Gorge at Thalout / Aut
  - `STN_SON_DHARAMPUR`: Son Khad tributary gauge at Dharampur
- **Sampling Frequency**: **15-minute** (optimal) or **1-hour** (acceptable).
- **Target File Format**: CSV (`data/user_provided/river_gauge_telemetry.csv`)

#### Schema Definition:
| Column Name | Data Type | Physical Unit | Required / Optional | Description | Sample Value |
|---|---|---|---|---|---|
| `station_id` | `VARCHAR(32)` | Text code | **Required** | Unique station identifier | `STN_BEAS_MANDI` |
| `timestamp_utc` | `ISO 8601` | UTC (`YYYY-MM-DDTHH:MM:SSZ`) | **Required** | Timestamp of reading | `2023-07-09T08:00:00Z` |
| `timestamp_ist` | `ISO 8601` | IST (`YYYY-MM-DDTHH:MM:SS+05:30`) | **Required** | Local Indian Standard Time | `2023-07-09T13:30:00+05:30` |
| `water_level_m` | `FLOAT` | Meters above MSL | **Required** | Observed river stage height | `764.85` |
| `water_level_above_danger_m` | `FLOAT` | Meters | Optional | Exceedance above danger level | `2.85` |
| `discharge_cumec` | `FLOAT` | $m^3/s$ (cumecs) | **Required** | River discharge flow rate | `3420.0` |
| `rate_of_rise_m_per_hr` | `FLOAT` | Meters / hour | Optional | Computed rate of stage increase | `1.45` |
| `sensor_health_flag` | `VARCHAR(16)` | Enum | Optional | `VALID`, `INTERPOLATED`, `ERR` | `VALID` |

#### Sample CSV Snippet:
```csv
station_id,timestamp_utc,timestamp_ist,water_level_m,water_level_above_danger_m,discharge_cumec,rate_of_rise_m_per_hr,sensor_health_flag
STN_BEAS_MANDI,2023-07-09T04:00:00Z,2023-07-09T09:30:00+05:30,762.10,0.10,1850.0,0.65,VALID
STN_BEAS_MANDI,2023-07-09T05:00:00Z,2023-07-09T10:30:00+05:30,763.20,1.20,2400.0,1.10,VALID
STN_BEAS_MANDI,2023-07-09T06:00:00Z,2023-07-09T11:30:00+05:30,764.85,2.85,3420.0,1.65,VALID
```

---

### Dataset B: High-Frequency Automatic Weather Station (IMD AWS / ARG)
- **Primary Use**: Catching ultra-localized convective cloudbursts ($>100\text{mm}/\text{hr}$) that coarse reanalysis grids smooth out.
- **Target Stations**: Mandi AWS, Sundernagar IMD, Karsog ARG, Gohar ARG, Seraj AWS, Jogindernagar AWS.
- **Sampling Frequency**: **15-minute** intervals.
- **Target File Format**: CSV (`data/user_provided/imd_aws_telemetry.csv`)

#### Schema Definition:
| Column Name | Data Type | Physical Unit | Required / Optional | Description | Sample Value |
|---|---|---|---|---|---|
| `station_id` | `VARCHAR(32)` | Text code | **Required** | AWS Station Code | `IMD_AWS_MND_01` |
| `timestamp_ist` | `ISO 8601` | IST | **Required** | Sensor observation time | `2023-07-09T10:15:00+05:30` |
| `rainfall_15min_mm` | `FLOAT` | Millimeters | **Required** | Rain observed in last 15 min | `28.5` |
| `rainfall_1h_mm` | `FLOAT` | Millimeters | **Required** | Cumulative 1-hour rain | `74.0` |
| `air_temperature_c` | `FLOAT` | Degrees Celsius | Optional | Ambient surface air temp | `21.4` |
| `relative_humidity_pct` | `FLOAT` | Percent (0–100) | Optional | Ambient relative humidity | `96.5` |
| `surface_pressure_hpa` | `FLOAT` | Hectopascals | Optional | Barometric pressure | `918.2` |
| `wind_speed_kmh` | `FLOAT` | km/h | Optional | 10m surface wind speed | `34.2` |
| `wind_gust_kmh` | `FLOAT` | km/h | Optional | Peak wind gust | `58.0` |

---

### Dataset C: Dam & Reservoir Operational Logs (BBMB / HPSEBL)
- **Primary Use**: Predicting sudden artificial or regulated discharge surges along the river channel.
- **Target Facilities**:
  - **Pandoh Dam** (Bhakra Beas Management Board — BBMB)
  - **Larji Hydroelectric Project Dam** (HPSEBL)
- **Sampling Frequency**: **1-hour** intervals during monsoon months (June–September).
- **Target File Format**: CSV (`data/user_provided/dam_operations_log.csv`)

#### Schema Definition:
| Column Name | Data Type | Physical Unit | Required / Optional | Description | Sample Value |
|---|---|---|---|---|---|
| `facility_id` | `VARCHAR(32)` | Text code | **Required** | `DAM_PANDOH` or `DAM_LARJI` | `DAM_PANDOH` |
| `timestamp_ist` | `ISO 8601` | IST | **Required** | Operational logging time | `2023-07-09T12:00:00+05:30` |
| `reservoir_level_m` | `FLOAT` | Meters above MSL | **Required** | Water level in reservoir | `621.50` |
| `full_reservoir_level_m` | `FLOAT` | Meters above MSL | **Required** | Max capacity level (FRL) | `621.79` |
| `inflow_cumec` | `FLOAT` | $m^3/s$ | **Required** | Inflow from upstream Beas | `3950.0` |
| `total_outflow_cumec` | `FLOAT` | $m^3/s$ | **Required** | Total water discharged | `3780.0` |
| `spillway_gates_open` | `INTEGER` | Count | Optional | Number of open spillway crest gates | `5` |
| `warning_siren_triggered` | `BOOLEAN` | `true` / `false` | Optional | Whether downstream warning sirens sounded | `true` |

---

### Dataset D: In-Situ Soil Moisture & Piezometer Telemetry
- **Primary Use**: Direct ground-truth slope saturation to model debris flow and mudslide triggering.
- **Target File Format**: CSV (`data/user_provided/soil_sensors_telemetry.csv`)

#### Schema Definition:
| Column Name | Data Type | Physical Unit | Description | Sample Value |
|---|---|---|---|---|
| `sensor_id` | `VARCHAR(32)` | Text | Hillslope probe ID | `SLP_PRB_PND_01` |
| `timestamp_ist` | `ISO 8601` | IST | Observation timestamp | `2023-07-09T11:00:00+05:30` |
| `soil_vwc_10cm_pct` | `FLOAT` | Volumetric % (0–100) | Moisture at 10cm depth | `43.8` |
| `soil_vwc_30cm_pct` | `FLOAT` | Volumetric % (0–100) | Moisture at 30cm depth | `41.2` |
| `pore_water_pressure_kpa`| `FLOAT` | Kilopascals | Piezometric pressure | `14.5` |

---

## 3. How to Submit This Data

Create the directory `data/user_provided/` and place your CSV files directly into it:
```
data/
└── user_provided/
    ├── river_gauge_telemetry.csv
    ├── imd_aws_telemetry.csv
    ├── dam_operations_log.csv
    └── soil_sensors_telemetry.csv
```

Once uploaded, run the ingestion and validation command:
```bash
python scripts/ingest_user_data.py
```
Flowshield will automatically validate timestamps, missing values, physical ranges, join with the ERA5-Land reanalysis feature matrix, and retrain the XGBoost inference models.
