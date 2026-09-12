"""Centralized data validation and freshness engine for FlowShield.

Enforces physical boundaries, coordinate bounds, chronological sanity, and freshness classification.
Rejects unphysical or corrupted telemetry (e.g. negative rainfall, NaN, future timestamps)
and prevents unvalidated data from reaching ML inference or the UI.
"""

import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from ..schemas.data_types import FreshnessStatus, DataType

logger = logging.getLogger("flowshield.observation_validator")


class PhysicalLimits:
    """Rigorous physical range constraints for environmental parameters."""
    TEMP_MIN_C = -50.0
    TEMP_MAX_C = 60.0
    HUMIDITY_MIN = 0.0
    HUMIDITY_MAX = 100.0
    PRESSURE_MIN_HPA = 800.0
    PRESSURE_MAX_HPA = 1100.0
    WIND_SPEED_MIN_KMH = 0.0
    WIND_SPEED_MAX_KMH = 250.0
    RAINFALL_MIN_MM = 0.0
    RAINFALL_MAX_1H_MM = 300.0  # World record is ~305 mm/h
    RIVER_LEVEL_MIN_M = 0.0
    RIVER_LEVEL_MAX_M = 150.0
    LAT_MIN = -90.0
    LAT_MAX = 90.0
    LON_MIN = -180.0
    LON_MAX = 180.0


class ValidationResult:
    """Outcome of an observation validation evaluation."""
    def __init__(
        self,
        is_valid: bool,
        errors: List[str],
        warnings: List[str],
        sanitized_data: Dict[str, Any],
        freshness_status: FreshnessStatus,
    ):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings
        self.sanitized_data = sanitized_data
        self.freshness_status = freshness_status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "freshness_status": self.freshness_status.value,
        }


