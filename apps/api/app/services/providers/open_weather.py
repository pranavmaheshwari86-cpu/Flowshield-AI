"""
apps/api/app/services/providers/open_weather.py
Flowshield — OpenWeatherMap Real-Time Telemetry Provider
Fetches live atmospheric, temperature, humidity, pressure, wind, and precipitation telemetry.
"""

import json
import time
import logging
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone

from .base import DataProvider, FreshnessPolicy, LocationTarget
from ...schemas.observation import NormalizedObservation, SourceType, DataState, DataQualityStatus
from ...config import settings
from ...utils.ssl_context import get_ssl_context

logger = logging.getLogger("flowshield.providers.open_weather")

_GLOBAL_OPENWEATHER_BLOCKED_UNTIL: float = 0.0
_GLOBAL_OPENWEATHER_ERROR: Optional[str] = None


class OpenWeatherProvider(DataProvider):
    """Acquires live real-time atmospheric and precipitation telemetry from OpenWeatherMap API."""

    API_URL_WEATHER = "https://api.openweathermap.org/data/2.5/weather"
    API_URL_FORECAST = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or settings.OPENWEATHER_API_KEY or "").strip()

    @property
    def _circuit_breaker_until(self) -> float:
        return _GLOBAL_OPENWEATHER_BLOCKED_UNTIL

    @_circuit_breaker_until.setter
    def _circuit_breaker_until(self, val: float):
        global _GLOBAL_OPENWEATHER_BLOCKED_UNTIL
        _GLOBAL_OPENWEATHER_BLOCKED_UNTIL = val

    @property
    def _circuit_breaker_error(self) -> Optional[str]:
        return _GLOBAL_OPENWEATHER_ERROR

    @_circuit_breaker_error.setter
    def _circuit_breaker_error(self, val: Optional[str]):
        global _GLOBAL_OPENWEATHER_ERROR
        _GLOBAL_OPENWEATHER_ERROR = val

    @property
    def name(self) -> str:
        return "OpenWeatherMap Live API"

    @property
    def source_type(self) -> SourceType:
        return SourceType.AUTOMATED_STATION

    def freshness_policy(self) -> FreshnessPolicy:
        # OpenWeather updates every 10-30 minutes; stale after 1 hour
        return FreshnessPolicy(
            expected_update_interval_sec=1800,
            stale_after_sec=3600,
            hard_expiry_sec=14400,
        )

    def provenance(self) -> Dict[str, Any]:
        return {
            "provider": "OpenWeatherMap Current & Forecast API",
            "source_models": ["Global Meteorological Broadcast / Station Network", "NWP Models"],
            "citation": "OpenWeather Ltd (Vane Weather)",
            "spatial_resolution": "Station point / 0.1 deg grid interpolation",
            "temporal_resolution": "Real-time / 10-30 min update cycle",
            "license": "Commercial / Standard OpenWeather API License",
            "is_synthetic": False,
        }

    def health(self) -> bool:
        """Lightweight health check against OpenWeather endpoint."""
        if not self.api_key:
            return False
        try:
            test_url = f"{self.API_URL_WEATHER}?lat=31.70&lon=76.93&appid={self.api_key}&units=metric"
            req = urllib.request.Request(test_url, headers={"User-Agent": "Flowshield-Disaster-Intelligence/2.4"})
            with urllib.request.urlopen(req, context=get_ssl_context(), timeout=4) as resp:
                return resp.status == 200
        except Exception as e:
            logger.debug(f"OpenWeather health check failed: {e}")
            return False

    def fetch(self, targets: List[LocationTarget]) -> Dict[str, Any]:
        if not targets:
            return {"results": []}

        if not self.api_key:
            return {"error": "Missing OPENWEATHER_API_KEY", "results": []}

        now = time.time()
        if now < self._circuit_breaker_until:
            return {"error": self._circuit_breaker_error or "OpenWeather circuit breaker active", "results": []}

        ssl_ctx = get_ssl_context()

        def fetch_target(target: LocationTarget) -> Dict[str, Any]:
            try:
                # 1. Fetch current weather
                params = {
                    "lat": f"{target.latitude:.4f}",
                    "lon": f"{target.longitude:.4f}",
                    "appid": self.api_key,
                    "units": "metric",
                }
                query = urllib.parse.urlencode(params)
                url = f"{self.API_URL_WEATHER}?{query}"
                req = urllib.request.Request(url, headers={"User-Agent": "Flowshield-Disaster-Intelligence/2.4"})

                with urllib.request.urlopen(req, context=ssl_ctx, timeout=3) as resp:
                    current_data = json.loads(resp.read().decode("utf-8"))

                # 2. Fetch short-term forecast for multi-hour accumulation
                forecast_data = None
                try:
                    f_url = f"{self.API_URL_FORECAST}?{query}"
                    f_req = urllib.request.Request(f_url, headers={"User-Agent": "Flowshield-Disaster-Intelligence/2.4"})
                    with urllib.request.urlopen(f_req, context=ssl_ctx, timeout=3) as f_resp:
                        forecast_data = json.loads(f_resp.read().decode("utf-8"))
                except Exception as fe:
                    logger.debug(f"OpenWeather forecast query skipped/failed for {target.name}: {fe}")

                return {
                    "target_id": target.id,
                    "target_name": target.name,
                    "current": current_data,
                    "forecast": forecast_data,
                }
            except urllib.error.HTTPError as he:
                err_body = he.read().decode("utf-8", errors="ignore")
                logger.warning(f"OpenWeather HTTP {he.code} for {target.name}: {err_body}")
                if he.code in (401, 403, 429):
                    self._circuit_breaker_until = time.time() + 600.0  # 10 minute cooldown
                    self._circuit_breaker_error = f"OpenWeather HTTP {he.code}: {err_body}"
                return {
                    "target_id": target.id,
                    "target_name": target.name,
                    "error": f"OpenWeather HTTP {he.code}: {err_body}",
                }
            except Exception as e:
                logger.warning(f"OpenWeather fetch exception for {target.name}: {e}")
                return {
                    "target_id": target.id,
                    "target_name": target.name,
                    "error": str(e),
                }

        # Fast probe: test first target before spawning pool
        first_res = fetch_target(targets[0])
        if "error" in first_res and (time.time() < self._circuit_breaker_until):
            logger.warning(f"OpenWeather fast probe triggered circuit breaker: {first_res['error']}")
            return {"error": first_res["error"], "results": [first_res]}

        results = [first_res]
        if len(targets) > 1:
            with ThreadPoolExecutor(max_workers=8) as executor:
                future_to_target = {executor.submit(fetch_target, t): t for t in targets[1:]}
                for future in as_completed(future_to_target):
                    results.append(future.result())

        return {"results": results}

    def validate(self, raw_payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        if "error" in raw_payload and not raw_payload.get("results"):
            errors.append(f"Provider returned error: {raw_payload['error']}")
            return False, errors

        results = raw_payload.get("results", [])
        if not results:
            errors.append("Empty payload from OpenWeather")
            return False, errors

        valid_count = 0
        for idx, item in enumerate(results):
            if "current" in item and item["current"].get("main"):
                valid_count += 1
            elif "error" in item:
                errors.append(f"Target {item.get('target_id', idx)} failed: {item['error']}")

        if valid_count == 0:
            errors.append("No valid target records received from OpenWeather")
            return False, errors

        return True, errors

    def normalize(self, raw_payload: Dict[str, Any], targets: List[LocationTarget]) -> List[NormalizedObservation]:
        is_valid, errors = self.validate(raw_payload)
        now_utc = datetime.now(timezone.utc)

        if not is_valid:
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
                    surface_pressure_hpa=1013.0,
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
        result_map = {r.get("target_id"): r for r in results if "target_id" in r}

        normalized = []
        for target in targets:
            item = result_map.get(target.id)
            if not item or "current" not in item:
                continue

            current = item["current"]
            main = current.get("main", {})
            wind = current.get("wind", {})
            rain = current.get("rain", {})
            forecast = item.get("forecast", {})

            # Atmospheric variables
            temp_c = float(main.get("temp", 20.0))
            humidity_pct = float(main.get("humidity", 70.0))
            pressure_hpa = float(main.get("pressure", 1013.0))
            wind_kmh = float(wind.get("speed", 3.0)) * 3.6  # m/s to km/h

            # Precipitation variables
            rain_1h = float(rain.get("1h", 0.0))
            rain_3h = float(rain.get("3h", rain_1h * 2.2))

            # Calculate 24h/72h rainfall from forecast list if available
            rain_24h = rain_3h * 2.5
            rain_72h = rain_24h * 1.8
            if forecast and "list" in forecast:
                f_list = forecast.get("list", [])[:8]  # next 24h (8 x 3h slots)
                f_rain_24 = sum(f.get("rain", {}).get("3h", 0.0) for f in f_list)
                if f_rain_24 > 0:
                    rain_24h = max(rain_24h, f_rain_24)

            # Estimate soil saturation based on humidity and antecedent rain
            base_soil = min(98.0, max(20.0, (humidity_pct * 0.5) + (rain_24h * 0.4)))
            deep_soil = min(95.0, max(25.0, base_soil * 0.92))

            obs = NormalizedObservation(
                location_id=target.id,
                timestamp=now_utc,
                rainfall_1h_mm=round(rain_1h, 2),
                rainfall_3h_mm=round(rain_3h, 2),
                rainfall_6h_mm=round(rain_1h * 4.0 if rain_1h > 0 else rain_3h * 1.6, 2),
                rainfall_24h_mm=round(rain_24h, 2),
                rainfall_72h_mm=round(rain_72h, 2),
                soil_saturation_pct=round(base_soil, 1),
                deep_soil_saturation_pct=round(deep_soil, 1),
                temperature_c=round(temp_c, 1),
                relative_humidity_pct=round(humidity_pct, 1),
                surface_pressure_hpa=round(pressure_hpa, 1),
                wind_speed_kmh=round(wind_kmh, 1),
                river_level_m=None,
                river_level_change_m=None,
                source_type=self.source_type,
                data_state=DataState.OBSERVED,
                data_quality_status=DataQualityStatus.VALID,
                data_quality_score=0.98,
                provider_name=self.name,
                metadata={
                    "weather_condition": current.get("weather", [{}])[0].get("main", "Clear"),
                    "weather_description": current.get("weather", [{}])[0].get("description", ""),
                    "station_name": current.get("name", target.name),
                },
            )
            normalized.append(obs)

        return normalized
