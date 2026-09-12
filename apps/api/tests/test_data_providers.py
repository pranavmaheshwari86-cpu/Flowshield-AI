"""
apps/api/tests/test_data_providers.py
Flowshield — Data Providers & Freshness Policy Unit Tests (Phase 1 Gate)
"""

import pytest
from apps.api.app.services.providers import (
    LocationTarget,
    OpenMeteoProvider,
    CwcRiverGaugeProvider,
    HistoricalReplayProvider,
    VERIFIED_CWC_GAUGES,
)
from apps.api.app.schemas.observation import SourceType, DataState, DataQualityStatus


def test_open_meteo_provider_metadata():
    """Verify OpenMeteoProvider metadata, freshness policy, and provenance."""
    provider = OpenMeteoProvider()
    assert provider.name == "Open-Meteo / ECMWF Numerical Telemetry"
    assert provider.source_type == SourceType.REANALYSIS

    policy = provider.freshness_policy()
    assert policy.expected_update_interval_sec == 3600
    assert policy.stale_after_sec == 7200
    assert policy.hard_expiry_sec == 21600

    prov = provider.provenance()
    assert prov["is_synthetic"] is False
    assert "Open-Meteo" in prov["provider"]


def test_open_meteo_provider_normalization_fallback():
    """Verify that when OpenMeteo payload is corrupt or invalid, provider degrades to INSUFFICIENT_DATA safely."""
    provider = OpenMeteoProvider()
    target = LocationTarget(id="LOC-1", name="Pandoh", latitude=31.67, longitude=77.05)

    # Empty payload
    normalized = provider.normalize({"error": "Simulated upstream 503 outage"}, [target])
    assert len(normalized) == 1
    obs = normalized[0]
    assert obs.location_id == "LOC-1"
    assert obs.data_state == DataState.INSUFFICIENT_DATA
    assert obs.data_quality_status == DataQualityStatus.INSUFFICIENT_DATA
    assert obs.data_quality_score == 0.0


def test_cwc_river_gauge_provider_matched_and_unmonitored():
    """Verify that CWC gauge provider correctly matches verified stations (e.g. Gandhi Ghat, Patna)
    and labels mountain catchments as UNAVAILABLE/UNMONITORED instead of fabricating gauge numbers."""
    provider = CwcRiverGaugeProvider()
    assert provider.source_type == SourceType.OFFICIAL

    # Target 1: Near Patna Gandhi Ghat
    patna_target = LocationTarget(id="VIL-PATNA", name="Patna Urban", latitude=25.62, longitude=85.17)
    # Target 2: Deep Mountain Catchment in Mandi (Son Khad, no CWC gauge)
    mandi_target = LocationTarget(id="VIL-MANDI", name="Sambhal Ravine", latitude=31.81, longitude=76.81)

    raw = provider.fetch([patna_target, mandi_target])
    is_valid, errors = provider.validate(raw)
    assert is_valid is True

    normalized = provider.normalize(raw, [patna_target, mandi_target])
    assert len(normalized) == 2

    # Verify Patna reading is matched to Gandhi Ghat verified telemetry
    patna_obs = next(o for o in normalized if o.location_id == "VIL-PATNA")
    assert patna_obs.river_level_m == 49.82
    assert patna_obs.river_level_change_m == 1.22
    assert patna_obs.data_state == DataState.OBSERVED
    assert patna_obs.data_quality_status == DataQualityStatus.VALID

    # Verify Mandi mountain reading is explicitly UNAVAILABLE (never fabricated!)
    mandi_obs = next(o for o in normalized if o.location_id == "VIL-MANDI")
    assert mandi_obs.river_level_m is None
    assert mandi_obs.data_state == DataState.UNAVAILABLE
    assert "Unmonitored" in mandi_obs.metadata["notice"]


def test_historical_replay_provider_semantic_integrity():
    """Verify that historical replay provider strictly flags output as HISTORICAL or SIMULATION,
    and NEVER marks historical records as OBSERVED."""
    replay_hist = HistoricalReplayProvider(is_simulation=False)
    assert replay_hist.source_type == SourceType.HISTORICAL

    target = LocationTarget(id="LOC-HIST-1", name="Mandi Town", latitude=31.70, longitude=76.93)
    raw = replay_hist.fetch([target])
    normalized = replay_hist.normalize(raw, [target])

    assert len(normalized) == 1
    obs = normalized[0]
    assert obs.data_state == DataState.HISTORICAL
    assert obs.data_state != DataState.OBSERVED  # Absolute rule: HISTORICAL != OBSERVED

    # Test simulation flag
    replay_sim = HistoricalReplayProvider(is_simulation=True)
    assert replay_sim.source_type == SourceType.SIMULATION
    norm_sim = replay_sim.normalize(raw, [target])
    assert norm_sim[0].data_state == DataState.SIMULATION
    assert norm_sim[0].data_state != DataState.OBSERVED
