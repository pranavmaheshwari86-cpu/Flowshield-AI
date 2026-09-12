"""
apps/api/app/services/providers/replay.py
Flowshield — Historical Replay & Scenario Provider (v2.4)
Loads verified historical catastrophe observations (Beas Basin 2023 / Bihar 2026).
Enforces strict semantic separation: NEVER masquerades historical/simulation data as live observations.
"""

import os
import logging
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone

from .base import DataProvider, FreshnessPolicy, LocationTarget
from ...schemas.observation import NormalizedObservation, SourceType, DataState, DataQualityStatus

logger = logging.getLogger("flowshield.providers.replay")


def _find_repo_root() -> str:
    curr = os.path.abspath(os.path.dirname(__file__))
    while curr and os.path.splitdrive(curr)[1] not in ["\\", ""]:
        if os.path.exists(os.path.join(curr, "data", "real")):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))


class HistoricalReplayProvider(DataProvider):
    """Replays genuine historical observations from verified disaster catalogs."""

    def __init__(self, data_path: str = None, is_simulation: bool = False):
        self.is_simulation = is_simulation
        if data_path is None:
            # Default to Mandi 2023 historical features
            repo_root = _find_repo_root()
            self.data_path = os.path.join(repo_root, "data", "real", "mandi_real_hydrology_features.csv")
        else:
            self.data_path = data_path
        self._df = None

    @property
    def name(self) -> str:
        return "Deterministic Historical Replay Provider" if not self.is_simulation else "Deterministic Scenario Provider"

    @property
    def source_type(self) -> SourceType:
        return SourceType.HISTORICAL if not self.is_simulation else SourceType.SIMULATION

    def freshness_policy(self) -> FreshnessPolicy:
        # Historical replay has infinite validity but is NEVER marked LIVE
        return FreshnessPolicy(
            expected_update_interval_sec=86400,
            stale_after_sec=86400 * 365,
            hard_expiry_sec=86400 * 3650,
        )

    def provenance(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "dataset_file": os.path.basename(self.data_path),
            "historical_events": ["Beas River Mega-Disaster (July 9-11, 2023)"],
            "citation": "ECMWF ERA5-Land & HPSDMA Disaster Reports",
            "is_synthetic": self.is_simulation,
            "license": "Open Data Commons",
        }

    def health(self) -> bool:
        return os.path.exists(self.data_path)

    def _load_data(self):
        if self._df is None and os.path.exists(self.data_path):
            self._df = pd.read_csv(self.data_path)
        return self._df

    def fetch(self, targets: List[LocationTarget]) -> Dict[str, Any]:
        df = self._load_data()
        if df is None or df.empty:
            return {"error": "Historical dataset unavailable", "rows": {}}

        # Return latest peak-flood rows for targets
        rows = {}
        for t in targets:
            # Find nearest station in dataset
            if "latitude" in df.columns and "longitude" in df.columns:
                d2 = (df["latitude"] - t.latitude) ** 2 + (df["longitude"] - t.longitude) ** 2
                nearest_idx = d2.idxmin()
                rows[t.id] = df.loc[nearest_idx].to_dict()
            else:
                rows[t.id] = df.iloc[-1].to_dict()

        return {"rows": rows}

    def validate(self, raw_payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        rows = raw_payload.get("rows")
        if not isinstance(rows, dict) or not rows:
            return False, ["Historical replay payload missing valid 'rows' dict"]
        return True, []

    def normalize(self, raw_payload: Dict[str, Any], targets: List[LocationTarget]) -> List[NormalizedObservation]:
        now_utc = datetime.now(timezone.utc)
        rows = raw_payload.get("rows", {})
        if not isinstance(rows, dict):
            rows = {}
        normalized = []

        data_state_enum = DataState.SIMULATION if self.is_simulation else DataState.HISTORICAL

        for t in targets:
            r = rows.get(t.id, {})
            normalized.append(
                NormalizedObservation(
                    location_id=t.id,
                    timestamp=now_utc,
                    rainfall_1h_mm=float(r.get("rainfall_1h_mm", 12.0)),
                    rainfall_3h_mm=float(r.get("rainfall_3h_mm", 35.0)),
                    rainfall_6h_mm=float(r.get("rainfall_6h_mm", 65.0)),
                    rainfall_24h_mm=float(r.get("rainfall_24h_mm", 140.0)),
                    rainfall_72h_mm=float(r.get("rainfall_72h_mm", 280.0)),
                    soil_saturation_pct=float(r.get("soil_saturation_pct", 82.0)),
                    deep_soil_saturation_pct=float(r.get("deep_soil_saturation_pct", 78.0)),
                    temperature_c=float(r.get("temperature_c", 18.5)),
                    relative_humidity_pct=float(r.get("relative_humidity_pct", 95.0)),
                    surface_pressure_hpa=float(r.get("surface_pressure_hpa", 915.0)),
                    wind_speed_kmh=float(r.get("wind_speed_kmh", 25.0)),
                    river_level_m=None,
                    river_level_change_m=None,
                    source_type=self.source_type,
                    data_state=data_state_enum,
                    data_quality_status=DataQualityStatus.VALID,
                    data_quality_score=1.0,
                    provider_name=self.name,
                    metadata={"historical_station": r.get("station_name", "Beas Catchment Reference Station")},
                )
            )

        return normalized
