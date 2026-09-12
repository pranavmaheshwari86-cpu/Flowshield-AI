"""
ml/features/feature_definitions.py
Flowshield — Canonical Hydrological & Meteorological Feature Definitions
Smart India Hackathon 2026 (PS ID: 26192)

Defines legitimate, physically sound features derived strictly from verified
ECMWF ERA5-Land reanalysis and DEM topographic attributes.
Zero synthetic features. Zero future-looking leakage.
"""

from typing import List, Dict, Any

# Canonical 15 features for Flash Flood Event Prediction
CANONICAL_FEATURE_NAMES: List[str] = [
    # 1. Short-term rainfall intensity (Flash flood / cloudburst trigger)
    "rainfall_1h_mm",
    
    # 2. Medium-term antecedent rainfall (Sub-catchment accumulation)
    "rainfall_3h_mm",
    
    # 3. Intermediate rainfall accumulation
    "rainfall_6h_mm",
    
    # 4. Daily antecedent rainfall (Basin saturation loading)
    "rainfall_24h_mm",
    
    # 5. Multi-day cumulative rainfall (Deep saturation / baseflow loading)
    "rainfall_72h_mm",
    
    # 6. Topsoil saturation ratio (% of field capacity ~0.45 m^3/m^3)
    "soil_saturation_pct",
    
    # 7. Deep soil saturation ratio (% of field capacity 7-28cm)
    "deep_soil_saturation_pct",
    
    # 8. Ambient air temperature at 2m (Celsius)
    "temperature_c",
    
    # 9. Relative atmospheric humidity (%)
    "relative_humidity_pct",
    
    # 10. Barometric surface pressure (hPa)
    "surface_pressure_hpa",
    
    # 11. Surface wind speed at 10m (km/h)
    "wind_speed_kmh",
    
    # 12. Settlement / station elevation above sea level (meters)
    "elevation_m",
    
    # 13. Mean catchment hillslope incline (degrees)
    "catchment_slope_deg",
    
    # 14. Distance to active river channel (meters)
    "dist_to_river_m",
    
    # 15. Upstream contributing catchment drainage area (sq km)
    "upstream_drainage_sqkm",
]

TARGET_COLUMN: str = "flood_occurred"

# Feature metadata and physical boundaries for validation
FEATURE_METADATA: Dict[str, Dict[str, Any]] = {
    "rainfall_1h_mm": {
        "display_name": "Rainfall (1h Intensity)",
        "unit": "mm",
        "min": 0.0,
        "max": 300.0,
        "description": "Hourly precipitation rate from ERA5-Land reanalysis."
    },
    "rainfall_3h_mm": {
        "display_name": "Rainfall (3h Cumulative)",
        "unit": "mm",
        "min": 0.0,
        "max": 500.0,
        "description": "Rolling 3-hour accumulated rainfall."
    },
    "rainfall_6h_mm": {
        "display_name": "Rainfall (6h Cumulative)",
        "unit": "mm",
        "min": 0.0,
        "max": 700.0,
        "description": "Rolling 6-hour accumulated rainfall."
    },
    "rainfall_24h_mm": {
        "display_name": "Rainfall (24h Cumulative)",
        "unit": "mm",
        "min": 0.0,
        "max": 1000.0,
        "description": "Rolling 24-hour antecedent rainfall index."
    },
    "rainfall_72h_mm": {
        "display_name": "Rainfall (72h Cumulative)",
        "unit": "mm",
        "min": 0.0,
        "max": 1500.0,
        "description": "Rolling 72-hour macro saturation precipitation."
    },
    "soil_saturation_pct": {
        "display_name": "Topsoil Saturation (0-7cm)",
        "unit": "%",
        "min": 0.0,
        "max": 100.0,
        "description": "Topsoil moisture expressed as percentage of field capacity."
    },
    "deep_soil_saturation_pct": {
        "display_name": "Deep Soil Saturation (7-28cm)",
        "unit": "%",
        "min": 0.0,
        "max": 100.0,
        "description": "Root zone moisture saturation percentage."
    },
    "temperature_c": {
        "display_name": "Air Temperature",
        "unit": "°C",
        "min": -20.0,
        "max": 50.0,
        "description": "2m surface air temperature."
    },
    "relative_humidity_pct": {
        "display_name": "Relative Humidity",
        "unit": "%",
        "min": 0.0,
        "max": 100.0,
        "description": "Near-surface relative humidity."
    },
    "surface_pressure_hpa": {
        "display_name": "Surface Pressure",
        "unit": "hPa",
        "min": 600.0,
        "max": 1100.0,
        "description": "Atmospheric pressure adjusted for elevation."
    },
    "wind_speed_kmh": {
        "display_name": "Wind Speed",
        "unit": "km/h",
        "min": 0.0,
        "max": 200.0,
        "description": "10m surface horizontal wind speed."
    },
    "elevation_m": {
        "display_name": "Altitude / Elevation",
        "unit": "m",
        "min": 500.0,
        "max": 4500.0,
        "description": "Settlement elevation above sea level."
    },
    "catchment_slope_deg": {
        "display_name": "Catchment Slope",
        "unit": "°",
        "min": 0.0,
        "max": 75.0,
        "description": "Average terrain incline in degrees."
    },
    "dist_to_river_m": {
        "display_name": "Distance to River Channel",
        "unit": "m",
        "min": 0.0,
        "max": 10000.0,
        "description": "Perpendicular distance to active river bed."
    },
    "upstream_drainage_sqkm": {
        "display_name": "Upstream Drainage Area",
        "unit": "km²",
        "min": 10.0,
        "max": 25000.0,
        "description": "Catchment area draining into this river section."
    },
}

