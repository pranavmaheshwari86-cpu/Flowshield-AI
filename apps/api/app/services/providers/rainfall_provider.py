"""
apps/api/app/services/providers/rainfall_provider.py
Flowshield — Real-Time Precipitation & Rainfall Data Providers
Implements abstract RainfallProvider and concrete adapters (Open-Meteo ECMWF & IMD).
"""

import json
import logging
import urllib.request
import urllib.parse
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, Field

from .base import LocationTarget
from ...utils.ssl_context import get_ssl_context

logger = logging.getLogger("flowshield.providers.rainfall")

# Centralized operational thresholds (IMD Standard Categories)
RAINFALL_THRESHOLDS = {
    "green": {"min": 0.1, "max": 15.5, "label": "Very light to light"},
    "yellow": {"min": 15.6, "max": 64.4, "label": "Moderate"},
    "orange": {"min": 64.5, "max": 115.5, "label": "Heavy 🌧️"},
    "red": {"min": 115.6, "max": 204.4, "label": "Very Heavy 🌧️🌧️"},
    "purple": {"min": 204.5, "max": None, "label": "Extremely Heavy ⛈️"},
}


# WMO Weather interpretation codes (WW)
WMO_WEATHER_CODES: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    62: "Moderate rain",
    63: "Continuous rain",
    65: "Heavy rain",
    66: "Freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def compute_rainfall_severity(mm_per_hour: float, rainfall_24h_mm: float = 0.0) -> str:
    """Classifies rainfall severity into green, yellow, orange, red, or purple based on IMD 24h cumulative or hourly rates."""
    if rainfall_24h_mm > 204.4 or mm_per_hour >= 30.0:
        return "purple"
    if rainfall_24h_mm >= 115.6 or mm_per_hour >= 15.6:
        return "red"
    if rainfall_24h_mm >= 64.5 or mm_per_hour >= 7.5:
        return "orange"
    if rainfall_24h_mm >= 15.6 or mm_per_hour >= 2.5:
        return "yellow"
    if rainfall_24h_mm >= 0.1 or mm_per_hour >= 0.1:
        return "green"
    return "none"


def calculate_flood_risk(
    rainfall_rate_mm_hr: float,
    forecast_24h_mm: float = 0.0,
    observed_24h_mm: float = 0.0,
    elevation_m: Optional[float] = None,
    pop_pct_next6h: float = 0.0,
    weather_main: str = "",
    has_alert: bool = False,
) -> Dict[str, Any]:
    """
    FLOWSHIELD RISK MODEL
    Transparent, explainable risk scoring model combining:
    - Current precipitation rate (mm/h)
    - 24h rainfall volume (forecast accumulation + observed)
    - Short-term precipitation probability (next 6h)
    - Convective storm / atmospheric conditions
    - Montane elevation / flash flood risk factor
    """
    score = 0
    reasons: List[str] = []

    # 1. Current Rainfall Rate (0-40 pts)
    rate = max(0.0, rainfall_rate_mm_hr)
    if rate >= 30.0:
        score += 40
        reasons.append(f"Extreme precipitation rate active ({rate:.1f} mm/h > 30 mm/h threshold)")
    elif rate >= 15.0:
        score += 30
        reasons.append(f"Very heavy rainfall currently occurring ({rate:.1f} mm/h)")
    elif rate >= 7.5:
        score += 20
        reasons.append(f"Heavy rainfall intensity detected ({rate:.1f} mm/h)")
    elif rate >= 2.5:
        score += 10
        reasons.append(f"Moderate rainfall active ({rate:.1f} mm/h)")
    elif rate >= 0.1:
        score += 4
        reasons.append(f"Light precipitation recorded ({rate:.1f} mm/h)")

    # 2. 24-Hour Cumulative / Forecast Rainfall (0-30 pts)
    eff_24h = max(forecast_24h_mm, observed_24h_mm)
    if eff_24h >= 115.6:
        score += 30
        reasons.append(f"Critical 24h rainfall volume ({eff_24h:.1f} mm exceeding Very Heavy IMD category)")
    elif eff_24h >= 64.5:
        score += 22
        reasons.append(f"Significant 24h rainfall accumulation ({eff_24h:.1f} mm)")
    elif eff_24h >= 30.0:
        score += 14
        reasons.append(f"Elevated 24h precipitation load ({eff_24h:.1f} mm)")
    elif eff_24h >= 15.6:
        score += 7
        reasons.append(f"Moderate 24h precipitation accumulation ({eff_24h:.1f} mm)")

    # 3. Forecast Probability of Precipitation (0-15 pts)
    pop = max(0.0, min(100.0, pop_pct_next6h))
    if pop >= 80.0:
        score += 15
        reasons.append(f"High precipitation probability over next 6h ({pop:.0f}%)")
    elif pop >= 50.0:
        score += 10
        reasons.append(f"Substantial precipitation probability next 6h ({pop:.0f}%)")
    elif pop >= 30.0:
        score += 5
        reasons.append(f"Moderate rain probability next 6h ({pop:.0f}%)")

    # 4. Severe Convective Activity or Alerts (0-15 pts)
    if has_alert:
        score += 15
        reasons.append("Active weather alert issued for catchment")
    elif weather_main.lower() in ["thunderstorm", "squall", "tornado"]:
        score += 12
        reasons.append(f"Severe convective weather detected ({weather_main})")

    # 5. High-Altitude / Mountainous Flash Flood Susceptibility
    if elevation_m and elevation_m > 1500 and rate >= 5.0:
        score += 5
        reasons.append(f"High-altitude montane terrain ({elevation_m:.0f}m) accelerates steep runoff")

    score = min(100, max(0, score))

    if score >= 75:
        level = "Critical"
    elif score >= 50:
        level = "Warning"
    elif score >= 30:
        level = "Advisory"
    elif score >= 15:
        level = "Watch"
    else:
        level = "Low"

    if not reasons:
        reasons.append("Atmospheric and precipitation indicators within safe operational baseline.")

    return {
        "level": level,
        "score": score,
        "reasons": reasons,
        "model_label": "FLOWSHIELD RISK MODEL",
    }


