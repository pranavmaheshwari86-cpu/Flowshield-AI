"""
apps/api/app/services/providers/open_meteo.py
Flowshield — Open-Meteo / ECMWF Copernicus Real-Time Provider (v2.4)
Fetches live atmospheric, precipitation, and multi-layer soil saturation telemetry.
"""

import json
import logging
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone

from .base import DataProvider, FreshnessPolicy, LocationTarget
from ...schemas.observation import NormalizedObservation, SourceType, DataState, DataQualityStatus

logger = logging.getLogger("flowshield.providers.open_meteo")


class OpenMeteoProvider(DataProvider):
    """Acquires live real-time atmospheric and hydrometeorological telemetry from Open-Meteo API."""

    API_URL = "https://api.open-meteo.com/v1/forecast"

    @property
    def name(self) -> str:
        return "Open-Meteo / ECMWF Numerical Telemetry"

    @property
    def source_type(self) -> SourceType:
        return SourceType.REANALYSIS

    def freshness_policy(self) -> FreshnessPolicy:
        # Open-Meteo updates hourly; stale after 2 hours; expired after 6 hours
        return FreshnessPolicy(
            expected_update_interval_sec=3600,
            stale_after_sec=7200,
            hard_expiry_sec=21600,
        )

    def provenance(self) -> Dict[str, Any]:
        return {
            "provider": "Open-Meteo Weather API",
            "source_models": ["ECMWF IFS / ERA5-Land", "DWD ICON"],
            "citation": "Copernicus Climate Change Service / ECMWF",
            "spatial_resolution": "9km to 25km grid (bilinearly interpolated)",
            "temporal_resolution": "1 hour",
            "license": "Open Data Commons / CC BY 4.0",
            "is_synthetic": False,
        }

    def health(self) -> bool:
        """Lightweight health check against Open-Meteo endpoint."""
        try:
            test_url = f"{self.API_URL}?latitude=31.70&longitude=76.93&current=temperature_2m"
            req = urllib.request.Request(test_url, headers={"User-Agent": "Flowshield/2.4 (SIH)"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                return resp.status == 200
        except Exception:
            return False

    def fetch(self, targets: List[LocationTarget]) -> Dict[str, Any]:
        if not targets:
            return {"results": []}

        lats = ",".join(f"{t.latitude:.4f}" for t in targets)
        lons = ",".join(f"{t.longitude:.4f}" for t in targets)

        params = {
            "latitude": lats,
            "longitude": lons,
            "current": "temperature_2m,relative_humidity_2m,precipitation,surface_pressure,wind_speed_10m",
            "hourly": "precipitation,soil_moisture_0_to_7cm,soil_moisture_7_to_28cm",
            "past_days": "3",
            "forecast_days": "1",
            "timezone": "auto",
        }

        query = urllib.parse.urlencode(params)
        url = f"{self.API_URL}?{query}"
        req = urllib.request.Request(url, headers={"User-Agent": "Flowshield-Disaster-Intelligence/2.4"})

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            logger.warning(f"Open-Meteo fetch failed ({e}); returning error payload")
            return {"error": str(e), "results": []}

        if isinstance(payload, dict):
            return {"results": [payload]}
        return {"results": payload}

    def validate(self, raw_payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        if "error" in raw_payload:
            errors.append(f"Provider returned error: {raw_payload['error']}")
            return False, errors

        results = raw_payload.get("results", [])
        if not results:
            errors.append("Empty payload from Open-Meteo")
            return False, errors

        for idx, item in enumerate(results):
            if "current" not in item and "hourly" not in item:
                errors.append(f"Target index {idx} missing both current and hourly blocks")
        return len(errors) == 0, errors

    def normalize(self, raw_payload: Dict[str, Any], targets: List[LocationTarget]) -> List[NormalizedObservation]:
        is_valid, errors = self.validate(raw_payload)
        now_utc = datetime.now(timezone.utc)

        if not is_valid:
            # Generate degraded INSUFFICIENT_DATA stubs for each target
            return [
                NormalizedObservation(
                    location_id=t.id,
                    timestamp=now_utc,
                    rainfall_1h_mm=0.0,
                    rainfall_3h_mm=0.0,
                    rainfall_6h_mm=0.0,
                    rainfall_24h_mm=0.0,
                    rainfall_72h_mm=0.0,
                    soil_saturation_pct=50.0,
                    deep_soil_saturation_pct=50.0,
                    temperature_c=20.0,
                    relative_humidity_pct=70.0,
                    surface_pressure_hpa=920.0,
                    wind_speed_kmh=10.0,
                    river_level_m=None,
                    river_level_change_m=None,
                    source_type=self.source_type,
                    data_state=DataState.INSUFFICIENT_DATA,
                    data_quality_status=DataQualityStatus.INSUFFICIENT_DATA,
                    data_quality_score=0.0,
                    provider_name=self.name,
                    metadata={"validation_errors": errors},
                )
                for t in targets
            ]

        results = raw_payload.get("results", [])
        normalized = []

        for target, item in zip(targets, results):
            current = item.get("current", {})
            hourly = item.get("hourly", {})
            precip = hourly.get("precipitation", [])
            soil_0_7 = hourly.get("soil_moisture_0_to_7cm", [])
            soil_7_28 = hourly.get("soil_moisture_7_to_28cm", [])

            # Compute accumulation windows from hourly past values
            # Typically hourly past_days=3 gives 72 historical hours
            n_hours = len(precip)
            r1 = float(precip[-1]) if n_hours >= 1 else float(current.get("precipitation", 0.0))
            r3 = float(sum(precip[-3:])) if n_hours >= 3 else r1 * 3.0
            r6 = float(sum(precip[-6:])) if n_hours >= 6 else r3 * 2.0
            r24 = float(sum(precip[-24:])) if n_hours >= 24 else r6 * 4.0
            r72 = float(sum(precip[-72:])) if n_hours >= 72 else r24 * 2.5

            # Soil moisture is typically m³/m³ (e.g. 0.35) -> convert to % saturation (0 to 100%)
            # Nominal mountain soil porosity: 0.45 m³/m³
            raw_s1 = float(soil_0_7[-1]) if soil_0_7 else 0.25
            raw_s2 = float(soil_7_28[-1]) if soil_7_28 else 0.25
            soil_pct = min(100.0, max(0.0, (raw_s1 / 0.45) * 100.0))
            deep_soil_pct = min(100.0, max(0.0, (raw_s2 / 0.45) * 100.0))

            temp = float(current.get("temperature_2m", 22.0))
            hum = float(current.get("relative_humidity_2m", 75.0))
            press = float(current.get("surface_pressure", 920.0))
            wind = float(current.get("wind_speed_10m", 10.0))

            normalized.append(
                NormalizedObservation(
                    location_id=target.id,
                    timestamp=now_utc,
                    rainfall_1h_mm=round(r1, 2),
                    rainfall_3h_mm=round(r3, 2),
                    rainfall_6h_mm=round(r6, 2),
                    rainfall_24h_mm=round(r24, 2),
                    rainfall_72h_mm=round(r72, 2),
                    soil_saturation_pct=round(soil_pct, 1),
                    deep_soil_saturation_pct=round(deep_soil_pct, 1),
                    temperature_c=round(temp, 1),
                    relative_humidity_pct=round(hum, 1),
                    surface_pressure_hpa=round(press, 1),
                    wind_speed_kmh=round(wind, 1),
                    river_level_m=None,
                    river_level_change_m=None,
                    source_type=self.source_type,
                    data_state=DataState.OBSERVED,
                    data_quality_status=DataQualityStatus.VALID,
                    data_quality_score=1.0,
                    provider_name=self.name,
                    metadata={"grid_elevation": item.get("elevation", target.elevation_m)},
                )
            )

        return normalized
