"""
ml/pipeline/data_sources/indofloods.py
Flowshield — IndoFloods & Historical Flood Event Loader

Loads verified flood events from:
1. IndoFloods (IIT Gandhinagar, Zenodo DOI: 10.5281/zenodo.14584654)
2. Historical SDMA/NDMA catalogs
3. Region config reference_events

Filters events by spatial bounding box to build flood labels
for a specific target region.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger("flowshield.pipeline.indofloods")

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_INDOFLOODS_DIR = _REPO_ROOT / "data" / "real" / "indofloods"


def load_indofloods_events(
    indofloods_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Loads the full IndoFloods event catalog (4,548 events nationally).
    """
    d = indofloods_dir or _INDOFLOODS_DIR
    events_file = d / "floodevents_indofloods.csv"

    if not events_file.exists():
        logger.warning(f"IndoFloods events file not found: {events_file}")
        return pd.DataFrame()

    df = pd.read_csv(events_file)
    logger.info(f"Loaded {len(df)} IndoFloods events from {events_file}")
    return df


def load_indofloods_metadata(
    indofloods_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """Loads CWC gauge metadata (coordinates, warning/danger levels)."""
    d = indofloods_dir or _INDOFLOODS_DIR
    meta_file = d / "metadata_indofloods.csv"

    if not meta_file.exists():
        logger.warning(f"IndoFloods metadata not found: {meta_file}")
        return pd.DataFrame()

    df = pd.read_csv(meta_file)
    logger.info(f"Loaded {len(df)} CWC gauge records from {meta_file}")
    return df


def load_indofloods_catchments(
    indofloods_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """Loads catchment characteristics (108 variables per gauge basin)."""
    d = indofloods_dir or _INDOFLOODS_DIR
    catch_file = d / "catchment_characteristics_indofloods.csv"

    if not catch_file.exists():
        logger.warning(f"IndoFloods catchments not found: {catch_file}")
        return pd.DataFrame()

    df = pd.read_csv(catch_file)
    logger.info(f"Loaded {len(df)} catchment records from {catch_file}")
    return df


def filter_events_by_region(
    events_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    boundary: Dict[str, float],
    lat_col: str = "Latitude",
    lon_col: str = "Longitude",
) -> pd.DataFrame:
    """
    Filters IndoFloods events to those within a region's bounding box.

    Steps:
    1. Join events with gauge metadata on gauge ID
    2. Filter by lat/lon bounding box from region config
    3. Return matched events with their spatial coordinates
    """
    if events_df.empty or metadata_df.empty:
        return pd.DataFrame()

    lat_min = boundary.get("lat_min", -90)
    lat_max = boundary.get("lat_max", 90)
    lon_min = boundary.get("lon_min", -180)
    lon_max = boundary.get("lon_max", 180)

    # Identify or derive GaugeID
    ev = events_df.copy()
    if "GaugeID" not in ev.columns and "EventID" in ev.columns:
        ev["GaugeID"] = ev["EventID"].astype(str).apply(lambda x: "-".join(x.split("-")[:3]))

    gauge_col_candidates = ["GaugeID", "gauge_id", "Station_ID", "station_id"]
    gauge_col = None
    for c in gauge_col_candidates:
        if c in ev.columns and c in metadata_df.columns:
            gauge_col = c
            break

    if gauge_col is None:
        # Attempt direct spatial filtering if events have coordinates
        if lat_col in events_df.columns and lon_col in events_df.columns:
            mask = (
                (events_df[lat_col] >= lat_min)
                & (events_df[lat_col] <= lat_max)
                & (events_df[lon_col] >= lon_min)
                & (events_df[lon_col] <= lon_max)
            )
            filtered = events_df[mask].copy()
            logger.info(
                f"Filtered {len(filtered)}/{len(events_df)} events by direct coordinates"
            )
            return filtered

        logger.warning("Cannot join events with metadata — no common gauge ID column found")
        return pd.DataFrame()

    # Merge events with metadata to get coordinates
    merged = ev.merge(
        metadata_df[[gauge_col, lat_col, lon_col]].drop_duplicates(),
        on=gauge_col,
        how="inner",
    )

    # Spatial filter
    mask = (
        (merged[lat_col] >= lat_min)
        & (merged[lat_col] <= lat_max)
        & (merged[lon_col] >= lon_min)
        & (merged[lon_col] <= lon_max)
    )
    filtered = merged[mask].copy()

    logger.info(
        f"Region filter: {len(filtered)}/{len(events_df)} events "
        f"within [{lat_min:.2f}, {lat_max:.2f}] × [{lon_min:.2f}, {lon_max:.2f}]"
    )
    return filtered


def extract_event_dates(
    filtered_events: pd.DataFrame,
    date_col_candidates: Optional[List[str]] = None,
) -> List[Tuple[str, str]]:
    """
    Extracts (start_date, end_date) tuples from filtered flood events.
    Each event gets a ±24h window for label matching.
    """
    if filtered_events.empty:
        return []

    candidates = date_col_candidates or [
        "Date", "date", "Start_Date", "start_date", "Start Date", "End Date", "Start date", "End date",
        "Event_Date", "event_date", "FloodDate",
    ]

    date_col = None
    for c in candidates:
        if c in filtered_events.columns:
            date_col = c
            break

    if date_col is None:
        logger.warning(f"No date column found in filtered events. Columns: {list(filtered_events.columns)}")
        return []

    dates = pd.to_datetime(filtered_events[date_col], errors="coerce").dropna()
    event_windows = []
    for dt in dates:
        start = (dt - pd.Timedelta(hours=24)).strftime("%Y-%m-%d")
        end = (dt + pd.Timedelta(hours=24)).strftime("%Y-%m-%d")
        event_windows.append((start, end))

    logger.info(f"Extracted {len(event_windows)} event date windows")
    return event_windows


def load_reference_events(region_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extracts reference events defined directly in the region config YAML.
    These are manually curated major flood events with verified dates.
    """
    events = region_config.get("reference_events", [])
    if events:
        logger.info(f"Loaded {len(events)} reference events from region config")
    return events
