"""Tests for Phase E: Centralized Feature Assembler & Soil Guard.

Validates that FlowShield never fabricates feature values, strictly distinguishes
VWC soil moisture from rainfall-derived estimates, and correctly raises
MODEL_INPUT_UNAVAILABLE when real physical telemetry is absent.
"""

import pytest
from apps.api.app.models.village import Village
from apps.api.app.models.observation import EnvironmentalObservation
from apps.api.app.services.feature_assembler import feature_assembler, FeatureAssemblyError
from apps.api.app.schemas.data_types import DataType
from apps.api.app.schemas.errors import ErrorCode


@pytest.fixture
def sample_village():
    return Village(
        id="hp-mandi-01",
        name="Mandi Sadar",
        district="Mandi",
        state="Himachal Pradesh",
        latitude=31.7087,
        longitude=76.9320,
        elevation=760.0,
        slope=18.5,
        distance_to_river=0.35,
        population=26000,
        tehsil="Mandi Sadar",
        historical_flood_frequency=3,
        vulnerability_index=0.45
    )


def test_feature_assembly_with_real_telemetry(sample_village):
    """Verifies complete assembly with authentic observed weather and VWC soil moisture."""
    real_weather = {
        "temperature_c": 19.4,
        "relative_humidity_pct": 74.0,
        "surface_pressure_hpa": 925.0,
        "wind_speed_kmh": 11.2,
    }
    accumulations = {
        "1h": 4.5,
        "3h": 12.0,
        "6h": 22.5,
        "24h": 45.0,
        "72h": 68.0,
    }

    # Pass authentic topsoil and deepsoil VWC
    features, prov = feature_assembler.assemble_inference_vector(
        village=sample_village,
        accumulations=accumulations,
        forecast_rain_mm=15.0,
        horizon_hours=3,
        real_weather_dict=real_weather,
        real_soil_vwc_top=0.315,
        real_soil_vwc_deep=0.270,
        strict_soil_guard=True
    )

    # 1. Atmospheric features must match real values, not defaults
    assert features["temperature_c"] == 19.4
    assert features["relative_humidity_pct"] == 74.0
    assert features["surface_pressure_hpa"] == 925.0
    assert features["wind_speed_kmh"] == 11.2

    # 2. VWC conversion: (0.315 / 0.45) * 100 = 70.0%
    assert features["soil_saturation_pct"] == 70.0
    assert prov["soil"]["data_type"] == DataType.OBSERVED
    assert "Soil VWC" in prov["soil"]["source"]

    # 3. Terrain GIS
    assert features["elevation_m"] == 760.0
    assert features["catchment_slope_deg"] == 18.5
    assert features["dist_to_river_m"] == 350.0
    assert features["upstream_drainage_sqkm"] == 6350.0


def test_feature_assembly_soil_guard_derived_estimate(sample_village):
    """Verifies that rainfall-derived soil is explicitly marked DERIVED_ESTIMATE with formula."""
    real_weather = {
        "temperature_c": 21.0,
        "relative_humidity_pct": 80.0,
        "surface_pressure_hpa": 920.0,
        "wind_speed_kmh": 10.0,
    }
    accumulations = {"24h": 20.0}

    # No VWC provided -> fallback to derived estimate
    features, prov = feature_assembler.assemble_inference_vector(
        village=sample_village,
        accumulations=accumulations,
        forecast_rain_mm=0.0,
        real_weather_dict=real_weather,
        real_soil_vwc_top=None,
        real_soil_vwc_deep=None,
        strict_soil_guard=False
    )

    assert prov["soil"]["data_type"] == DataType.DERIVED_ESTIMATE
    assert "formula" in prov["soil"]
    # 48 + 0.35 * 20 = 55.0
    assert features["soil_saturation_pct"] == 55.0


def test_feature_assembly_missing_weather_raises_error(sample_village):
    """Verifies that missing atmospheric telemetry raises MODEL_INPUT_UNAVAILABLE."""
    # Omit temperature and humidity
    incomplete_weather = {
        "surface_pressure_hpa": 920.0,
        "wind_speed_kmh": 10.0,
    }

    with pytest.raises(FeatureAssemblyError) as exc_info:
        feature_assembler.assemble_inference_vector(
            village=sample_village,
            real_weather_dict=incomplete_weather,
        )

    assert exc_info.value.code == ErrorCode.MODEL_INPUT_UNAVAILABLE
    assert "temperature_c" in exc_info.value.missing_features
    assert "relative_humidity_pct" in exc_info.value.missing_features
