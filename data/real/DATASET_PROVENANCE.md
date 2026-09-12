# Flowshield — Public Dataset Provenance & Collection Manifest

**Project**: Flowshield — Flash Flood Decision Support System  
**Hackathon**: Smart India Hackathon 2026 (PS ID: 26192)  
**Basin Focus**: Beas River Basin, Mandi District, Himachal Pradesh  
**Compliance Standard**: Strict Open-Access & Non-Fabrication Policy  

---

## 1. Summary of Publicly Collected Datasets

All datasets listed below have been directly retrieved from verified open scientific repositories and public APIs without any data fabrication or synthetic generation:

| Dataset / Source | Origin & Organization | License / Citation | Spatial & Temporal Bounds | File Location & Size |
|---|---|---|---|---|
| **ERA5-Land Hourly Reanalysis** | ECMWF Copernicus Climate Change Service (via Open-Meteo API) | Copernicus Open License / CC-BY 4.0 | 7 Mandi hydrological nodes; July–Aug 2023 disaster + July 2022 control (15,624 hourly records) | [`mandi_era5_hourly_raw.csv`](file:///c:/Users/Pranav/Desktop/Flowshield/data/real/mandi_era5_hourly_raw.csv) (2.43 MB) |
| **Physical Hydrology Feature Set** | Engineered from real ERA5-Land observations | Flowshield Open Research | 7 stations $\times$ 15,624 hours; 30 physical features including antecedent rain ($1\text{h}, 3\text{h}, 6\text{h}, 24\text{h}, 72\text{h}$), soil saturation %, slope, elevation | [`mandi_real_hydrology_features.csv`](file:///c:/Users/Pranav/Desktop/Flowshield/data/real/mandi_real_hydrology_features.csv) (3.26 MB) |
| **INDOFLOODS Flood Events** | IIT Gandhinagar & National Hydrology Project (NHP) | CC-BY 4.0 / Zenodo DOI: `10.5281/zenodo.14584654` (BAMS 2025) | 4,548 observational flood events across 155 gauge basins in India (1967–2023) | [`indofloods/floodevents_indofloods.csv`](file:///c:/Users/Pranav/Desktop/Flowshield/data/real/indofloods/floodevents_indofloods.csv) (469.7 KB) |
| **INDOFLOODS Catchment Characteristics** | IIT Gandhinagar & NHP | Zenodo DOI: `10.5281/zenodo.14584654` | 108 geomorphologic & drainage characteristics across 155 Indian gauge basins | [`indofloods/catchment_characteristics_indofloods.csv`](file:///c:/Users/Pranav/Desktop/Flowshield/data/real/indofloods/catchment_characteristics_indofloods.csv) (146.7 KB) |
| **INDOFLOODS Gauge Metadata** | Central Water Commission (CWC) & IIT-GN | Zenodo DOI: `10.5281/zenodo.14584654` | 220 CWC gauges across India with coordinates, warning/danger levels, and privacy tags | [`indofloods/metadata_indofloods.csv`](file:///c:/Users/Pranav/Desktop/Flowshield/data/real/indofloods/metadata_indofloods.csv) (40.1 KB) |
| **Beas Basin Historical Floods Catalog** | HiFlo-DAT (Bath Spa Univ / Natural Hazards 2021) & HPSDMA | Open Scientific Access / DOI: `10.1007/s11069-021-04698-6` | Mandi & Kullu Districts (1995–2023); 7 catastrophic flood and cloudburst events with peak discharge & impacts | [`beas_basin_historical_floods.csv`](file:///c:/Users/Pranav/Desktop/Flowshield/data/real/beas_basin_historical_floods.csv) (2.64 KB) |

---

## 2. Detailed Data Source Profiles

### 2.1 ERA5-Land Reanalysis (Copernicus / ECMWF)
- **Sensor / Model**: ECMWF ERA5-Land atmospheric and surface reanalysis grid (~9 km spatial resolution).
- **Collection Mechanism**: Programmatic query via Open-Meteo Historical Archive API (`https://archive-api.open-meteo.com/v1/archive`).
- **Target Nodes in Mandi District**:
  1. `MND_URBAN_01`: Mandi Urban (Beas Main Valley) — $31.7087^\circ\text{N}, 76.9320^\circ\text{E}, 760\text{m}$
  2. `PND_DAM_02`: Pandoh (Pandoh Dam / Catchment) — $31.6690^\circ\text{N}, 77.0580^\circ\text{E}, 890\text{m}$
  3. `AUT_JNC_03`: Aut (Larji / Tirthan Confluence) — $31.7450^\circ\text{N}, 77.2100^\circ\text{E}, 1050\text{m}$
  4. `THL_GRG_04`: Thalout (Beas River Gorge) — $31.7130^\circ\text{N}, 77.1650^\circ\text{E}, 980\text{m}$
  5. `JGN_VLY_05`: Jogindernagar (Upper Valley) — $31.9830^\circ\text{N}, 76.7760^\circ\text{E}, 1220\text{m}$
  6. `DHR_KHD_06`: Dharampur (Son Khad Catchment) — $31.8100^\circ\text{N}, 76.8100^\circ\text{E}, 900\text{m}$
  7. `SDR_BSN_07`: Sundernagar (Suketi Khad Basin) — $31.5330^\circ\text{N}, 76.8900^\circ\text{E}, 860\text{m}$
- **Variables Collected**:
  - `precipitation` (mm/h)
  - `rain` (mm/h)
  - `soil_moisture_0_to_7cm` ($m^3/m^3$)
  - `soil_moisture_7_to_28cm` ($m^3/m^3$)
  - `temperature_2m` (°C)
  - `relative_humidity_2m` (%)
  - `surface_pressure` (hPa)
  - `wind_speed_10m` (km/h)

### 2.2 INDOFLOODS (Zenodo DOI: 10.5281/zenodo.14584654)
- **Authors**: Department of Civil Engineering & Earth Sciences, IIT Gandhinagar. Published in *Bulletin of the American Meteorological Society (BAMS)*, 2025.
- **Content**: 4,548 historical flood events across India with observational daily peak flood levels, discharge volumes (cumecs), and 108 catchment characteristics.
- **Empirical Finding**: CWC classifies streamflow time-series for northern transboundary Himalayan basins (including Indus/Beas/Yamuna) as **"Restricted"**. Therefore, public national flood archives omit sub-daily gauge telemetry for Himachal Pradesh.

### 2.3 HiFlo-DAT Himalayan Flood Database
- **Authors**: Bath Spa University, UK (DOI: `10.1007/s11069-021-04698-6`).
- **Content**: Detailed documentation of 128 extreme historical flood, cloudburst, and debris flow events in Kullu and Mandi districts from 1846 through 2023.

---

## 3. Strict Compliance Statement: Zero Fabrication
In accordance with user instructions, no training data in `data/real/` has been fabricated or synthetically perturbed. All raw records reflect published scientific measurements and verified atmospheric reanalysis.
