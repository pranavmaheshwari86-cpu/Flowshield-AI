"""
ml/pipeline/feature_engineering.py
Flowshield — Canonical 15-Feature Engineering from Raw ERA5-Land Data

Transforms raw ERA5-Land hourly observations into the canonical
Flowshield feature contract. All transformations are documented
and deterministic.

Feature Provenance:
    rainfall_1h_mm           ← precipitation (direct hourly, mm)
    rainfall_3h_mm           ← rolling sum of precipitation over 3h
    rainfall_6h_mm           ← rolling sum of precipitation over 6h
    rainfall_24h_mm          ← rolling sum of precipitation over 24h
    rainfall_72h_mm          ← rolling sum of precipitation over 72h
    soil_saturation_pct      ← soil_moisture_0_to_7cm × 100 / field_capacity
    deep_soil_saturation_pct ← soil_moisture_7_to_28cm × 100 / field_capacity
    temperature_c            ← temperature_2m (direct, °C)
    relative_humidity_pct    ← relative_humidity_2m (direct, %)
    surface_pressure_hpa     ← surface_pressure (convert Pa → hPa)
    wind_speed_kmh           ← wind_speed_10m (direct, km/h)
    elevation_m              ← static terrain attribute from station config
    catchment_slope_deg      ← static terrain attribute from station config
    dist_to_river_m          ← static terrain attribute from station config
    upstream_drainage_sqkm   ← static terrain attribute from station config
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from ml.registry.feature_contract import CANONICAL_FEATURES, PHYSICAL_BOUNDS

logger = logging.getLogger("flowshield.pipeline.feature_engineering")

# Approximate field capacity for volumetric water content → % saturation
# ERA5-Land soil moisture is in m³/m³. Typical field capacity ~0.35 m³/m³
# for loamy soils. Range 0.20-0.45 depending on soil type.
DEFAULT_FIELD_CAPACITY = 0.35


def engineer_features(
    raw_df: pd.DataFrame,
    field_capacity: float = DEFAULT_FIELD_CAPACITY,
) -> pd.DataFrame:
    """
    Transforms raw ERA5-Land hourly data into the canonical 15-feature schema.

    Parameters
    ----------
    raw_df : pd.DataFrame
        Raw ERA5-Land data with columns: station_id, datetime_utc,
        precipitation, rain, soil_moisture_0_to_7cm, soil_moisture_7_to_28cm,
        temperature_2m, relative_humidity_2m, surface_pressure, wind_speed_10m,
        elevation_m, catchment_slope_deg, dist_to_river_m, upstream_drainage_sqkm.

    field_capacity : float
        Volumetric water content at field capacity (m³/m³).

    Returns
    -------
    pd.DataFrame
        DataFrame with canonical 15 features + station_id + datetime_utc.
    """
    if raw_df.empty:
        logger.warning("Empty input DataFrame — returning empty features.")
        return pd.DataFrame(columns=["station_id", "datetime_utc"] + CANONICAL_FEATURES)

    df = raw_df.copy()
    if "datetime_utc" not in df.columns and "time" in df.columns:
        df["datetime_utc"] = df["time"]
    if "station_id" not in df.columns:
        df["station_id"] = "STN_01"

    sort_cols = [c for c in ["station_id", "datetime_utc"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols).reset_index(drop=True)

    # ----- Rainfall rolling accumulations (per station) -----
    # Use 'precipitation' column (mm/h in ERA5-Land via Open-Meteo)
    precip_col = "precipitation"
    if precip_col not in df.columns:
        precip_col = "rain"
    if precip_col not in df.columns:
        logger.error("No precipitation or rain column found in raw data.")
        raise ValueError("Missing precipitation column in raw ERA5-Land data.")

    # Ensure precipitation is numeric and non-negative
    df[precip_col] = pd.to_numeric(df[precip_col], errors="coerce").fillna(0).clip(lower=0)

    # Rolling sums grouped by station (causal — only past data, no leakage)
    grouped = df.groupby("station_id")[precip_col]
    df["rainfall_1h_mm"] = df[precip_col].round(2)
    df["rainfall_3h_mm"] = grouped.transform(
        lambda x: x.rolling(window=3, min_periods=1).sum()
    ).round(2)
    df["rainfall_6h_mm"] = grouped.transform(
        lambda x: x.rolling(window=6, min_periods=1).sum()
    ).round(2)
    df["rainfall_24h_mm"] = grouped.transform(
        lambda x: x.rolling(window=24, min_periods=1).sum()
    ).round(2)
    df["rainfall_72h_mm"] = grouped.transform(
        lambda x: x.rolling(window=72, min_periods=1).sum()
    ).round(2)

    # ----- Soil saturation (VWC → % of field capacity) -----
    if "soil_moisture_0_to_7cm" in df.columns:
        vwc_top = pd.to_numeric(df["soil_moisture_0_to_7cm"], errors="coerce").fillna(0)
        df["soil_saturation_pct"] = (vwc_top / field_capacity * 100).clip(0, 100).round(1)
    else:
        df["soil_saturation_pct"] = np.nan

    if "soil_moisture_7_to_28cm" in df.columns:
        vwc_deep = pd.to_numeric(df["soil_moisture_7_to_28cm"], errors="coerce").fillna(0)
        df["deep_soil_saturation_pct"] = (vwc_deep / field_capacity * 100).clip(0, 100).round(1)
    else:
        df["deep_soil_saturation_pct"] = np.nan

    # ----- Meteorological features (direct mapping) -----
    if "temperature_2m" in df.columns:
        df["temperature_c"] = pd.to_numeric(df["temperature_2m"], errors="coerce")
    else:
        df["temperature_c"] = np.nan

    if "relative_humidity_2m" in df.columns:
        df["relative_humidity_pct"] = pd.to_numeric(
            df["relative_humidity_2m"], errors="coerce"
        ).clip(0, 100)
    else:
        df["relative_humidity_pct"] = np.nan

    if "surface_pressure" in df.columns:
        pressure = pd.to_numeric(df["surface_pressure"], errors="coerce")
        # Open-Meteo returns hPa directly, but guard against Pa
        if pressure.median() > 2000:
            pressure = pressure / 100.0  # Pa → hPa
        df["surface_pressure_hpa"] = pressure.round(1)
    else:
        df["surface_pressure_hpa"] = np.nan

    if "wind_speed_10m" in df.columns:
        df["wind_speed_kmh"] = pd.to_numeric(
            df["wind_speed_10m"], errors="coerce"
        ).clip(lower=0).round(1)
    else:
        df["wind_speed_kmh"] = np.nan

    # ----- Terrain features (static from station config) -----
    for col in ["elevation_m", "catchment_slope_deg", "dist_to_river_m", "upstream_drainage_sqkm"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = np.nan

    # ----- Clip to physical bounds -----
    for feat, (lo, hi) in PHYSICAL_BOUNDS.items():
        if feat in df.columns:
            df[feat] = df[feat].clip(lo, hi)

    # ----- Select canonical columns -----
    output_cols = ["station_id", "datetime_utc", "latitude", "longitude", "role"] + CANONICAL_FEATURES
    available_cols = [c for c in output_cols if c in df.columns]
    result = df[available_cols].copy()

    # Validate no future leakage: rolling windows are purely backward-looking
    # (pandas rolling with default center=False is causal by design)
    missing_pct = result[CANONICAL_FEATURES].isnull().mean() * 100
    for feat in CANONICAL_FEATURES:
        pct = missing_pct[feat]
        if pct > 50:
            logger.warning(
                f"Feature '{feat}' has {pct:.1f}% missing values after engineering"
            )

    logger.info(
        f"Feature engineering complete: {len(result)} rows, "
        f"{len(CANONICAL_FEATURES)} canonical features"
    )
    return result