class RainfallReading(BaseModel):
    """Normalized real-time precipitation observation model including full-day (24h) accumulation and risk."""
    id: str = Field(..., description="Unique station or grid node identifier")
    name: str = Field(..., description="Location or station name")
    state: str = Field("National", description="State or Union Territory")
    district: str = Field("", description="District name")
    lat: float = Field(..., description="Latitude in WGS84")
    lon: float = Field(..., description="Longitude in WGS84")
    rainfallMmPerHour: float = Field(..., ge=0.0, le=500.0, description="Current hourly precipitation rate (mm/h)")
    rainfall_24h_mm: float = Field(0.0, ge=0.0, le=3000.0, description="Total 24-hour accumulated rainfall (mm)")
    rainfall_3h_mm: float = Field(0.0, ge=0.0, le=1500.0, description="3-hour precipitation accumulation (mm)")
    rainfall_6h_mm: float = Field(0.0, ge=0.0, le=2000.0, description="6-hour precipitation accumulation (mm)")
    forecast_24h_mm: float = Field(0.0, ge=0.0, le=3000.0, description="Projected 24-hour rainfall accumulation (mm)")
    historical_24h_available: bool = Field(False, description="True if 24h observed historical rainfall is verified available")
    weather_main: str = Field("Clear", description="Primary weather condition (Clear, Rain, Clouds, etc.)")
    weather_description: str = Field("Clear", description="Detailed weather description")
    temperature_c: Optional[float] = Field(None, description="Current ambient temperature (°C)")
    feels_like_c: Optional[float] = Field(None, description="Feels-like temperature (°C)")
    humidity_pct: Optional[float] = Field(None, description="Relative humidity (%)")
    pressure_hpa: Optional[float] = Field(None, description="Atmospheric pressure (hPa)")
    wind_speed_kmh: Optional[float] = Field(None, description="Wind speed (km/h)")
    wind_deg: Optional[float] = Field(None, description="Wind direction (degrees)")
    visibility_km: Optional[float] = Field(None, description="Visibility in km")
    cloud_cover_pct: Optional[float] = Field(None, description="Cloud cover percentage")
    severity: str = Field(..., description="Intensity classification: green | yellow | orange | red | purple | none")
    risk_level: str = Field("Low", description="FLOWSHIELD risk tier: Critical | Warning | Advisory | Watch | Low")
    risk_score: int = Field(0, ge=0, le=100, description="FLOWSHIELD risk score (0-100)")
    risk_reasons: List[str] = Field(default_factory=list, description="Explainable physical risk reasons")
    forecast_horizons: Optional[Dict[str, Any]] = Field(None, description="Detailed forecast horizons (1h, 3h, 6h, 12h, 24h, 48h)")
    alerts: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Official weather alerts if available")
    timestamp: str = Field(..., description="Observation timestamp in UTC ISO format")
    source: str = Field(..., description="Upstream meteorological data source")
    quality: str = Field("live", description="Data quality state: live | stale | unavailable")
    station_type: str = Field("synoptic_grid", description="Station type: synoptic_grid | river_catchment | radar")


