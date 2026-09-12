"""
ml/pipeline/data_sources/open_meteo.py
Flowshield — ERA5-Land Data Fetcher via Open-Meteo Archive API

Fetches hourly ERA5-Land reanalysis for any set of stations defined
in a region config. Variables match the canonical feature pipeline:
precipitation, soil moisture (2 layers), temperature, humidity,
pressure, wind speed.

API Reference: https://open-meteo.com/en/docs/historical-weather-api
License: Copernicus C3S / CC-BY 4.0
"""

import os
import time
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

import pandas as pd
import httpx

logger = logging.getLogger("flowshield.pipeline.open_meteo")

# Open-Meteo Historical Archive API endpoint
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# ERA5-Land variables to request (mapped to Flowshield feature names)
ERA5_VARIABLES = [
    "precipitation",                # → rolling rainfall accumulations
    "rain",                         # → rainfall separation (liquid only)
    "soil_moisture_0_to_7cm",       # → soil_saturation_pct
    "soil_moisture_7_to_28cm",      # → deep_soil_saturation_pct
    "temperature_2m",               # → temperature_c
    "relative_humidity_2m",         # → relative_humidity_pct
    "surface_pressure",             # → surface_pressure_hpa
    "wind_speed_10m",               # → wind_speed_kmh
]

# Rate limiting
MAX_RETRIES = 3
RETRY_DELAY_S = 5.0
REQUEST_DELAY_S = 1.0  # Between station requests


def fetch_station_era5(
    station_id: str,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    cache_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Fetches ERA5-Land hourly data for a single station.

    Parameters
    ----------
    station_id : str
        Unique station identifier (e.g., "MND_URBAN_01").
    latitude, longitude : float
        Station coordinates (WGS84).
    start_date, end_date : str
        ISO date strings (e.g., "2018-01-01", "2023-12-31").
    cache_dir : Path, optional
        Directory to cache raw CSV downloads. If cached file exists, skips API call.

    Returns
    -------
    pd.DataFrame
        Hourly ERA5-Land data with columns: station_id, datetime_utc,
        precipitation, rain, soil_moisture_0_to_7cm, soil_moisture_7_to_28cm,
        temperature_2m, relative_humidity_2m, surface_pressure, wind_speed_10m.
    """
    # Check cache first
    if cache_dir:
        cache_file = cache_dir / f"{station_id}_era5_{start_date}_{end_date}.csv"
        if cache_file.exists():
            logger.info(f"Cache hit for {station_id}: {cache_file}")
            df = pd.read_csv(cache_file, parse_dates=["datetime_utc"])
            return df

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(ERA5_VARIABLES),
        "timezone": "UTC",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                f"Fetching ERA5-Land for {station_id} "
                f"({latitude}, {longitude}) [{start_date} → {end_date}] "
                f"(attempt {attempt}/{MAX_RETRIES})"
            )
            with httpx.Client(timeout=120.0) as client:
                response = client.get(BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

            hourly = data.get("hourly", {})
            timestamps = hourly.get("time", [])
            if not timestamps:
                logger.warning(f"Empty response for {station_id}")
                return pd.DataFrame()

            records = []
            for i, ts in enumerate(timestamps):
                row = {
                    "station_id": station_id,
                    "datetime_utc": ts,
                }
                for var in ERA5_VARIABLES:
                    values = hourly.get(var, [])
                    row[var] = values[i] if i < len(values) else None
                records.append(row)

            df = pd.DataFrame(records)
            df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True)

            logger.info(
                f"Retrieved {len(df)} hourly records for {station_id}"
            )

            # Cache the result
            if cache_dir:
                os.makedirs(cache_dir, exist_ok=True)
                df.to_csv(cache_file, index=False)
                logger.info(f"Cached to {cache_file}")

            return df

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait = RETRY_DELAY_S * attempt * 2
                logger.warning(f"Rate limited. Waiting {wait}s before retry.")
                time.sleep(wait)
            elif attempt < MAX_RETRIES:
                logger.warning(f"HTTP {e.response.status_code} for {station_id}. Retrying in {RETRY_DELAY_S}s.")
                time.sleep(RETRY_DELAY_S)
            else:
                logger.error(f"Failed to fetch data for {station_id} after {MAX_RETRIES} attempts: {e}")
                raise
        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning(f"Error fetching {station_id}: {e}. Retrying.")
                time.sleep(RETRY_DELAY_S)
            else:
                logger.error(f"Failed to fetch data for {station_id}: {e}")
                raise

    return pd.DataFrame()


def fetch_region_era5(
    stations: Dict[str, Dict[str, Any]],
    start_date: str,
    end_date: str,
    cache_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Fetches ERA5-Land data for all stations in a region config.

    Parameters
    ----------
    stations : dict
        Station definitions from region config YAML (keys are station IDs,
        values have latitude, longitude, elevation_m, etc.).
    start_date, end_date : str
        Temporal bounds for the data request.
    cache_dir : Path, optional
        Cache directory for raw downloads.

    Returns
    -------
    pd.DataFrame
        Combined hourly data for all stations with station metadata merged.
    """
    all_frames: List[pd.DataFrame] = []

    for station_id, station_cfg in stations.items():
        lat = station_cfg["latitude"]
        lon = station_cfg["longitude"]

        df = fetch_station_era5(
            station_id=station_id,
            latitude=lat,
            longitude=lon,
            start_date=start_date,
            end_date=end_date,
            cache_dir=cache_dir,
        )

        if df.empty:
            logger.warning(f"No data returned for station {station_id}. Skipping.")
            continue

        # Attach static terrain metadata from config
        df["elevation_m"] = float(station_cfg.get("elevation_m", 0))
        df["catchment_slope_deg"] = float(station_cfg.get("catchment_slope_deg", 0))
        df["dist_to_river_m"] = float(station_cfg.get("dist_to_river_m", 0))
        df["upstream_drainage_sqkm"] = float(station_cfg.get("upstream_drainage_sqkm", 0))
        df["latitude"] = lat
        df["longitude"] = lon
        df["role"] = station_cfg.get("role", "train")

        all_frames.append(df)

        # Rate-limit between stations
        time.sleep(REQUEST_DELAY_S)

    if not all_frames:
        logger.error("No data retrieved for any station in the region.")
        return pd.DataFrame()

    combined = pd.concat(all_frames, ignore_index=True)
    logger.info(
        f"Combined dataset: {len(combined)} rows across "
        f"{combined['station_id'].nunique()} stations"
    )
    return combined
