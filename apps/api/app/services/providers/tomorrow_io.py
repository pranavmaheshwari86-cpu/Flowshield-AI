"""
apps/api/app/services/providers/tomorrow_io.py
Flowshield — Tomorrow.io High-Resolution Weather & Nowcasting Provider (v2.5)
Fetches live atmospheric, precipitation nowcast (1-min), and 120-hour forecast telemetry.
"""

import json
import logging
import os
import time
import threading
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone

from .base import DataProvider, FreshnessPolicy, LocationTarget
from ...schemas.observation import NormalizedObservation, SourceType, DataState, DataQualityStatus
from ...config import settings
from ...utils.ssl_context import get_ssl_context

logger = logging.getLogger("flowshield.providers.tomorrow_io")


class TomorrowIOProvider(DataProvider):
    """
    Acquires hyper-local real-time atmospheric, minutely precipitation nowcast (0-60 min),
    and hourly precipitation forecasts (up to 120h) from Tomorrow.io Weather API v4.
    
    Includes:
    - Persistent disk & memory caching (15-min TTL) to protect the 25 calls/hour free tier quota
    - Inter-call pacing (min 0.4s) to respect the 3 req/sec burst limit
    - Resilient 429 backoff with automatic cache serving
    """

    BASE_URL = "https://api.tomorrow.io/v4"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (
            api_key
            or getattr(settings, "TOMORROW_API_KEY", "")
            or os.getenv("TOMORROW_API_KEY", "")
        ).strip()
        self.base_url = (
            getattr(settings, "TOMORROW_API_BASE_URL", "")
            or os.getenv("TOMORROW_API_BASE_URL", self.BASE_URL)
        ).rstrip("/")

        # Caching configuration (15-min TTL)
        self.cache_dir = Path("scratch")
        self.cache_file = self.cache_dir / "tomorrow_cache.json"
        self._cached_payloads: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl_sec = 900  # 15 minutes

        # Rate Limiting & Health state
        self._lock = threading.Lock()
        self._min_request_interval = 0.4  # seconds between calls (max 2.5 req/s < 3 req/s limit)
        self._last_request_time = 0.0
        self._rate_limited_until = 0.0
        self._rate_limit_error: Optional[str] = None

        self._load_cache_from_disk()

    @property
    def name(self) -> str:
        return "Tomorrow.io High-Resolution Nowcasting API"

    @property
    def source_type(self) -> SourceType:
        return SourceType.AUTOMATED_STATION

    def freshness_policy(self) -> FreshnessPolicy:
        # Tomorrow.io nowcasts update rapidly; nominal 15 min, stale after 1 hour
        return FreshnessPolicy(
            expected_update_interval_sec=900,
            stale_after_sec=3600,
            hard_expiry_sec=21600,
        )

    def provenance(self) -> Dict[str, Any]:
        return {
            "provider": "Tomorrow.io (ClimaCell) Weather Intelligence",
            "source_models": [
                "Proprietary Radar Assimilation",
                "Cellular Network Wireless Signal Attenuation",
                "High-Resolution NWP Models",
            ],
            "citation": "Tomorrow.io Weather API v4",
            "spatial_resolution": "Hyper-local point / 1km precipitation nowcast",
            "temporal_resolution": "1-minute nowcast (0-60 min) / 1-hour forecast (120 hr)",
            "license": "Commercial / Tomorrow.io Developer License",
            "is_synthetic": False,
        }

    def _load_cache_from_disk(self):
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._cached_payloads = json.load(f)
                logger.info(f"Loaded {len(self._cached_payloads)} cached Tomorrow.io locations from disk.")
        except Exception as e:
            logger.debug(f"Could not load Tomorrow.io disk cache: {e}")

    def _save_cache_to_disk(self):
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cached_payloads, f)
        except Exception as e:
            logger.debug(f"Could not save Tomorrow.io disk cache: {e}")

    def _pace_request(self):
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_request_interval:
                time.sleep(self._min_request_interval - elapsed)
            self._last_request_time = time.time()

    def health(self) -> bool:
        """Lightweight health check against Tomorrow.io realtime endpoint."""
        if not self.api_key:
            return False
        try:
            test_url = f"{self.base_url}/weather/realtime?location=31.70,76.93&apikey={self.api_key}&units=metric"
            req = urllib.request.Request(test_url, headers={"User-Agent": "Flowshield-Disaster-Intelligence/2.5"})
            with urllib.request.urlopen(req, context=get_ssl_context(), timeout=5) as resp:
                return resp.status == 200
        except urllib.error.HTTPError as he:
            # 429 proves the API key is authenticated and valid, but currently throttled by rate limit window
            if he.code == 429:
                return True
            logger.debug(f"Tomorrow.io health check HTTP error {he.code}: {he}")
            return False
        except Exception as e:
            logger.debug(f"Tomorrow.io health check failed: {e}")
            return False


    def fetch_target(self, target: LocationTarget) -> Dict[str, Any]:
        """Fetches forecast & minutely nowcast for a single target, with caching and rate limit defense."""
        now = time.time()
        cache_key = f"{round(target.latitude, 2):.2f}_{round(target.longitude, 2):.2f}"


        # 1. Check in-memory / disk cache (15-min TTL)
        cached = self._cached_payloads.get(cache_key)
        if cached and (now - cached.get("cached_at", 0)) < self._cache_ttl_sec:
            payload = cached.get("data", {})
            return {
                "target_id": target.id,
                "target_name": target.name,
                "data": payload,
                "from_cache": True,
            }

        # 2. Check if currently under 429 rate limit backoff
        if not self.api_key:
            return {
                "target_id": target.id,
                "target_name": target.name,
                "error": "Missing TOMORROW_API_KEY",
            }

        if now < self._rate_limited_until:
            if cached:
                return {
                    "target_id": target.id,
                    "target_name": target.name,
                    "data": cached.get("data", {}),
                    "from_cache": True,
                    "warning": "Served from stale cache due to Tomorrow.io rate limiting",
                }
            return {
                "target_id": target.id,
                "target_name": target.name,
                "error": self._rate_limit_error or "Tomorrow.io rate limit reached (backoff active)",
            }

        # 3. Perform paced outbound request
        self._pace_request()
        params = {
            "location": f"{target.latitude:.4f},{target.longitude:.4f}",
            "timesteps": "1m,1h,1d",
            "units": "metric",
            "apikey": self.api_key,
        }
        url = f"{self.base_url}/weather/forecast?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Flowshield-Disaster-Intelligence/2.5"})

        try:
            with urllib.request.urlopen(req, context=get_ssl_context(), timeout=7) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8"))
                    self._cached_payloads[cache_key] = {"data": payload, "cached_at": now}
                    self._save_cache_to_disk()
                    return {
                        "target_id": target.id,
                        "target_name": target.name,
                        "data": payload,
                        "from_cache": False,
                    }
                return {
                    "target_id": target.id,
                    "target_name": target.name,
                    "error": f"Tomorrow.io HTTP {resp.status}",
                }
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            logger.warning(f"Tomorrow.io HTTP {he.code} for {target.name}: {err_body}")
            if he.code == 429:
                self._rate_limited_until = time.time() + 180.0  # 3-minute backoff
                self._rate_limit_error = "Tomorrow.io rate limit reached (25 req/hr or 3 req/s). Retrying later."
                if cached:
                    return {
                        "target_id": target.id,
                        "target_name": target.name,
                        "data": cached.get("data", {}),
                        "from_cache": True,
                        "warning": "Served from cache due to 429 rate limit",
                    }
                return {
                    "target_id": target.id,
                    "target_name": target.name,
                    "error": self._rate_limit_error,
                }
            elif he.code in (401, 403):
                return {
                    "target_id": target.id,
                    "target_name": target.name,
                    "error": "Tomorrow.io API authentication error (invalid key)",
                }
            return {
                "target_id": target.id,
                "target_name": target.name,
                "error": f"Tomorrow.io HTTP {he.code}: {err_body}",
            }
        except Exception as e:
            logger.warning(f"Tomorrow.io connection exception for {target.name}: {e}")
            if cached:
                return {
                    "target_id": target.id,
                    "target_name": target.name,
                    "data": cached.get("data", {}),
                    "from_cache": True,
                }
            return {
                "target_id": target.id,
                "target_name": target.name,
                "error": str(e),
            }

    def fetch(self, targets: List[LocationTarget]) -> Dict[str, Any]:
        if not targets:
            return {"results": []}

        if not self.api_key:
            return {"error": "Missing TOMORROW_API_KEY", "results": []}

        results = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_target = {executor.submit(self.fetch_target, t): t for t in targets}
            for future in as_completed(future_to_target):
                results.append(future.result())

        return {"results": results}

    def validate(self, raw_payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        if "error" in raw_payload and not raw_payload.get("results"):
            errors.append(f"Provider error: {raw_payload['error']}")
            return False, errors

        results = raw_payload.get("results", [])
        if not results:
            errors.append("Empty payload from Tomorrow.io")
            return False, errors

        valid_count = 0
        for idx, item in enumerate(results):
            if "data" in item and item["data"].get("timelines"):
                valid_count += 1
            elif "error" in item:
                errors.append(f"Target {item.get('target_id', idx)} failed: {item['error']}")

        if valid_count == 0:
            errors.append("No valid timeline records received from Tomorrow.io")
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
            if not item or "data" not in item:
                continue

            data = item["data"]
            timelines = data.get("timelines", {})
            hourly = timelines.get("hourly", [])
            minutely = timelines.get("minutely", [])
            daily = timelines.get("daily", [])

            # Determine base real-time values (prefer 1st minutely entry, fallback to 1st hourly)
            base_values = {}
            if minutely and "values" in minutely[0]:
                base_values = minutely[0]["values"]
            elif hourly and "values" in hourly[0]:
                base_values = hourly[0]["values"]

            temp_c = float(base_values.get("temperature", 20.0))
            humidity_pct = float(base_values.get("humidity", 70.0))
            pressure_hpa = float(base_values.get("pressureSurfaceLevel") or base_values.get("pressureSeaLevel") or 1013.0)
            wind_kmh = float(base_values.get("windSpeed", 2.0)) * 3.6  # m/s to km/h

            # Precipitation rates and accumulation
            rain_1h = float(base_values.get("rainIntensity", 0.0))
            if rain_1h == 0.0 and hourly:
                rain_1h = float(hourly[0].get("values", {}).get("rainAccumulation", 0.0))

            rain_3h = sum(float(h.get("values", {}).get("rainAccumulation", 0.0)) for h in hourly[:3])
            rain_6h = sum(float(h.get("values", {}).get("rainAccumulation", 0.0)) for h in hourly[:6])
            rain_24h = sum(float(h.get("values", {}).get("rainAccumulation", 0.0)) for h in hourly[:24])
            rain_72h = sum(float(h.get("values", {}).get("rainAccumulation", 0.0)) for h in hourly[:72])

            if rain_3h == 0.0 and rain_1h > 0.0:
                rain_3h = rain_1h * 2.5
            if rain_24h == 0.0 and daily:
                rain_24h = float(daily[0].get("values", {}).get("rainAccumulationSum", rain_3h * 2.0))
            if rain_72h == 0.0:
                rain_72h = rain_24h * 1.8

            # Soil saturation approximation based on humidity & antecedent accumulation
            base_soil = min(98.0, max(20.0, (humidity_pct * 0.5) + (rain_24h * 0.4)))
            deep_soil = min(95.0, max(25.0, base_soil * 0.92))

            # Extract 1-minute nowcast timeline for next 60 minutes
            nowcast_summary = [
                {
                    "time": m.get("time"),
                    "rain_intensity_mmh": float(m.get("values", {}).get("rainIntensity", 0.0)),
                    "precip_prob_pct": float(m.get("values", {}).get("precipitationProbability", 0.0)),
                }
                for m in minutely[:60]
            ]

            weather_code = base_values.get("weatherCode", 1000)

            obs = NormalizedObservation(
                location_id=target.id,
                timestamp=now_utc,
                rainfall_1h_mm=round(rain_1h, 2),
                rainfall_3h_mm=round(rain_3h, 2),
                rainfall_6h_mm=round(rain_6h, 2),
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
                data_quality_score=0.99,
                provider_name=self.name,
                metadata={
                    "weather_code": weather_code,
                    "station_name": target.name,
                    "from_cache": item.get("from_cache", False),
                    "nowcast_points": len(nowcast_summary),
                    "nowcast_preview": nowcast_summary[:10],
                },
            )
            normalized.append(obs)

        return normalized