# Regional monitoring stations in Mandi District (Beas River Basin corridor)
MANDI_STATIONS_METADATA: Dict[str, Dict[str, Any]] = {
    "AUT_JNC_03": {
        "name": "Aut Junction / Larji Dam",
        "latitude": 31.7250,
        "longitude": 77.2100,
        "elevation_m": 980.0,
        "catchment_slope_deg": 31.0,
        "dist_to_river_m": 60.0,
        "upstream_drainage_sqkm": 5100.0,
        "role": "train"
    },
    "DHR_KHD_06": {
        "name": "Dharampur Khad / Son River",
        "latitude": 31.7850,
        "longitude": 76.8200,
        "elevation_m": 850.0,
        "catchment_slope_deg": 19.5,
        "dist_to_river_m": 95.0,
        "upstream_drainage_sqkm": 850.0,
        "role": "spatial_holdout_val"
    },
    "JGN_VLY_05": {
        "name": "Joginder Nagar / Uhl River",
        "latitude": 31.9820,
        "longitude": 76.7720,
        "elevation_m": 1220.0,
        "catchment_slope_deg": 26.0,
        "dist_to_river_m": 110.0,
        "upstream_drainage_sqkm": 1120.0,
        "role": "train"
    },
    "MND_URBAN_01": {
        "name": "Mandi Urban / Victoria Bridge",
        "latitude": 31.7100,
        "longitude": 76.9320,
        "elevation_m": 760.0,
        "catchment_slope_deg": 16.0,
        "dist_to_river_m": 35.0,
        "upstream_drainage_sqkm": 6350.0,
        "role": "train"
    },
    "PND_DAM_02": {
        "name": "Pandoh Dam Reservoir",
        "latitude": 31.6681,
        "longitude": 77.0583,
        "elevation_m": 895.0,
        "catchment_slope_deg": 22.0,
        "dist_to_river_m": 45.0,
        "upstream_drainage_sqkm": 5400.0,
        "role": "spatial_holdout_val"
    },
    "SDR_BSN_07": {
        "name": "Sundernagar / Suketi Khad",
        "latitude": 31.5320,
        "longitude": 76.9110,
        "elevation_m": 860.0,
        "catchment_slope_deg": 15.0,
        "dist_to_river_m": 140.0,
        "upstream_drainage_sqkm": 1950.0,
        "role": "train"
    },
    "THL_GRG_04": {
        "name": "Thalout / Beas Gorge",
        "latitude": 31.7120,
        "longitude": 77.1850,
        "elevation_m": 940.0,
        "catchment_slope_deg": 34.0,
        "dist_to_river_m": 50.0,
        "upstream_drainage_sqkm": 4920.0,
        "role": "train"
    },
}

PHYSICAL_MIN_BOUNDS: Dict[str, float] = {k: float(v["min"]) for k, v in FEATURE_METADATA.items()}
PHYSICAL_MAX_BOUNDS: Dict[str, float] = {k: float(v["max"]) for k, v in FEATURE_METADATA.items()}
STATION_COORDINATES: Dict[str, Dict[str, Any]] = MANDI_STATIONS_METADATA

