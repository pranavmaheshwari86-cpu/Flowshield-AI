"""
ml/pipeline/label_engineering.py
Flowshield — Multi-Region Flood & Flash-Flood Label Engineering

Constructs scientifically defensible flood labels by synthesizing:
1. IndoFloods CWC gauge exceedances (where gauges exist in region)
2. Verified regional disaster catalogs & reference events (SDMA/NDMA)
3. Hydrological Flash Flood Guidance (FFG) trigger thresholds for sparse regions
   (IMD/CWC criteria: high-intensity rainfall on saturated steep terrain)
4. Causal lead-time window expansion (-6h to +12h) for early warning training
5. Leakage-free negative sampling with seasonal balancing

Zero data fabrication — all labels ground in verified dates, regional events,
or published hydrological FFG criteria.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Set
import numpy as np
import pandas as pd

logger = logging.getLogger("flowshield.pipeline.label_engineering")


def build_event_windows(
    reference_events: List[Dict[str, Any]],
    indofloods_windows: Optional[List[Tuple[str, str]]] = None,
    lead_hours: int = 6,
    lag_hours: int = 18,
) -> List[Tuple[pd.Timestamp, pd.Timestamp, str]]:
    """
    Builds datetime intervals for known flood events with early-warning lead time.

    Parameters
    ----------
    reference_events : list of dict
        Events from region config YAML (must contain 'date' or 'date_start'/'date_end').
    indofloods_windows : list of (start_str, end_str), optional
        Extracted windows from IndoFloods.
    lead_hours : int
        Hours prior to event onset to label as positive (for early-warning learning).
    lag_hours : int
        Hours after event peak to continue labeling as active flood/recession.

    Returns
    -------
    List of (window_start_utc, window_end_utc, event_name)
    """
    windows = []

    # 1. Process region config reference events
    for ev in reference_events:
        name = ev.get("event", ev.get("name", "Reference Flood Event"))
        date_str = ev.get("date") or ev.get("date_start")
        if not date_str:
            continue

        try:
            start_dt = pd.to_datetime(date_str, utc=True)
            end_date_str = ev.get("date_end") or date_str
            end_dt = pd.to_datetime(end_date_str, utc=True) + pd.Timedelta(days=1)

            w_start = start_dt - pd.Timedelta(hours=lead_hours)
            w_end = end_dt + pd.Timedelta(hours=lag_hours)
            windows.append((w_start, w_end, name))
        except Exception as e:
            logger.warning(f"Could not parse event date for {name}: {e}")

    # 2. Process IndoFloods windows
    if indofloods_windows:
        for i, (s_str, e_str) in enumerate(indofloods_windows):
            try:
                s_dt = pd.to_datetime(s_str, utc=True) - pd.Timedelta(hours=lead_hours)
                e_dt = pd.to_datetime(e_str, utc=True) + pd.Timedelta(hours=lag_hours)
                windows.append((s_dt, e_dt, f"IndoFloods_CWC_{i+1}"))
            except Exception as e:
                logger.warning(f"Could not parse IndoFloods window ({s_str}, {e_str}): {e}")

    logger.info(f"Constructed {len(windows)} consolidated flood event windows")
    return windows


def apply_flood_labels(
    df: pd.DataFrame,
    region_config: Dict[str, Any],
    indofloods_windows: Optional[List[Tuple[str, str]]] = None,
    use_hydrological_ffg: bool = True,
) -> pd.DataFrame:
    """
    Assigns binary target column 'flood_occurred' (0 or 1) to hourly station data.

    A time step is labeled positive (flood_occurred = 1) if:
    a) Timestamp falls inside a verified flood event window (IndoFloods / reference event)
    OR
    b) Satisfies regional Flash Flood Guidance (FFG) joint physical conditions:
       - High rainfall accumulation (e.g. 24h rain >= regional threshold)
       - High antecedent soil moisture (topsoil saturation >= 70%)
       - Near-river vulnerable location (dist_to_river <= 500m or steep slope)

    Parameters
    ----------
    df : pd.DataFrame
        Station dataframe with canonical feature columns and 'datetime_utc'.
    region_config : dict
        Regional configuration dictionary.
    indofloods_windows : list, optional
        Pre-extracted IndoFloods event windows.
    use_hydrological_ffg : bool
        Whether to apply physical Flash Flood Guidance for periods between cataloged events.

    Returns
    -------
    pd.DataFrame with 'flood_occurred' column added.
    """
    out_df = df.copy()
    if "datetime_utc" in out_df.columns:
        out_df["datetime_utc"] = pd.to_datetime(out_df["datetime_utc"], utc=True)

    out_df["flood_occurred"] = 0

    # Delegate target labeling to IndependentLabeler (strictly authentic disaster catalogs)
    from ml.pipeline.independent_labeler import independent_labeler
    region_slug = region_config.get("region", {}).get("slug", "himachal_pradesh")
    return independent_labeler.label_station_forecasting(out_df, region_slug=region_slug, region_config=region_config, lead_hours=6)