class ObservationValidator:
    """Comprehensive validation engine enforcing physical bounds and temporal freshness."""

    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> Tuple[bool, Optional[str]]:
        """Validate geographic coordinates."""
        if math.isnan(lat) or math.isnan(lon) or math.isinf(lat) or math.isinf(lon):
            return False, "Coordinates contain NaN or Infinite values"
        if not (PhysicalLimits.LAT_MIN <= lat <= PhysicalLimits.LAT_MAX):
            return False, f"Latitude {lat} out of bounds [{PhysicalLimits.LAT_MIN}, {PhysicalLimits.LAT_MAX}]"
        if not (PhysicalLimits.LON_MIN <= lon <= PhysicalLimits.LON_MAX):
            return False, f"Longitude {lon} out of bounds [{PhysicalLimits.LON_MIN}, {PhysicalLimits.LON_MAX}]"
        return True, None

    @staticmethod
    def evaluate_freshness(
        timestamp_utc: Optional[datetime],
        is_official_bulletin: bool = False,
        provider_available: bool = True,
    ) -> FreshnessStatus:
        """Classifies observation into LIVE, RECENT, VERIFIED_CACHE, STALE, or UNAVAILABLE."""
        if not provider_available or timestamp_utc is None:
            return FreshnessStatus.UNAVAILABLE

        now = datetime.now(timezone.utc)
        if timestamp_utc.tzinfo is None:
            timestamp_utc = timestamp_utc.replace(tzinfo=timezone.utc)

        age_seconds = (now - timestamp_utc).total_seconds()
        if age_seconds < 0:
            # Tolerant up to 10 mins of clock drift
            if abs(age_seconds) <= 600:
                age_seconds = 0
            else:
                return FreshnessStatus.UNAVAILABLE

        if is_official_bulletin:
            if age_seconds <= 86400:  # 24 hours
                return FreshnessStatus.VERIFIED_CACHE
            return FreshnessStatus.STALE

        # Automated real-time sensor
        if age_seconds <= 3600:  # < 1 hour
            return FreshnessStatus.LIVE
        elif age_seconds <= 10800:  # 1 to 3 hours
            return FreshnessStatus.RECENT
        else:
            return FreshnessStatus.STALE

    def validate_observation(
        self,
        raw_obs: Dict[str, Any],
        is_official_bulletin: bool = False,
    ) -> ValidationResult:
        """Inspects all environmental measurements in an observation dict."""
        errors: List[str] = []
        warnings: List[str] = []
        sanitized: Dict[str, Any] = {}

        # 1. Timestamp validation
        ts = raw_obs.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                errors.append(f"Invalid timestamp format: {ts}")
                ts = None

        if ts is not None and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        if ts is not None and (ts - now).total_seconds() > 600:
            errors.append(f"Future timestamp rejected: {ts} is > 10m ahead of system time {now}")

        sanitized["timestamp"] = ts
        freshness = self.evaluate_freshness(ts, is_official_bulletin=is_official_bulletin)

        # 2. Atmospheric & physical range checks
        # Temperature
        temp = raw_obs.get("temperature") or raw_obs.get("temperature_c")
        if temp is not None:
            try:
                temp_val = float(temp)
                if math.isnan(temp_val) or math.isinf(temp_val):
                    errors.append("Temperature is NaN or Inf")
                elif not (PhysicalLimits.TEMP_MIN_C <= temp_val <= PhysicalLimits.TEMP_MAX_C):
                    errors.append(f"Temperature {temp_val}°C outside physical bounds [{PhysicalLimits.TEMP_MIN_C}, {PhysicalLimits.TEMP_MAX_C}]")
                else:
                    sanitized["temperature_c"] = temp_val
            except (ValueError, TypeError):
                errors.append(f"Unparseable temperature value: {temp}")
        else:
            sanitized["temperature_c"] = None

        # Relative Humidity
        hum = raw_obs.get("humidity") or raw_obs.get("relative_humidity_pct")
        if hum is not None:
            try:
                hum_val = float(hum)
                if math.isnan(hum_val) or math.isinf(hum_val):
                    errors.append("Humidity is NaN or Inf")
                elif not (PhysicalLimits.HUMIDITY_MIN <= hum_val <= PhysicalLimits.HUMIDITY_MAX):
                    errors.append(f"Humidity {hum_val}% outside [0, 100]")
                else:
                    sanitized["relative_humidity_pct"] = hum_val
            except (ValueError, TypeError):
                errors.append(f"Unparseable humidity value: {hum}")
        else:
            sanitized["relative_humidity_pct"] = None

        # Surface Pressure
        pres = raw_obs.get("surface_pressure") or raw_obs.get("surface_pressure_hpa") or raw_obs.get("pressure")
        if pres is not None:
            try:
                pres_val = float(pres)
                if math.isnan(pres_val) or math.isinf(pres_val):
                    errors.append("Pressure is NaN or Inf")
                elif not (PhysicalLimits.PRESSURE_MIN_HPA <= pres_val <= PhysicalLimits.PRESSURE_MAX_HPA):
                    warnings.append(f"Pressure {pres_val} hPa outside standard bounds [{PhysicalLimits.PRESSURE_MIN_HPA}, {PhysicalLimits.PRESSURE_MAX_HPA}]")
                    sanitized["surface_pressure_hpa"] = pres_val
                else:
                    sanitized["surface_pressure_hpa"] = pres_val
            except (ValueError, TypeError):
                errors.append(f"Unparseable pressure value: {pres}")
        else:
            sanitized["surface_pressure_hpa"] = None

        # Wind Speed
        wind = raw_obs.get("wind_speed") or raw_obs.get("wind_speed_kmh")
        if wind is not None:
            try:
                wind_val = float(wind)
                if math.isnan(wind_val) or math.isinf(wind_val):
                    errors.append("Wind speed is NaN or Inf")
                elif not (PhysicalLimits.WIND_SPEED_MIN_KMH <= wind_val <= PhysicalLimits.WIND_SPEED_MAX_KMH):
                    errors.append(f"Wind speed {wind_val} km/h outside [0, 250]")
                else:
                    sanitized["wind_speed_kmh"] = wind_val
            except (ValueError, TypeError):
                errors.append(f"Unparseable wind speed value: {wind}")
        else:
            sanitized["wind_speed_kmh"] = None

        # Rainfall 1h
        rain = raw_obs.get("rainfall_1h") or raw_obs.get("rainfall_1h_mm")
        if rain is not None:
            try:
                rain_val = float(rain)
                if math.isnan(rain_val) or math.isinf(rain_val):
                    errors.append("Rainfall is NaN or Inf")
                elif rain_val < PhysicalLimits.RAINFALL_MIN_MM:
                    errors.append(f"Negative rainfall rate {rain_val} mm/h is physically impossible")
                elif rain_val > PhysicalLimits.RAINFALL_MAX_1H_MM:
                    errors.append(f"Rainfall {rain_val} mm/h exceeds world-record threshold {PhysicalLimits.RAINFALL_MAX_1H_MM} mm/h")
                else:
                    sanitized["rainfall_1h_mm"] = rain_val
            except (ValueError, TypeError):
                errors.append(f"Unparseable rainfall value: {rain}")
        else:
            sanitized["rainfall_1h_mm"] = None

        # River Level
        river = raw_obs.get("river_level") or raw_obs.get("river_level_m")
        if river is not None:
            try:
                river_val = float(river)
                if math.isnan(river_val) or math.isinf(river_val):
                    errors.append("River level is NaN or Inf")
                elif not (PhysicalLimits.RIVER_LEVEL_MIN_M <= river_val <= PhysicalLimits.RIVER_LEVEL_MAX_M):
                    errors.append(f"River level {river_val} m MSL outside [{PhysicalLimits.RIVER_LEVEL_MIN_M}, {PhysicalLimits.RIVER_LEVEL_MAX_M}]")
                else:
                    sanitized["river_level_m"] = river_val
            except (ValueError, TypeError):
                errors.append(f"Unparseable river level: {river}")
        else:
            sanitized["river_level_m"] = None

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            sanitized_data=sanitized,
            freshness_status=freshness,
        )

    @staticmethod
    def deduplicate_and_sort_timeseries(
        points: List[Dict[str, Any]],
        timestamp_key: str = "timestamp",
    ) -> List[Dict[str, Any]]:
        """Deduplicates points by timestamp and sorts in chronological ascending order."""
        seen = set()
        deduped = []
        for pt in points:
            ts = pt.get(timestamp_key)
            if ts is None:
                continue
            if isinstance(ts, datetime):
                ts_key = ts.isoformat()
            else:
                ts_key = str(ts)

            if ts_key not in seen:
                seen.add(ts_key)
                deduped.append(pt)

        # Sort chronologically
        def get_ts(pt):
            t = pt.get(timestamp_key)
            if isinstance(t, datetime):
                return t
            try:
                return datetime.fromisoformat(str(t).replace("Z", "+00:00"))
            except Exception:
                return datetime.min.replace(tzinfo=timezone.utc)

        deduped.sort(key=get_ts)
        return deduped


observation_validator = ObservationValidator()