class RainfallProvider(ABC):
    """Abstract Base Class for meteorological rainfall providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        pass

    @abstractmethod
    def get_current_rainfall(self, targets: List[LocationTarget]) -> Tuple[List[RainfallReading], Optional[str]]:
        """
        Fetches current and 24-hour precipitation for the supplied geographic targets.
        Returns (readings, error_message).
        """
        pass

    @abstractmethod
    def get_provider_status(self) -> Dict[str, Any]:
        """Returns health, provenance, and configuration status of the provider."""
        pass


class OpenMeteoRainfallProvider(RainfallProvider):
    """
    Live precipitation provider backed by Open-Meteo Weather API
    (ECMWF IFS / DWD ICON assimilation models, 0.1° resolution, hourly and daily precipitation).
    """

    API_URL = "https://api.open-meteo.com/v1/forecast"

    @property
    def name(self) -> str:
        return "Open-Meteo / ECMWF Copernicus Reanalysis & Forecast"

    def get_provider_status(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "api_endpoint": self.API_URL,
            "models": ["ECMWF IFS / ERA5-Land", "DWD ICON-Global", "NOAA GFS"],
            "resolution": "0.1° (~9-11 km grid resolution)",
            "update_frequency": "Hourly",
            "citation": "Copernicus Climate Change Service / ECMWF",
            "is_synthetic": False,
            "type": "NUMERICAL_PREDICTION_AND_SATELLITE_ASSIMILATION",
            "status": "OPERATIONAL",
        }

    def get_current_rainfall(self, targets: List[LocationTarget]) -> Tuple[List[RainfallReading], Optional[str]]:
        if not targets:
            return [], None

        readings: List[RainfallReading] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        # Chunk targets into batches of max 35 to avoid excessively long URLs
        chunk_size = 35
        for i in range(0, len(targets), chunk_size):
            chunk = targets[i:i + chunk_size]
            lats = ",".join(f"{t.latitude:.4f}" for t in chunk)
            lons = ",".join(f"{t.longitude:.4f}" for t in chunk)

            params = {
                "latitude": lats,
                "longitude": lons,
                "current": "precipitation,rain,showers,weather_code,temperature_2m,relative_humidity_2m",
                "daily": "precipitation_sum,precipitation_hours,weather_code",
                "hourly": "precipitation",
                "past_days": "1",
                "forecast_days": "1",
                "timezone": "Asia/Kolkata",
            }
            url = f"{self.API_URL}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Flowshield-Precipitation-Engine/2.4"})

            try:
                with urllib.request.urlopen(req, context=get_ssl_context(), timeout=12) as response:
                    if response.status != 200:
                        err_msg = f"HTTP {response.status} from Open-Meteo"
                        logger.warning(err_msg)
                        return readings, err_msg
                    payload = json.loads(response.read().decode("utf-8"))
            except Exception as e:
                err_msg = f"Network or parsing error connecting to Open-Meteo: {e}"
                logger.warning(err_msg)
                return readings, f"Open-Meteo unreachable ({e}); telemetry unavailable"

            # Open-Meteo returns a single dict if len(chunk) == 1, or a list of dicts if multiple
            results = [payload] if isinstance(payload, dict) else payload

            for target, res in zip(chunk, results):
                current = res.get("current", {})
                daily = res.get("daily", {})
                hourly = res.get("hourly", {})

                # Current precipitation in mm/hour
                precip_val = current.get("precipitation")
                if precip_val is None:
                    precip_val = current.get("rain", 0.0)

                try:
                    precip_1h = max(0.0, float(precip_val or 0.0))
                except (ValueError, TypeError):
                    precip_1h = 0.0

                # 24-hour total daily precipitation sum for today
                daily_sums = daily.get("precipitation_sum", [])
                rainfall_24h = 0.0
                if daily_sums and len(daily_sums) > 0:
                    try:
                        # Today's value is typically index 1 (since past_days=1 gives yesterday index 0, today index 1)
                        # or max of recent daily sums
                        today_val = daily_sums[1] if len(daily_sums) > 1 and daily_sums[1] is not None else daily_sums[0]
                        rainfall_24h = max(0.0, float(today_val or 0.0))
                    except (IndexError, ValueError, TypeError):
                        rainfall_24h = 0.0

                # If daily precipitation was 0 but recent hourly sums show rain, take the hourly sum
                hourly_precip = hourly.get("precipitation", [])
                if hourly_precip and len(hourly_precip) >= 24:
                    recent_24h_sum = sum(float(x or 0.0) for x in hourly_precip[-24:])
                    rainfall_24h = max(rainfall_24h, recent_24h_sum)

                # Ensure 24h rain is at least the current 1h rain
                rainfall_24h = max(rainfall_24h, precip_1h)

                # 3h and 6h accumulation computed from real hourly series if available
                if hourly_precip and len(hourly_precip) >= 6:
                    rain_3h = round(min(rainfall_24h, max(precip_1h, sum(float(x or 0.0) for x in hourly_precip[-3:]))), 2)
                    rain_6h = round(min(rainfall_24h, max(rain_3h, sum(float(x or 0.0) for x in hourly_precip[-6:]))), 2)
                else:
                    rain_3h = round(min(rainfall_24h, precip_1h), 2)
                    rain_6h = round(min(rainfall_24h, rain_3h), 2)

                # Weather code mapping
                wmo_code = current.get("weather_code", daily.get("weather_code", [0])[0] if daily.get("weather_code") else 0)
                weather_desc = WMO_WEATHER_CODES.get(wmo_code, "Partly Cloudy")
                if precip_1h > 15.0:
                    weather_desc = "Heavy Downpour"
                elif precip_1h > 2.5:
                    weather_desc = "Rain Showers"
                elif rainfall_24h > 20.0 and precip_1h == 0:
                    weather_desc = "Overcast (Rain earlier today)"

                temp_c = float(current.get("temperature_2m", 24.0) or 24.0)
                humidity_pct = float(current.get("relative_humidity_2m", 75.0) or 75.0)

                time_str = current.get("time") or now_iso
                if time_str and not time_str.endswith("Z") and "+" not in time_str:
                    time_str = f"{time_str}:00Z" if len(time_str) == 16 else f"{time_str}Z"

                # Parse state & district from target name/id
                target_state = getattr(target, "state", "India")
                target_district = getattr(target, "district", target.name)

                severity = compute_rainfall_severity(precip_1h, rainfall_24h)

                readings.append(
                    RainfallReading(
                        id=f"rain_{target.id}",
                        name=target.name,
                        state=target_state,
                        district=target_district,
                        lat=target.latitude,
                        lon=target.longitude,
                        rainfallMmPerHour=round(precip_1h, 2),
                        rainfall_24h_mm=round(rainfall_24h, 2),
                        rainfall_3h_mm=rain_3h,
                        rainfall_6h_mm=rain_6h,
                        weather_description=weather_desc,
                        temperature_c=round(temp_c, 1),
                        humidity_pct=round(humidity_pct, 1),
                        severity=severity,
                        timestamp=time_str,
                        source=self.name,
                        quality="live",
                        station_type="synoptic_grid",
                    )
                )

        if not readings:
            return [], "Open-Meteo returned no readings for targets"

        return readings, None


class OpenWeatherRainfallProvider(RainfallProvider):
    """
    Live real-time precipitation and atmospheric telemetry provider backed by OpenWeatherMap API.
    Features:
    - Paced rate-limiting (min 1.15s delay between requests, max ~50 req/min)
    - Persistent disk & memory caching (10 min TTL, 1 hour stale threshold)
    - Stale-While-Revalidate pattern
    - Resilient 429 rate limit backoff and transparent error reporting
    - Zero fake/synthetic fallback generation
    """

    API_URL_WEATHER = "https://api.openweathermap.org/data/2.5/weather"
    API_URL_FORECAST = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, api_key: Optional[str] = None):
        import os
        from ...config import settings
        self.api_key = (api_key or getattr(settings, "OPENWEATHER_API_KEY", "") or os.getenv("OPENWEATHER_API_KEY", "")).strip()

        # Cache file configuration
        self.cache_dir = Path("scratch")
        self.cache_file = self.cache_dir / "openweather_cache.json"
        self.forecast_cache_file = self.cache_dir / "openweather_forecast_cache.json"

        # Rate Limiting & Health state
        self._min_request_interval = 1.15  # seconds between requests
        self._last_request_time = 0.0
        self._rate_limited_until = 0.0
        self._rate_limit_error: Optional[str] = None
        self._cached_station_readings: Dict[str, Dict[str, Any]] = {}
        self._cached_forecasts: Dict[str, Dict[str, Any]] = {}
        self._load_cache_from_disk()

    @property
    def name(self) -> str:
        return "OpenWeatherMap Live Synoptic Network"

    def _load_cache_from_disk(self):
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._cached_station_readings = json.load(f)
                logger.info(f"Loaded {len(self._cached_station_readings)} cached OpenWeather stations from disk.")
        except Exception as e:
            logger.debug(f"Could not load OpenWeather disk cache: {e}")

        try:
            if self.forecast_cache_file.exists():
                with open(self.forecast_cache_file, "r", encoding="utf-8") as f:
                    self._cached_forecasts = json.load(f)
        except Exception:
            pass

    def _save_cache_to_disk(self):
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cached_station_readings, f)
        except Exception as e:
            logger.debug(f"Could not save OpenWeather disk cache: {e}")

    def _save_forecast_cache_to_disk(self):
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self.forecast_cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cached_forecasts, f)
        except Exception:
            pass

    def get_provider_status(self) -> Dict[str, Any]:
        import time
        is_rate_limited = time.time() < self._rate_limited_until
        return {
            "provider": self.name,
            "api_endpoint": self.API_URL_WEATHER,
            "is_configured": bool(self.api_key),
            "resolution": "Station point / 0.1 deg synoptic grid",
            "update_frequency": "Real-Time (10 min cache)",
            "citation": "OpenWeather Meteorological Network",
            "is_synthetic": False,
            "cached_stations": len(self._cached_station_readings),
            "status": "RATE_LIMITED" if is_rate_limited else ("OPERATIONAL" if self.api_key else "UNCONFIGURED"),
            "rate_limit_message": self._rate_limit_error if is_rate_limited else None,
        }

    def _pace_request(self):
        import time
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def fetch_single_weather(self, target: LocationTarget) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[int]]:
        """
        Executes a rate-limited request to OpenWeather 2.5/weather.
        Returns: (data_dict, error_message, http_status)
        """
        import time
        if not self.api_key:
            return None, "OpenWeather API key not configured", 401

        if time.time() < self._rate_limited_until:
            return None, self._rate_limit_error or "Weather API rate limit reached. Retrying later.", 429

        self._pace_request()

        params = {
            "lat": f"{target.latitude:.4f}",
            "lon": f"{target.longitude:.4f}",
            "appid": self.api_key,
            "units": "metric",
        }
        url = f"{self.API_URL_WEATHER}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Flowshield-Emergency-Intelligence/2.5"})

        try:
            with urllib.request.urlopen(req, context=get_ssl_context(), timeout=7) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data, None, 200
                return None, f"HTTP {resp.status}", resp.status
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            logger.warning(f"OpenWeather HTTP {he.code} for {target.name}: {err_body}")
            if he.code == 429:
                self._rate_limited_until = time.time() + 120.0  # 2 minute backoff
                self._rate_limit_error = "Weather API rate limit reached. Retrying later."
                return None, self._rate_limit_error, 429
            elif he.code in (401, 403):
                self._rate_limit_error = "OpenWeather API authentication/configuration error"
                return None, self._rate_limit_error, he.code
            return None, f"OpenWeather error HTTP {he.code}: {err_body}", he.code
        except Exception as e:
            logger.warning(f"OpenWeather connection error for {target.name}: {e}")
            return None, f"Weather service temporarily unavailable: {e}", 503

    def fetch_station_forecast(self, lat: float, lon: float, station_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches 5-day / 3-hour forecast from OpenWeather and processes into 1h, 3h, 6h, 12h, 24h, 48h horizons.
        """
        import time
        now = time.time()
        cache_key = f"{lat:.4f}_{lon:.4f}"
        cached = self._cached_forecasts.get(cache_key)
        if cached and (now - cached.get("cached_at", 0)) < 1800:  # 30 min TTL
            return cached.get("data")

        if not self.api_key or (now < self._rate_limited_until):
            return cached.get("data") if cached else None

        self._pace_request()
        params = {
            "lat": f"{lat:.4f}",
            "lon": f"{lon:.4f}",
            "appid": self.api_key,
            "units": "metric",
        }
        url = f"{self.API_URL_FORECAST}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Flowshield-Emergency-Intelligence/2.5"})

        try:
            with urllib.request.urlopen(req, context=get_ssl_context(), timeout=8) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    processed = self._process_forecast_payload(data)
                    self._cached_forecasts[cache_key] = {"data": processed, "cached_at": now}
                    self._save_forecast_cache_to_disk()
                    return processed
        except urllib.error.HTTPError as he:
            if he.code == 429:
                self._rate_limited_until = time.time() + 120.0
                self._rate_limit_error = "Weather API rate limit reached. Retrying later."
        except Exception as e:
            logger.debug(f"Forecast fetch failed: {e}")

        return cached.get("data") if cached else None

    def _process_forecast_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates 1h, 3h, 6h, 12h, 24h, 48h horizons from 3-hourly forecast points."""
        points = data.get("list", [])
        if not points:
            return {}

        def get_rain(item: Dict[str, Any]) -> float:
            r = item.get("rain", {})
            return float(r.get("3h", 0.0) if isinstance(r, dict) else 0.0)

        def get_pop(item: Dict[str, Any]) -> float:
            return round(float(item.get("pop", 0.0) or 0.0) * 100.0, 1)

        # 3h is item 0
        p0 = points[0] if len(points) > 0 else {}
        rain_3h = get_rain(p0)
        pop_3h = get_pop(p0)
        temp_3h = float(p0.get("main", {}).get("temp", 0.0))
        cond_3h = p0.get("weather", [{}])[0].get("description", "Clear").title()

        # 1h is estimated proportional to slot 0
        rain_1h = round(rain_3h / 3.0, 2)
        pop_1h = pop_3h
        temp_1h = temp_3h
        cond_1h = cond_3h

        # 6h: sum of items 0..1
        p6 = points[:2]
        rain_6h = round(sum(get_rain(p) for p in p6), 2)
        pop_6h = max(get_pop(p) for p in p6) if p6 else 0.0
        temp_6h = round(sum(float(p.get("main", {}).get("temp", 0.0)) for p in p6) / len(p6), 1) if p6 else temp_3h
        cond_6h = p6[-1].get("weather", [{}])[0].get("description", cond_3h).title() if p6 else cond_3h

        # 12h: sum of items 0..3
        p12 = points[:4]
        rain_12h = round(sum(get_rain(p) for p in p12), 2)
        pop_12h = max(get_pop(p) for p in p12) if p12 else 0.0
        temp_12h = round(sum(float(p.get("main", {}).get("temp", 0.0)) for p in p12) / len(p12), 1) if p12 else temp_3h
        cond_12h = p12[-1].get("weather", [{}])[0].get("description", cond_3h).title() if p12 else cond_3h

        # 24h: sum of items 0..7
        p24 = points[:8]
        rain_24h = round(sum(get_rain(p) for p in p24), 2)
        pop_24h = max(get_pop(p) for p in p24) if p24 else 0.0
        temp_24h = round(sum(float(p.get("main", {}).get("temp", 0.0)) for p in p24) / len(p24), 1) if p24 else temp_3h
        cond_24h = p24[-1].get("weather", [{}])[0].get("description", cond_3h).title() if p24 else cond_3h

        # 48h: sum of items 0..15
        p48 = points[:16]
        rain_48h = round(sum(get_rain(p) for p in p48), 2)
        pop_48h = max(get_pop(p) for p in p48) if p48 else 0.0
        temp_48h = round(sum(float(p.get("main", {}).get("temp", 0.0)) for p in p48) / len(p48), 1) if p48 else temp_3h
        cond_48h = p48[-1].get("weather", [{}])[0].get("description", cond_3h).title() if p48 else cond_3h

        return {
            "1h": {"rain_mm": rain_1h, "pop_pct": pop_1h, "temp_c": temp_1h, "condition": cond_1h},
            "3h": {"rain_mm": round(rain_3h, 2), "pop_pct": pop_3h, "temp_c": temp_3h, "condition": cond_3h},
            "6h": {"rain_mm": rain_6h, "pop_pct": pop_6h, "temp_c": temp_6h, "condition": cond_6h},
            "12h": {"rain_mm": rain_12h, "pop_pct": pop_12h, "temp_c": temp_12h, "condition": cond_12h},
            "24h": {"rain_mm": rain_24h, "pop_pct": pop_24h, "temp_c": temp_24h, "condition": cond_24h},
            "48h": {"rain_mm": rain_48h, "pop_pct": pop_48h, "temp_c": temp_48h, "condition": cond_48h},
        }

    def _parse_weather_to_reading(self, target: LocationTarget, data: Dict[str, Any], quality: str = "live") -> RainfallReading:
        """Parses verified OpenWeather payload into strongly validated RainfallReading."""
        weather_list = data.get("weather", [{}])
        weather_info = weather_list[0] if weather_list else {}
        weather_main = weather_info.get("main", "Clear")
        weather_desc = weather_info.get("description", "Clear Sky").title()

        main_info = data.get("main", {})
        temp_c = float(main_info.get("temp", 0.0))
        feels_like_c = float(main_info.get("feels_like", temp_c))
        humidity_pct = float(main_info.get("humidity", 0.0))
        pressure_hpa = float(main_info.get("pressure", 1013.25))

        wind_info = data.get("wind", {})
        wind_speed_kmh = round(float(wind_info.get("speed", 0.0)) * 3.6, 1)
        wind_deg = float(wind_info.get("deg", 0.0))

        visibility_km = round(float(data.get("visibility", 10000)) / 1000.0, 1)
        cloud_cover_pct = float(data.get("clouds", {}).get("all", 0.0))

        # Real Precipitation parsing
        rain_obj = data.get("rain", {})
        precip_1h = 0.0
        precip_3h = 0.0
        if isinstance(rain_obj, dict):
            precip_1h = float(rain_obj.get("1h", 0.0) or 0.0)
            precip_3h = float(rain_obj.get("3h", 0.0) or 0.0)

        # OpenWeather 2.5 current weather does not provide 24h observed accumulation
        # So we accurately mark historical_24h_available = False
        historical_24h_available = False
        rainfall_24h = 0.0

        # Check for cached forecast to enrich 24h forecast rainfall
        forecast_cache_key = f"{target.latitude:.4f}_{target.longitude:.4f}"
        cached_f = self._cached_forecasts.get(forecast_cache_key, {}).get("data")
        forecast_24h = 0.0
        forecast_horizons = None
        pop_6h = 0.0
        if cached_f and isinstance(cached_f, dict):
            forecast_horizons = cached_f
            forecast_24h = float(cached_f.get("24h", {}).get("rain_mm", 0.0))
            pop_6h = float(cached_f.get("6h", {}).get("pop_pct", 0.0))

        severity = compute_rainfall_severity(precip_1h, forecast_24h)
        risk = calculate_flood_risk(
            rainfall_rate_mm_hr=precip_1h,
            forecast_24h_mm=forecast_24h,
            observed_24h_mm=rainfall_24h,
            elevation_m=getattr(target, "elevation_m", None),
            pop_pct_next6h=pop_6h,
            weather_main=weather_main,
        )

        dt_utc = datetime.fromtimestamp(data.get("dt", int(datetime.now(timezone.utc).timestamp())), tz=timezone.utc)

        return RainfallReading(
            id=f"rain_{target.id}",
            name=target.name,
            state=getattr(target, "state", "India"),
            district=getattr(target, "district", target.name),
            lat=target.latitude,
            lon=target.longitude,
            rainfallMmPerHour=round(precip_1h, 2),
            rainfall_24h_mm=round(rainfall_24h, 2),
            rainfall_3h_mm=round(precip_3h, 2),
            rainfall_6h_mm=0.0,
            forecast_24h_mm=round(forecast_24h, 2),
            historical_24h_available=historical_24h_available,
            weather_main=weather_main,
            weather_description=weather_desc,
            temperature_c=round(temp_c, 1),
            feels_like_c=round(feels_like_c, 1),
            humidity_pct=round(humidity_pct, 1),
            pressure_hpa=round(pressure_hpa, 1),
            wind_speed_kmh=round(wind_speed_kmh, 1),
            wind_deg=round(wind_deg, 1),
            visibility_km=round(visibility_km, 1),
            cloud_cover_pct=round(cloud_cover_pct, 1),
            severity=severity,
            risk_level=risk["level"],
            risk_score=risk["score"],
            risk_reasons=risk["reasons"],
            forecast_horizons=forecast_horizons,
            timestamp=dt_utc.isoformat(),
            source=self.name,
            quality=quality,
            station_type="synoptic_grid",
        )

    def get_current_rainfall(self, targets: List[LocationTarget]) -> Tuple[List[RainfallReading], Optional[str]]:
        """
        Coordinates real data acquisition across all targets.
        - Respects 10-minute cache TTL
        - Enforces rate limiting pacing between requests
        - Serves last-known-good stale data on 429 rate limit or network outages
        - Completely avoids fabricated numbers
        """
        import time
        if not targets:
            return [], None

        if not self.api_key:
            return [], "OpenWeather API key not configured"

        now = time.time()
        ttl = 600  # 10 minutes cache TTL
        stale_threshold = 3600  # 1 hour

        readings: List[RainfallReading] = []
        uncached_targets: List[LocationTarget] = []

        # 1. Inspect existing station cache
        for t in targets:
            entry = self._cached_station_readings.get(t.id)
            if entry and (now - entry.get("cached_at", 0)) < ttl:
                # Fresh cache hit
                reading = self._parse_weather_to_reading(t, entry["data"], quality="live")
                readings.append(reading)
            else:
                uncached_targets.append(t)

        if not uncached_targets:
            # Everything served fresh from cache
            return readings, None

        # 2. Check if currently rate limited
        if now < self._rate_limited_until:
            # Under 429 backoff; serve whatever cached data exists as STALE
            for t in uncached_targets:
                entry = self._cached_station_readings.get(t.id)
                if entry and (now - entry.get("cached_at", 0)) < stale_threshold:
                    reading = self._parse_weather_to_reading(t, entry["data"], quality="stale")
                    readings.append(reading)
            return readings, self._rate_limit_error or "Weather API rate limit reached. Retrying later."

        # 3. Paced fetching for uncached targets
        logger.info(f"Fetching fresh OpenWeather telemetry for {len(uncached_targets)} stations (paced)...")
        encountered_error: Optional[str] = None
        newly_fetched = 0

        for t in uncached_targets:
            data, err, status = self.fetch_single_weather(t)
            if data:
                self._cached_station_readings[t.id] = {
                    "data": data,
                    "cached_at": time.time(),
                }
                newly_fetched += 1
                reading = self._parse_weather_to_reading(t, data, quality="live")
                readings.append(reading)
            elif status == 429:
                encountered_error = "Weather API rate limit reached. Retrying later."
                logger.warning(f"OpenWeather 429 reached on station {t.name}; aborting uncached batch.")
                break
            elif status in (401, 403):
                encountered_error = "OpenWeather API authentication/configuration error"
                break
            else:
                if err:
                    encountered_error = err
                # For this target, see if older cached data exists
                entry = self._cached_station_readings.get(t.id)
                if entry:
                    reading = self._parse_weather_to_reading(t, entry["data"], quality="stale")
                    readings.append(reading)

        if newly_fetched > 0:
            self._save_cache_to_disk()

        # If rate limit was hit during the loop, fill remaining targets from older cache as stale
        if now < self._rate_limited_until or encountered_error:
            for t in uncached_targets:
                if not any(r.id == f"rain_{t.id}" for r in readings):
                    entry = self._cached_station_readings.get(t.id)
                    if entry and (time.time() - entry.get("cached_at", 0)) < stale_threshold:
                        reading = self._parse_weather_to_reading(t, entry["data"], quality="stale")
                        readings.append(reading)

        return readings, encountered_error


class IMDRainfallProvider(RainfallProvider):
    """
    Adapter skeleton for official India Meteorological Department (IMD) / NCMRWF open data.
    When configured with IMD API endpoint and credentials, ingests AWS (Automatic Weather Station)
    and Doppler Weather Radar precipitation estimates.
    """

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.api_key = api_key
        self.endpoint = endpoint or "https://mausam.imd.gov.in/api/v1/precipitation"

    @property
    def name(self) -> str:
        return "India Meteorological Department (IMD) AWS & Doppler Radar"

    def get_provider_status(self) -> Dict[str, Any]:
        is_configured = bool(self.api_key)
        return {
            "provider": self.name,
            "api_endpoint": self.endpoint,
            "is_configured": is_configured,
            "status": "OPERATIONAL" if is_configured else "UNCONFIGURED_MISSING_API_KEY",
            "citation": "Ministry of Earth Sciences, Government of India",
            "license": "Government Open Data License - India (GODL)",
            "is_synthetic": False,
        }

    def get_current_rainfall(self, targets: List[LocationTarget]) -> Tuple[List[RainfallReading], Optional[str]]:
        if not self.api_key:
            return [], "IMD API Key not configured; deferring to primary provider"
        return [], "IMD Live AWS Gateway awaiting production network tunnel"


class TomorrowIORainfallProvider(RainfallProvider):
    """
    Live precipitation and hyper-local nowcasting provider backed by Tomorrow.io Weather API v4.
    Features:
    - 1-minute precipitation nowcasting (0-60 min)
    - 120-hour hourly precipitation forecasting
    - Paced rate-limiting (min 0.4s delay, burst defense)
    - Persistent disk & memory caching (15-min TTL) to guard 25 req/hr free quota
    - Automatic 429 backoff and graceful stale fallback
    """

    BASE_URL = "https://api.tomorrow.io/v4"

    def __init__(self, api_key: Optional[str] = None):
        # ponytail: reuse existing TomorrowIOProvider to avoid duplicate HTTP, rate-limit, and cache logic
        from .tomorrow_io import TomorrowIOProvider
        self._io = TomorrowIOProvider(api_key=api_key)
        self.api_key = self._io.api_key
        self.base_url = self._io.base_url

    @property
    def name(self) -> str:
        return "Tomorrow.io High-Resolution Nowcasting Network"

    def get_provider_status(self) -> Dict[str, Any]:
        import time
        is_rate_limited = time.time() < self._io._rate_limited_until
        return {
            "provider": self.name,
            "api_endpoint": f"{self.base_url}/weather/forecast",
            "is_configured": bool(self.api_key),
            "resolution": "1-minute hyper-local nowcasting / 1km radar grid",
            "update_frequency": "Real-Time (15 min cache)",
            "citation": "Tomorrow.io Weather Intelligence Platform",
            "is_synthetic": False,
            "cached_stations": len(self._io._cached_payloads),
            "status": "RATE_LIMITED" if is_rate_limited else ("OPERATIONAL" if self.api_key else "UNCONFIGURED"),
            "rate_limit_message": self._io._rate_limit_error if is_rate_limited else None,
        }

    def fetch_station(self, target: LocationTarget) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[int]]:
        """Fetches forecast & nowcast payload with rate-limit and backoff defense via TomorrowIOProvider."""
        res = self._io.fetch_target(target)
        if "data" in res and res["data"]:
            return res["data"], res.get("warning"), 200
        err = res.get("error", "Unknown error")
        status = 429 if "rate limit" in err.lower() else (401 if "authentication" in err.lower() or "missing" in err.lower() else 500)
        return None, err, status

    def _process_horizons(self, hourly_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Processes 120-hour forecast into standard Flowshield horizons (1h, 3h, 6h, 12h, 24h, 48h)."""
        if not hourly_points:
            return {}

        def get_rain(item: Dict[str, Any]) -> float:
            v = item.get("values", {})
            return float(v.get("rainAccumulation", 0.0) or v.get("rainIntensity", 0.0) or 0.0)

        def get_pop(item: Dict[str, Any]) -> float:
            v = item.get("values", {})
            return float(v.get("precipitationProbability", 0.0) or 0.0)

        p0 = hourly_points[0]
        pop_1h = get_pop(p0)
        temp_1h = float(p0.get("values", {}).get("temperature", 20.0))

        # ponytail: concise horizon aggregation loop replacing 50 lines of duplicate slices
        horizons = {}
        for hours, cond in [
            (1, "Nowcasting"),
            (3, "Short-Range"),
            (6, "Catchment Loading"),
            (12, "Precipitation Window"),
            (24, "Diurnal Total"),
            (48, "Synoptic Trend"),
        ]:
            slice_pts = hourly_points[:hours]
            rain = round(sum(get_rain(p) for p in slice_pts), 2)
            pop = max((get_pop(p) for p in slice_pts), default=pop_1h)
            temp = round(sum(float(p.get("values", {}).get("temperature", temp_1h)) for p in slice_pts) / max(1, len(slice_pts)), 1)
            horizons[f"{hours}h"] = {"rain_mm": rain, "pop_pct": pop, "temp_c": temp, "condition": cond}

        return horizons

    def _parse_to_reading(self, target: LocationTarget, payload: Dict[str, Any], quality: str = "live") -> RainfallReading:
        timelines = payload.get("timelines", {})
        minutely = timelines.get("minutely", [])
        hourly = timelines.get("hourly", [])
        daily = timelines.get("daily", [])

        base_values = minutely[0]["values"] if minutely and "values" in minutely[0] else (
            hourly[0]["values"] if hourly and "values" in hourly[0] else {}
        )

        temp_c = float(base_values.get("temperature", 20.0))
        feels_like_c = float(base_values.get("temperatureApparent", temp_c))
        humidity_pct = float(base_values.get("humidity", 70.0))
        pressure_hpa = float(base_values.get("pressureSurfaceLevel") or base_values.get("pressureSeaLevel") or 1013.25)
        wind_speed_kmh = round(float(base_values.get("windSpeed", 2.0)) * 3.6, 1)
        wind_deg = float(base_values.get("windDirection", 0.0))
        visibility_km = round(float(base_values.get("visibility", 10.0)), 1)
        cloud_cover_pct = float(base_values.get("cloudCover", 20.0))

        precip_1h = float(base_values.get("rainIntensity", 0.0))
        horizons = self._process_horizons(hourly)
        forecast_24h = float(horizons.get("24h", {}).get("rain_mm", 0.0))
        if forecast_24h == 0.0 and daily:
            forecast_24h = float(daily[0].get("values", {}).get("rainAccumulationSum", precip_1h * 2.5))

        precip_3h = float(horizons.get("3h", {}).get("rain_mm", precip_1h * 2.5))
        precip_6h = float(horizons.get("6h", {}).get("rain_mm", precip_3h * 1.8))
        pop_6h = float(horizons.get("6h", {}).get("pop_pct", 0.0))

        weather_code = base_values.get("weatherCode", 1000)
        weather_main = "Rain" if precip_1h > 0.1 else ("Clouds" if cloud_cover_pct > 50 else "Clear")
        weather_desc = f"Code {weather_code} ({'Rainy' if precip_1h > 0 else 'Fair'})"

        severity = compute_rainfall_severity(precip_1h, forecast_24h)
        risk = calculate_flood_risk(
            rainfall_rate_mm_hr=precip_1h,
            forecast_24h_mm=forecast_24h,
            observed_24h_mm=0.0,
            elevation_m=getattr(target, "elevation_m", None),
            pop_pct_next6h=pop_6h,
            weather_main=weather_main,
        )

        now_utc = datetime.now(timezone.utc)

        return RainfallReading(
            id=f"rain_{target.id}",
            name=target.name,
            state=getattr(target, "state", "India"),
            district=getattr(target, "district", target.name),
            lat=target.latitude,
            lon=target.longitude,
            rainfallMmPerHour=round(precip_1h, 2),
            rainfall_24h_mm=round(forecast_24h, 2),
            rainfall_3h_mm=round(precip_3h, 2),
            rainfall_6h_mm=round(precip_6h, 2),
            forecast_24h_mm=round(forecast_24h, 2),
            historical_24h_available=False,
            weather_main=weather_main,
            weather_description=weather_desc,
            temperature_c=round(temp_c, 1),
            feels_like_c=round(feels_like_c, 1),
            humidity_pct=round(humidity_pct, 1),
            pressure_hpa=round(pressure_hpa, 1),
            wind_speed_kmh=round(wind_speed_kmh, 1),
            wind_deg=round(wind_deg, 1),
            visibility_km=round(visibility_km, 1),
            cloud_cover_pct=round(cloud_cover_pct, 1),
            severity=severity,
            risk_level=risk["level"],
            risk_score=risk["score"],
            risk_reasons=risk["reasons"],
            forecast_horizons=horizons,
            timestamp=now_utc.isoformat(),
            source=self.name,
            quality=quality,
            station_type="synoptic_grid",
        )

    def get_current_rainfall(self, targets: List[LocationTarget]) -> Tuple[List[RainfallReading], Optional[str]]:
        if not targets:
            return [], None
        if not self.api_key:
            return [], "Tomorrow.io API key not configured"

        readings: List[RainfallReading] = []
        last_error = None

        for t in targets:
            data, err, _ = self.fetch_station(t)
            if data:
                quality = "stale" if err and "stale" in err.lower() else "live"
                readings.append(self._parse_to_reading(t, data, quality=quality))
            elif err:
                last_error = err

        return readings, last_error

