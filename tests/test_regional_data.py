"""
tests/test_regional_data.py
Flowshield — Regional Data & Configuration Validation Suite
Validates all 10 region configs, canonical feature contracts, and station geofences.
"""

import pytest
import yaml
from pathlib import Path

from ml.registry.region_resolver import ALL_REGIONS, region_resolver
from ml.registry.feature_contract import (
    CANONICAL_FEATURES,
    PHYSICAL_BOUNDS,
    compute_schema_hash,
    feature_contract,
)
from ml.src.utils.paths import get_repo_root


@pytest.fixture(scope="module")
def repo_root():
    return get_repo_root()


def test_all_ten_regions_present_and_resolvable():
    """Verify all 10 required regions are defined in ALL_REGIONS and resolvable."""
    expected_regions = [
        "himachal_pradesh",
        "jammu_kashmir",
        "leh_ladakh",
        "sikkim",
        "arunachal_pradesh",
        "nagaland",
        "manipur",
        "mizoram",
        "meghalaya",
        "tripura",
    ]
    assert len(ALL_REGIONS) == 10
    for r in expected_regions:
        assert r in ALL_REGIONS
        assert region_resolver.is_valid_region(r)


def test_region_config_files_valid_and_complete(repo_root):
    """Validate that every region has a syntactically valid and schema-compliant YAML config."""
    configs_dir = repo_root / "ml" / "configs" / "regions"
    assert configs_dir.exists()

    required_keys = [
        "region",
        "boundary",
        "stations",
        "training_period",
        "holdout_period",
        "data_sources",
        "model_defaults",
    ]

    for slug in ALL_REGIONS:
        cfg_file = configs_dir / f"{slug}.yaml"
        assert cfg_file.exists(), f"Config file missing for {slug}: {cfg_file}"

        with open(cfg_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        for key in required_keys:
            assert key in cfg, f"Key '{key}' missing in {cfg_file.name}"

        # Slug match
        assert cfg["region"]["slug"] == slug
        assert len(cfg["region"]["display_name"]) > 0

        # Coordinates sanity check (India region: Lat ~6-38 N, Lon ~68-98 E)
        bbox = cfg["boundary"]
        assert bbox["lat_min"] < bbox["lat_max"], f"Invalid lat order in {slug}"
        assert bbox["lon_min"] < bbox["lon_max"], f"Invalid lon order in {slug}"
        assert 6.0 <= bbox["lat_min"] <= 40.0, f"Lat min out of bounds in {slug}"
        assert 65.0 <= bbox["lon_min"] <= 100.0, f"Lon min out of bounds in {slug}"

        # Stations check
        stations = cfg["stations"]
        assert isinstance(stations, dict) and len(stations) >= 2, f"Expected >= 2 stations for {slug}"
        for st_id, st in stations.items():
            assert "name" in st
            lat = st.get("latitude") or st.get("lat")
            lon = st.get("longitude") or st.get("lon")
            assert lat is not None and bbox["lat_min"] - 0.5 <= lat <= bbox["lat_max"] + 0.5
            assert lon is not None and bbox["lon_min"] - 0.5 <= lon <= bbox["lon_max"] + 0.5

        # Model defaults check
        m_def = cfg["model_defaults"]
        assert "candidates" in m_def
        assert "recall_bar" in m_def
        assert 0.0 < m_def["recall_bar"] <= 1.0


def test_canonical_15_feature_contract():
    """Verify canonical feature contract has exactly 15 features in locked order."""
    assert len(CANONICAL_FEATURES) == 15
    expected_15 = [
        "rainfall_1h_mm",
        "rainfall_3h_mm",
        "rainfall_6h_mm",
        "rainfall_24h_mm",
        "rainfall_72h_mm",
        "soil_saturation_pct",
        "deep_soil_saturation_pct",
        "temperature_c",
        "relative_humidity_pct",
        "surface_pressure_hpa",
        "wind_speed_kmh",
        "elevation_m",
        "catchment_slope_deg",
        "dist_to_river_m",
        "upstream_drainage_sqkm",
    ]
    assert CANONICAL_FEATURES == expected_15

    # Bounds check
    for feat in CANONICAL_FEATURES:
        assert feat in PHYSICAL_BOUNDS
        low, high = PHYSICAL_BOUNDS[feat]
        assert low < high


def test_schema_hash_deterministic():
    """Verify compute_schema_hash returns consistent deterministic hash."""
    h1 = compute_schema_hash()
    h2 = compute_schema_hash()
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_feature_vector_validation():
    """Verify feature_contract.validate_feature_values catches out-of-bound or corrupted values."""
    valid_vector = {
        "rainfall_1h_mm": 25.0,
        "rainfall_3h_mm": 50.0,
        "rainfall_6h_mm": 70.0,
        "rainfall_24h_mm": 120.0,
        "rainfall_72h_mm": 180.0,
        "soil_saturation_pct": 75.0,
        "deep_soil_saturation_pct": 70.0,
        "temperature_c": 22.0,
        "relative_humidity_pct": 80.0,
        "surface_pressure_hpa": 920.0,
        "wind_speed_kmh": 15.0,
        "elevation_m": 850.0,
        "catchment_slope_deg": 18.0,
        "dist_to_river_m": 150.0,
        "upstream_drainage_sqkm": 2500.0,
    }
    is_valid, errors = feature_contract.validate_feature_values(valid_vector)
    assert is_valid is True
    assert len(errors) == 0

    # Test out of bounds
    corrupted_vector = valid_vector.copy()
    corrupted_vector["relative_humidity_pct"] = 150.0  # exceeds 100%
    corrupted_vector["soil_saturation_pct"] = -20.0  # below 0%

    is_valid_corr, errors_corr = feature_contract.validate_feature_values(corrupted_vector)
    assert is_valid_corr is False
    assert len(errors_corr) == 2

