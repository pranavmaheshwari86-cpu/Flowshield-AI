"""
apps/api/tests/test_observation_schema.py
Flowshield — Environmental Observation & Data Semantics Tests (Phase 1 Gate)
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from apps.api.app.schemas.observation import (
    SourceType,
    DataState,
    DataQualityStatus,
    EnvironmentalObservationBase,
    EnvironmentalObservationCreate,
    EnvironmentalObservationResponse,
    NormalizedObservation,
)
from apps.api.app.models.observation import EnvironmentalObservation


def test_data_semantics_enums():
    """Verify that all canonical SourceType, DataState, and DataQualityStatus enum values are defined."""
    assert SourceType.OFFICIAL == "OFFICIAL"
    assert SourceType.AUTOMATED_STATION == "AUTOMATED_STATION"
    assert SourceType.REANALYSIS == "REANALYSIS"
    assert SourceType.HISTORICAL == "HISTORICAL"
    assert SourceType.SIMULATION == "SIMULATION"

    assert DataState.OBSERVED == "OBSERVED"
    assert DataState.FORECAST == "FORECAST"
    assert DataState.HISTORICAL == "HISTORICAL"
    assert DataState.SIMULATION == "SIMULATION"
    assert DataState.ESTIMATED == "ESTIMATED"
    assert DataState.STALE == "STALE"
    assert DataState.INSUFFICIENT_DATA == "INSUFFICIENT_DATA"
    assert DataState.UNAVAILABLE == "UNAVAILABLE"
    assert DataState.INVALID == "INVALID"

    assert DataQualityStatus.VALID == "VALID"
    assert DataQualityStatus.DEGRADED == "DEGRADED"
    assert DataQualityStatus.STALE == "STALE"
    assert DataQualityStatus.INVALID == "INVALID"
    assert DataQualityStatus.INSUFFICIENT_DATA == "INSUFFICIENT_DATA"


def test_observation_schema_valid_creation():
    """Verify standard creation of observation schema with canonical physical parameters."""
    obs = EnvironmentalObservationBase(
        rainfall_1h=15.0,
        rainfall_3h=42.0,
        rainfall_6h=85.0,
        rainfall_24h=190.0,
        rainfall_intensity=35.0,
        soil_moisture=78.5,
        river_level=49.82,
        river_level_change=1.22,
        rainfall_12h=120.0,
        rainfall_72h=320.0,
        deep_soil_moisture=72.0,
        soil_moisture_change=5.2,
        river_level_change_1h=0.15,
        river_level_rate=0.15,
        temperature=18.5,
        humidity=92.0,
        surface_pressure=915.0,
        wind_speed=24.0,
        source_type=SourceType.AUTOMATED_STATION,
        data_state=DataState.OBSERVED,
        data_quality_status=DataQualityStatus.VALID,
        data_quality_score=1.0,
    )
    assert obs.rainfall_1h == 15.0
    assert obs.rainfall_72h == 320.0
    assert obs.deep_soil_moisture == 72.0
    assert obs.source_type == SourceType.AUTOMATED_STATION
    assert obs.data_state == DataState.OBSERVED


def test_observation_schema_invalid_physical_bounds():
    """Verify that physically impossible values (e.g. negative rainfall or >100% soil moisture) trip validation errors."""
    with pytest.raises(ValidationError):
        EnvironmentalObservationBase(
            rainfall_1h=-10.0,  # Negative rainfall impossible
            rainfall_3h=0.0,
            rainfall_6h=0.0,
            rainfall_24h=0.0,
            rainfall_intensity=0.0,
            soil_moisture=50.0,
            river_level=10.0,
            river_level_change=0.0,
        )

    with pytest.raises(ValidationError):
        EnvironmentalObservationBase(
            rainfall_1h=10.0,
            rainfall_3h=20.0,
            rainfall_6h=30.0,
            rainfall_24h=40.0,
            rainfall_intensity=5.0,
            soil_moisture=150.0,  # Soil moisture cannot exceed 100%
            river_level=10.0,
            river_level_change=0.0,
        )


def test_orm_model_canonical_property_accessors():
    """Verify that the SQLAlchemy EnvironmentalObservation model provides canonical 15-feature property accessors."""
    obs = EnvironmentalObservation(
        village_id="VIL-TEST-001",
        rainfall_1h=12.5,
        rainfall_3h=35.0,
        rainfall_6h=65.0,
        rainfall_24h=140.0,
        rainfall_intensity=25.0,
        soil_moisture=80.0,
        river_level=5.5,
        river_level_change=0.8,
        rainfall_72h=260.0,
        deep_soil_moisture=75.0,
        temperature=19.2,
        humidity=88.0,
        surface_pressure=918.0,
        wind_speed=18.0,
        source_type="AUTOMATED_STATION",
        data_state="OBSERVED",
        data_quality_status="VALID",
    )
    assert obs.rainfall_1h_mm == 12.5
    assert obs.rainfall_3h_mm == 35.0
    assert obs.rainfall_6h_mm == 65.0
    assert obs.rainfall_24h_mm == 140.0
    assert obs.rainfall_72h_mm == 260.0
    assert obs.soil_saturation_pct == 80.0
    assert obs.deep_soil_saturation_pct == 75.0
    assert obs.temperature_c == 19.2
    assert obs.relative_humidity_pct == 88.0
    assert obs.surface_pressure_hpa == 918.0
    assert obs.wind_speed_kmh == 18.0
