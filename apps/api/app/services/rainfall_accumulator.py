"""
apps/api/app/services/rainfall_accumulator.py
Flowshield — Real-Time Rainfall Accumulation & Forecast Aggregation Engine
Smart India Hackathon 2026 (Problem Statement ID: 26192)

Implements rigorous rolling-window meteorological precipitation calculations:
- 1-hour, 3-hour, 6-hour, 12-hour, 24-hour, and 72-hour rolling accumulations.
- Handles missing observations, duplicate timestamps, timezone offsets,
  variable sampling intervals, and null/corrupted sensor readings.
- Forecast precipitation aggregation for +1h, +3h, +6h, +12h, +24h, +48h.
- Normalizes rainfall values internally to millimeters (mm) and intensity to mm/hr.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union

logger = logging.getLogger("flowshield.rainfall_accumulator")


class RainfallAccumulator:
    """
    Mathematical accumulation engine for real-time and historical rainfall observations.
    Calculates exact rolling totals over 1h, 3h, 6h, 12h, and 24h windows without scalar shortcuts.
    """

    @staticmethod
    def parse_timestamp(ts: Union[str, datetime, int, float]) -> datetime:
        """Parses various timestamp representations into a timezone-aware UTC datetime."""
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                return ts.replace(tzinfo=timezone.utc)
            return ts.astimezone(timezone.utc)
        elif isinstance(ts, (int, float)):
            # Unix epoch timestamp in seconds
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        elif isinstance(ts, str):
            clean_ts = ts.strip()
            # Handle ISO string variations
            if clean_ts.endswith("Z"):
                clean_ts = clean_ts[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(clean_ts)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                # Fallback to strptime for standard formats
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S.%f",
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(clean_ts, fmt).replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue
        raise ValueError(f"Cannot parse timestamp: {ts}")

    def clean_and_sort_observations(
        self,
        raw_observations: List[Dict[str, Any]]
    ) -> List[Tuple[datetime, float]]:
        """
        Cleanses, deduplicates, and sorts raw rainfall observations chronologically.
        Returns a list of (utc_timestamp, rainfall_mm) tuples.
        """
        if not raw_observations:
            return []

        dedup_map: Dict[datetime, float] = {}

        for obs in raw_observations:
            if not isinstance(obs, dict):
                continue

            ts_raw = obs.get("timestamp") or obs.get("time") or obs.get("dt")
            if ts_raw is None:
                continue

            try:
                utc_dt = self.parse_timestamp(ts_raw)
            except Exception:
                continue

            # Extract rainfall amount in mm
            # Supports 'rainfall_mm', 'precipitation', 'rain', 'amount_mm', 'rainfall'
            val = None
            for key in ["rainfall_mm", "precipitation", "rain", "amount_mm", "rainfall", "rainfall_1h"]:
                if key in obs and obs[key] is not None:
                    try:
                        val = float(obs[key])
                        break
                    except (ValueError, TypeError):
                        continue

            if val is None:
                val = 0.0

            # Guard against invalid / negative physical values
            val = max(0.0, min(val, 500.0))

            # Deduplicate by timestamp: take max or latest valid reading
            if utc_dt in dedup_map:
                dedup_map[utc_dt] = max(dedup_map[utc_dt], val)
            else:
                dedup_map[utc_dt] = val

        sorted_points = sorted(dedup_map.items(), key=lambda x: x[0])
        return sorted_points

    def calculate_rolling_accumulations(
        self,
        observations: List[Dict[str, Any]],
        now: Optional[datetime] = None,
        current_rate_mm_hr: Optional[float] = None,
        current_rate: Optional[float] = None,
        **kwargs
    ) -> Dict[str, float]:
        """
        Calculates exact accumulated rainfall over rolling time horizons (1h, 3h, 6h, 12h, 24h, 72h).
        
        Returns:
        {
            "current_mm_hr": float,
            "1h": float,
            "3h": float,
            "6h": float,
            "12h": float,
            "24h": float,
            "72h": float
        }
        """
        if current_rate_mm_hr is None and current_rate is not None:
            current_rate_mm_hr = current_rate
        now_utc = self.parse_timestamp(now) if now else datetime.now(timezone.utc)
        cleaned = self.clean_and_sort_observations(observations)

        # Default outputs
        accum = {
            "current_mm_hr": 0.0,
            "1h": 0.0,
            "3h": 0.0,
            "6h": 0.0,
            "12h": 0.0,
            "24h": 0.0,
            "72h": 0.0,
        }

        if current_rate_mm_hr is not None:
            accum["current_mm_hr"] = max(0.0, round(float(current_rate_mm_hr), 2))

        if not cleaned:
            # If no time-series observations are present, base 1h on current rate
            if current_rate_mm_hr is not None:
                rate = max(0.0, float(current_rate_mm_hr))
                accum["1h"] = round(rate, 1)
            return accum

        # If current_rate was not provided, derive from most recent observation within past 90 minutes
        if current_rate_mm_hr is None and cleaned:
            latest_dt, latest_val = cleaned[-1]
            if (now_utc - latest_dt).total_seconds() <= 5400:  # 90 minutes
                accum["current_mm_hr"] = round(latest_val, 2)

        # Rolling window thresholds
        windows = {
            "1h": timedelta(hours=1),
            "3h": timedelta(hours=3),
            "6h": timedelta(hours=6),
            "12h": timedelta(hours=12),
            "24h": timedelta(hours=24),
            "72h": timedelta(hours=72),
        }

        # Sum observations falling strictly within each rolling window [now - window, now]
        for w_name, delta in windows.items():
            window_start = now_utc - delta
            total_mm = 0.0
            for dt, val in cleaned:
                if window_start <= dt <= now_utc:
                    total_mm += val
            accum[w_name] = round(total_mm, 2)

        # Ensure monotonicity: window(T1) <= window(T2) for T1 < T2
        accum["3h"] = max(accum["3h"], accum["1h"])
        accum["6h"] = max(accum["6h"], accum["3h"])
        accum["12h"] = max(accum["12h"], accum["6h"])
        accum["24h"] = max(accum["24h"], accum["12h"])
        accum["72h"] = max(accum["72h"], accum["24h"])

        return accum

    def aggregate_forecast(
        self,
        forecast_slots: List[Dict[str, Any]],
        now: Optional[datetime] = None
    ) -> Dict[str, Union[float, str]]:
        """
        Aggregates forecast precipitation for future horizons (+1h, +3h, +6h, +12h, +24h, +48h).
        
        Expected slot schema:
        - "time" or "timestamp" or "dt": ISO string or Unix timestamp
        - "precipitation_mm" or "rain" or "rainfall": float in mm for that slot
        
        Returns:
        {
            "1h": float | "Forecast unavailable",
            "3h": float | "Forecast unavailable",
            "6h": float | "Forecast unavailable",
            "12h": float | "Forecast unavailable",
            "24h": float | "Forecast unavailable",
            "48h": float | "Forecast unavailable",
        }
        """
        now_utc = self.parse_timestamp(now) if now else datetime.now(timezone.utc)
        
        result: Dict[str, Union[float, str]] = {
            "1h": "Forecast unavailable",
            "3h": "Forecast unavailable",
            "6h": "Forecast unavailable",
            "12h": "Forecast unavailable",
            "24h": "Forecast unavailable",
            "48h": "Forecast unavailable",
        }

        if not forecast_slots:
            return result

        # Parse and sort forecast slots
        parsed_slots: List[Tuple[datetime, float]] = []
        for slot in forecast_slots:
            ts_raw = slot.get("timestamp") or slot.get("time") or slot.get("dt") or slot.get("forecast_time") or slot.get("target_time")
            if ts_raw is None:
                continue
            try:
                dt = self.parse_timestamp(ts_raw)
            except Exception:
                continue

            # Amount in mm
            val = None
            for k in ["precipitation_mm", "precipitation", "rain", "rainfall", "amount_mm"]:
                if k in slot and slot[k] is not None:
                    try:
                        val = float(slot[k])
                        break
                    except (ValueError, TypeError):
                        continue
            if val is None:
                val = 0.0

            parsed_slots.append((dt, max(0.0, val)))

        if not parsed_slots:
            return result

        parsed_slots.sort(key=lambda x: x[0])
        max_forecast_dt = parsed_slots[-1][0]
        total_forecast_span_hrs = (max_forecast_dt - now_utc).total_seconds() / 3600.0

        horizons = {
            "1h": 1,
            "3h": 3,
            "6h": 6,
            "12h": 12,
            "24h": 24,
            "48h": 48,
        }

        for h_name, h_hours in horizons.items():
            h_target_dt = now_utc + timedelta(hours=h_hours)
            
            # If forecast slots don't reach at least 70% of this horizon, mark unavailable
            if total_forecast_span_hrs < (h_hours * 0.7):
                result[h_name] = "Forecast unavailable"
                continue

            # Sum all slots within [now_utc, h_target_dt]
            sum_mm = 0.0
            slots_found = False
            for dt, mm in parsed_slots:
                if now_utc <= dt <= h_target_dt:
                    sum_mm += mm
                    slots_found = True

            if slots_found:
                result[h_name] = round(sum_mm, 2)
            else:
                # If target is within forecast span but 0 rain in all slots
                result[h_name] = 0.0

        return result

    def get_observed_timeline_series(
        self,
        observations: List[Dict[str, Any]],
        now: Optional[datetime] = None,
        default_soil: float = 50.0,
        default_river: Optional[float] = None,
        current_rate_mm_hr: Optional[float] = None,
        *args,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generates the 7 exact observed timeline points: -6h, -5h, -4h, -3h, -2h, -1h, NOW.
        Each point contains actual observed rainfall rate, soil saturation, river stage, and operational risk.
        """
        now_utc = self.parse_timestamp(now) if now else datetime.now(timezone.utc)
        cleaned = self.clean_and_sort_observations(observations)

        # Target relative hours: -6 to 0
        rel_hours = [-6, -5, -4, -3, -2, -1, 0]
        series = []

        for rh in rel_hours:
            pt_dt = now_utc + timedelta(hours=rh)

            # Find closest observation within +/- 45 minutes of pt_dt
            closest_val: Optional[float] = None
            min_diff_sec = 2700  # 45 min window
            for obs_dt, val in cleaned:
                diff = abs((obs_dt - pt_dt).total_seconds())
                if diff < min_diff_sec:
                    min_diff_sec = diff
                    closest_val = val

            # Special handling for rh == 0 (current time)
            if rh == 0 and closest_val is None and current_rate_mm_hr is not None:
                closest_val = current_rate_mm_hr

            rain_rate = closest_val if closest_val is not None else None

            # Calculate deterministic risk score for this historical step if observations exist
            soil_contrib = (default_soil * 0.25) if default_soil is not None else 0.0
            if rain_rate is not None:
                # Hydrological wetness and runoff index bounded [0, 100]
                risk_score = min(100.0, max(0.0, (rain_rate * 3.5) + soil_contrib))
            else:
                # When rate is missing, fallback strictly to baseline soil saturation loading
                risk_score = min(100.0, max(0.0, soil_contrib))

            series.append({
                "relative_hour": rh,
                "timestamp": pt_dt,
                "observed_rainfall_rate": round(rain_rate, 2) if rain_rate is not None else None,
                "observed_river_stage": round(default_river, 2) if default_river is not None else None,
                "observed_soil_saturation": round(default_soil, 1) if default_soil is not None else None,
                "operational_risk_score": round(risk_score, 1),
            })

        return series


rainfall_accumulator = RainfallAccumulator()
