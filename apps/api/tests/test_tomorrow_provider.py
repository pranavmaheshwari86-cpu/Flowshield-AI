"""
apps/api/tests/test_tomorrow_provider.py
Flowshield — Tomorrow.io Weather & Nowcasting Provider Unit Tests
"""

import pytest
from datetime import datetime, timezone

from apps.api.app.services.providers.base import LocationTarget
from apps.api.app.services.providers.tomorrow_io import TomorrowIOProvider
from apps.api.app.services.providers.rainfall_provider import TomorrowIORainfallProvider, RainfallReading
from apps.api.app.schemas.observation import SourceType, DataState, DataQualityStatus


def test_tomorrow_provider_metadata():
    """Verify TomorrowIOProvider metadata, provenance, and freshness policy."""
    provider = TomorrowIOProvider(api_key="mock_test_key")
    assert provider.name == "Tomorrow.io High-Resolution Nowcasting API"
    assert provider.source_type == SourceType.AUTOMATED_STATION

    policy = provider.freshness_policy()
    assert policy.expected_update_interval_sec == 900
    assert policy.stale_after_sec == 3600
    assert policy.hard_expiry_sec == 21600

    prov = provider.provenance()
    assert prov["is_synthetic"] is False
    assert "Tomorrow.io" in prov["provider"]
    assert "1-minute" in prov["temporal_resolution"]


def test_tomorrow_provider_normalization_success():
    """Verify normalization of a full Tomorrow.io payload containing 1m nowcast and 1h forecast."""
    provider = TomorrowIOProvider(api_key="mock_test_key")
    target = LocationTarget(id="LOC-TEST", name="Mandi Catchment", latitude=31.70, longitude=76.93)

    mock_payload = {
        "results": [
            {
                "target_id": "LOC-TEST",
                "target_name": "Mandi Catchment",
                "data": {
                    "timelines": {
                        "minutely": [
                            {
                                "time": "2026-09-12T16:00:00Z",
                                "values": {
                                    "temperature": 22.5,
                                    "humidity": 85.0,
                                    "pressureSurfaceLevel": 915.2,
                                    "windSpeed": 4.0,  # m/s -> 14.4 km/h
                                    "rainIntensity": 12.5,
                                    "precipitationProbability": 80.0,
                                    "weatherCode": 4001,
                                },
                            }
                        ],
                        "hourly": [
                            {
                                "time": "2026-09-12T16:00:00Z",
                                "values": {
                                    "temperature": 22.5,
                                    "humidity": 85.0,
                                    "pressureSurfaceLevel": 915.2,
                                    "windSpeed": 4.0,
                                    "rainAccumulation": 12.5,
                                    "precipitationProbability": 80.0,
                                },
                            },
                            {
                                "time": "2026-09-12T17:00:00Z",
                                "values": {"rainAccumulation": 15.0},
                            },
                            {
                                "time": "2026-09-12T18:00:00Z",
                                "values": {"rainAccumulation": 8.0},
                            },
                        ],
                        "daily": [
                            {
                                "time": "2026-09-12T00:00:00Z",
                                "values": {"rainAccumulationSum": 45.0},
                            }
                        ],
                    }
                },
            }
        ]
    }

    obs_list = provider.normalize(mock_payload, [target])
    assert len(obs_list) == 1
    obs = obs_list[0]

    assert obs.location_id == "LOC-TEST"
    assert obs.temperature_c == 22.5
    assert obs.relative_humidity_pct == 85.0
    assert obs.surface_pressure_hpa == 915.2
    assert obs.wind_speed_kmh == 14.4
    assert obs.rainfall_1h_mm == 12.5
    assert obs.rainfall_3h_mm == 35.5  # 12.5 + 15.0 + 8.0
    assert obs.rainfall_24h_mm >= 35.5
    assert obs.data_state == DataState.OBSERVED
    assert obs.data_quality_status == DataQualityStatus.VALID
    assert obs.data_quality_score == 0.99
    assert "nowcast_points" in obs.metadata


def test_tomorrow_provider_normalization_fallback():
    """Verify that when Tomorrow.io payload is corrupt, it returns INSUFFICIENT_DATA safely."""
    provider = TomorrowIOProvider(api_key="mock_test_key")
    target = LocationTarget(id="LOC-FAIL", name="Pandoh Dam", latitude=31.67, longitude=77.05)

    obs_list = provider.normalize({"error": "Rate limit 429 reached"}, [target])
    assert len(obs_list) == 1
    obs = obs_list[0]
    assert obs.location_id == "LOC-FAIL"
    assert obs.data_state == DataState.INSUFFICIENT_DATA
    assert obs.data_quality_status == DataQualityStatus.INSUFFICIENT_DATA
    assert obs.data_quality_score == 0.0


def test_tomorrow_rainfall_provider_mock_reading():
    """Verify TomorrowIORainfallProvider parsing into RainfallReading with Flowshield Risk Model."""
    provider = TomorrowIORainfallProvider(api_key="mock_test_key")
    target = LocationTarget(id="mandi", name="Mandi Station", latitude=31.70, longitude=76.93, elevation_m=1200.0)

    mock_station_payload = {
        "timelines": {
            "minutely": [
                {
                    "time": "2026-09-12T16:00:00Z",
                    "values": {
                        "temperature": 24.0,
                        "temperatureApparent": 25.0,
                        "humidity": 90.0,
                        "pressureSurfaceLevel": 910.0,
                        "windSpeed": 5.0,
                        "windDirection": 120.0,
                        "visibility": 8.0,
                        "cloudCover": 80.0,
                        "rainIntensity": 22.0,  # heavy rain
                        "precipitationProbability": 90.0,
                        "weatherCode": 4001,
                    },
                }
            ],
            "hourly": [
                {"values": {"rainAccumulation": 22.0, "precipitationProbability": 90.0, "temperature": 24.0}},
                {"values": {"rainAccumulation": 20.0, "precipitationProbability": 85.0, "temperature": 23.5}},
                {"values": {"rainAccumulation": 15.0, "precipitationProbability": 70.0, "temperature": 23.0}},
            ],
            "daily": [
                {"values": {"rainAccumulationSum": 75.0}}
            ],
        }
    }

    reading = provider._parse_to_reading(target, mock_station_payload, quality="live")
    assert isinstance(reading, RainfallReading)
    assert reading.name == "Mandi Station"
    assert reading.rainfallMmPerHour == 22.0
    assert reading.rainfall_3h_mm == 57.0  # 22 + 20 + 15
    assert reading.forecast_24h_mm >= 57.0
    assert reading.severity in ["red", "purple"]
    assert reading.risk_level in ["Warning", "Critical"]
    assert reading.risk_score >= 50
    assert reading.source == provider.name
    assert "forecast_horizons" in reading.model_dump()


def test_tomorrow_provider_live_key():
    """Verify live connectivity using the configured TOMORROW_API_KEY from settings."""
    from apps.api.app.config import settings
    if not getattr(settings, "TOMORROW_API_KEY", ""):
        pytest.skip("TOMORROW_API_KEY not configured in environment")

    provider = TomorrowIOProvider()
    assert provider.health() is True
