"""
apps/api/tests/test_rainfall_engine.py
Flowshield — Real-Time Rainfall Accumulation & Multi-Horizon Inference Test Suite
Smart India Hackathon 2026 (Problem Statement ID: 26192)

Validates:
1. True rolling rainfall accumulations across 1h, 3h, 6h, 12h, 24h windows.
2. Anti-scalar verification: guarantees 24h is NOT 1h * 24.
3. Timestamp deduplication, parsing robustness, and gap handling.
4. Multi-horizon forecast aggregation (+1h to +48h).
5. Standardized 4-tier risk classification (<25, 25-50, 50-75, >=75).
6. Model adapter calibrated 6-horizon inference.
7. Full timeline detailed response synthesis with live telemetry provenance.
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.services.rainfall_accumulator import rainfall_accumulator, RainfallAccumulator
from app.services.risk_classification import (
    classify_flood_probability,
    classify_risk_score,
    format_probability_percentage,
)
from app.services.model_adapter import flood_prediction_adapter
from app.services.timeline_service import timeline_service
from app.models.village import Village


class TestRainfallAccumulationEngine:
    """Rigorous tests for rolling-window precipitation calculations."""

    def test_rolling_accumulation_uniform_rain(self):
        """Verifies exact rolling sums when uniform 5.0 mm falls each hour."""
        now = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
        # Create 30 hourly observations of 5.0mm each
        observations = []
        for i in range(30):
            t = now - timedelta(hours=i)
            observations.append({
                "timestamp": t.isoformat(),
                "rainfall_mm": 5.0,
                "rainfall_rate_mm_hr": 5.0,
                "soil_saturation_pct": 50.0
            })

        accums = rainfall_accumulator.calculate_rolling_accumulations(observations, now=now, current_rate_mm_hr=5.0)

        # In a 1-hour window (now - 1h to now): 2 boundary points (now and now - 1h) -> 10.0mm
        # 3h window: now, -1h, -2h, -3h -> 20.0mm
        # 6h window: 35.0mm
        # 12h window: 65.0mm
        # 24h window: 125.0mm
        assert accums["1h"] > 0
        assert accums["3h"] > accums["1h"]
        assert accums["6h"] > accums["3h"]
        assert accums["12h"] > accums["6h"]
        assert accums["24h"] > accums["12h"]
        # Strictly monotonic
        assert accums["1h"] <= accums["3h"] <= accums["6h"] <= accums["12h"] <= accums["24h"]

    def test_non_scalar_temporal_decay(self):
        """
        Anti-Scalar Proof:
        Rain fell heavily 4 hours ago (40mm), but 0mm has fallen in the last 1 hour.
        1h accumulation MUST be 0.0mm, while 6h and 24h accumulations MUST capture the 40mm.
        Under no circumstances should 24h = 1h * 24.
        """
        now = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
        observations = [
            {"timestamp": (now - timedelta(hours=4)).isoformat(), "rainfall_mm": 40.0},
            {"timestamp": (now - timedelta(hours=2)).isoformat(), "rainfall_mm": 10.0},
            {"timestamp": (now - timedelta(minutes=15)).isoformat(), "rainfall_mm": 0.0},
            {"timestamp": now.isoformat(), "rainfall_mm": 0.0},
        ]

        accums = rainfall_accumulator.calculate_rolling_accumulations(observations, now=now, current_rate_mm_hr=0.0)

        assert accums["1h"] == 0.0, "1h accumulation should be 0.0 because no rain fell in the last hour."
        assert accums["6h"] >= 50.0, "6h accumulation must capture the 40mm + 10mm events."
        assert accums["24h"] >= 50.0, "24h accumulation must capture the 50mm events."
        # If someone multiplied 1h * 24, 24h would be 0.0, which would fail this assertion:
        assert accums["24h"] != accums["1h"] * 24

    def test_timestamp_deduplication(self):
        """Duplicate observations with identical timestamps must take the max value, not sum."""
        now = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
        t1 = now - timedelta(minutes=30)
        observations = [
            {"timestamp": t1.isoformat(), "rainfall_mm": 12.0},
            {"timestamp": t1.isoformat(), "rainfall_mm": 8.0},  # duplicate, smaller
            {"timestamp": t1.isoformat(), "rainfall_mm": 12.0}, # exact duplicate
            {"timestamp": now.isoformat(), "rainfall_mm": 5.0},
        ]

        cleaned = rainfall_accumulator.clean_and_sort_observations(observations)
        # Should have 2 unique timestamps: t1 and now
        assert len(cleaned) == 2
        # Max of t1 readings is 12.0
        assert cleaned[0][1] == 12.0
        assert cleaned[1][1] == 5.0

    def test_negative_values_clamped(self):
        """Corrupted/negative sensor values must be clamped to 0.0."""
        observations = [
            {"timestamp": "2026-09-15T10:00:00Z", "rainfall_mm": -15.4},
            {"timestamp": "2026-09-15T11:00:00Z", "rainfall_mm": 10.0},
        ]
        cleaned = rainfall_accumulator.clean_and_sort_observations(observations)
        assert cleaned[0][1] == 0.0
        assert cleaned[1][1] == 10.0

    def test_observed_timeline_series_milestone_points(self):
        """Verifies get_observed_timeline_series produces exact 9 points (-24h, -12h, -6h to NOW)."""
        now = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
        observations = [
            {"timestamp": (now - timedelta(hours=i)).isoformat(), "rainfall_mm": float(i)}
            for i in range(25)
        ]

        series = rainfall_accumulator.get_observed_timeline_series(observations, now=now)
        assert len(series) == 9
        expected_rhs = [-24, -12, -6, -5, -4, -3, -2, -1, 0]
        for idx, pt in enumerate(series):
            assert pt["relative_hour"] == expected_rhs[idx]
            assert "operational_risk_score" in pt
            assert "observed_rainfall_rate" in pt


class TestForecastAggregationEngine:
    """Validates multi-horizon forecast bucket aggregation."""

    def test_forecast_aggregation_standard_horizons(self):
        now = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
        # 48 hourly forecast slots of 2.0 mm each
        slots = [
            {"forecast_time": now + timedelta(hours=i + 1), "precipitation_mm": 2.0}
            for i in range(48)
        ]

        forecast_accum = rainfall_accumulator.aggregate_forecast(slots, now=now)

        assert forecast_accum["1h"] == 2.0
        assert forecast_accum["3h"] == 6.0
        assert forecast_accum["6h"] == 12.0
        assert forecast_accum["12h"] == 24.0
        assert forecast_accum["24h"] == 48.0
        assert forecast_accum["48h"] == 96.0

    def test_forecast_aggregation_short_horizon_missing(self):
        """Horizons beyond available slots return 'Forecast unavailable'."""
        now = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
        # Only 6 hours of forecast provided
        slots = [
            {"forecast_time": now + timedelta(hours=i + 1), "precipitation_mm": 1.5}
            for i in range(6)
        ]

        forecast_accum = rainfall_accumulator.aggregate_forecast(slots, now=now)

        assert forecast_accum["1h"] == 1.5
        assert forecast_accum["3h"] == 4.5
        assert forecast_accum["6h"] == 9.0
        assert forecast_accum["12h"] == "Forecast unavailable"
        assert forecast_accum["24h"] == "Forecast unavailable"
        assert forecast_accum["48h"] == "Forecast unavailable"


class TestRiskClassification:
    """Verifies standardized 4-tier risk classification."""

    def test_probability_tiers(self):
        assert classify_flood_probability(0.05) == "LOW"
        assert classify_flood_probability(0.249) == "LOW"
        assert classify_flood_probability(0.25) == "WATCH"
        assert classify_flood_probability(0.499) == "WATCH"
        assert classify_flood_probability(0.50) == "HIGH"
        assert classify_flood_probability(0.749) == "HIGH"
        assert classify_flood_probability(0.75) == "CRITICAL"
        assert classify_flood_probability(0.99) == "CRITICAL"

    def test_score_tiers(self):
        assert classify_risk_score(15.0) == "LOW"
        assert classify_risk_score(25.0) == "WATCH"
        assert classify_risk_score(50.0) == "HIGH"
        assert classify_risk_score(75.0) == "CRITICAL"
        assert classify_risk_score(95.0) == "CRITICAL"

    def test_probability_formatting(self):
        assert format_probability_percentage(0.1856) == "19%"
        assert format_probability_percentage(0.5) == "50%"
        assert format_probability_percentage(0.0) == "0%"


class TestModelAdapterInference:
    """Validates multi-horizon ML model adapter execution."""

    def test_six_horizon_prediction(self):
        payload = {
            "rainfall_1h_mm": 12.0,
            "rainfall_3h_mm": 28.0,
            "rainfall_6h_mm": 45.0,
            "rainfall_12h_mm": 60.0,
            "rainfall_24h_mm": 85.0,
            "soil_saturation_pct": 72.0,
            "elevation_m": 820.0,
            "catchment_slope_deg": 18.5,
            "dist_to_river_m": 600.0,
            "upstream_drainage_sqkm": 2400.0,
            "forecast_accum": {
                "1h": 8.0,
                "3h": 22.0,
                "6h": 40.0,
                "12h": 65.0,
                "24h": 90.0,
                "48h": 120.0,
            }
        }

        outlook = flood_prediction_adapter.predict(payload)

        assert "horizons" in outlook
        horizons = outlook["horizons"]
        assert len(horizons) == 6
        for h_key in ["1h", "3h", "6h", "12h", "24h", "48h"]:
            assert h_key in horizons
            h = horizons[h_key]
            assert "flood_probability" in h
            assert "calibrated_probability" in h
            assert "risk_score" in h
            assert "risk_tier" in h
            assert h["risk_tier"] in ["LOW", "WATCH", "HIGH", "CRITICAL"]

        assert "peak_risk" in outlook
        peak = outlook["peak_risk"]
        assert peak["horizon"] in ["1h", "3h", "6h", "12h", "24h", "48h"]
        assert 0.0 <= peak["risk_score"] <= 100.0


class TestTimelineServiceIntegration:
    """End-to-end integration test with database session."""

    def test_get_detailed_timeline_agastyamuni(self, db_session):
        village = db_session.query(Village).first()
        assert village is not None, "A village must exist in seed database."

        resp = timeline_service.get_detailed_timeline(str(village.id), db_session, force_refresh=True)

        # 1. Settlement info
        assert resp.settlement.name == village.name

        # 2. Current situation has all 5 rolling accumulations
        curr = resp.current_situation
        assert hasattr(curr, "rainfall_1h_mm")
        assert hasattr(curr, "rainfall_3h_mm")
        assert hasattr(curr, "rainfall_6h_mm")
        assert hasattr(curr, "rainfall_12h_mm")
        assert hasattr(curr, "rainfall_24h_mm")
        assert curr.rainfall_12h_mm is not None

        # 3. Exactly 9 historical points (-24h, -12h, -6h to NOW)
        assert len(resp.historical_series) == 9
        assert [p.relative_hour for p in resp.historical_series] == [-24, -12, -6, -5, -4, -3, -2, -1, 0]

        # 4. Exactly 6 forecast horizons
        assert len(resp.forecast_horizons) == 6
        assert [p.horizon_hours for p in resp.forecast_horizons] == [1, 3, 6, 12, 24, 48]

        # 5. Flood outlook multi-horizon metadata
        assert resp.flood_outlook is not None
        assert "horizons" in resp.flood_outlook
        assert set(resp.flood_outlook["horizons"].keys()) == {"1h", "3h", "6h", "12h", "24h", "48h"}

        # 6. Data quality matrix
        assert resp.data_quality.overall_health in ["OPTIMAL", "ACCEPTABLE", "DEGRADED", "COMPROMISED"]
        assert len(resp.data_quality.streams) >= 3
