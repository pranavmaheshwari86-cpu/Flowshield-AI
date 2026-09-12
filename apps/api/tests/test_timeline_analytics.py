"""
apps/api/tests/test_timeline_analytics.py
Unit & integration tests for FlowShield Predictive Risk & Multi-Horizon Timeline
"""

import pytest
from datetime import datetime, timezone
from apps.api.app.services.timeline_service import timeline_service
from apps.api.app.database import SessionLocal


def test_multi_stream_peaks_detection():
    horizons = [1, 3, 6, 12, 24, 48]
    rainfall = [5.0, 12.0, 28.0, 14.0, 4.0, 1.0]      # Peak at +6h
    river_stages = [2.1, 2.4, 3.2, 4.8, 5.6, 5.1]     # Crest at +24h
    risk_scores = [20.0, 35.0, 62.0, 78.0, 84.0, 60.0] # Peak at +24h

    peaks = timeline_service._calculate_multi_stream_peaks(horizons, rainfall, river_stages, risk_scores)
    assert peaks["rainfall_peak_hours"] == 6.0
    assert peaks["river_crest_peak_hours"] == 24.0
    assert peaks["risk_peak_hours"] == 24.0


def test_multi_stream_peaks_flat_plateau():
    horizons = [1, 3, 6, 12, 24, 48]
    rainfall = [1.0, 1.2, 1.1, 1.0, 0.9, 1.0] # < 1.5 mm/h
    river_stages = [None, None, None, None, None, None]
    risk_scores = [15.0, 16.0, 15.5, 16.2, 15.8, 15.1] # range < 4.0

    peaks = timeline_service._calculate_multi_stream_peaks(horizons, rainfall, river_stages, risk_scores)
    assert peaks["rainfall_peak_hours"] is None
    assert peaks["river_crest_peak_hours"] is None
    assert peaks["risk_peak_hours"] is None  # Flat profile correctly detected


def test_lead_time_solver_crossing():
    horizons = [0, 1, 3, 6, 12, 24, 48]
    risks = [15.0, 22.0, 35.0, 45.0, 65.0, 80.0, 50.0] # crosses 50.0 between 6h and 12h
    p90s = [20.0, 30.0, 48.0, 60.0, 78.0, 92.0, 65.0]  # p90 crosses 50.0 between 3h and 6h

    res = timeline_service._calculate_lead_time_to_threshold(horizons, risks, p90s, threshold_value=50.0)
    assert res.is_crossed is True
    # between 6 and 12: fraction = (50 - 45) / (65 - 45) = 5/20 = 0.25 -> 6 + 0.25 * 6 = 7.5h
    assert res.most_likely_crossing_hour == 7.5
    assert res.lead_time_hours == 7.5
    assert res.earliest_crossing_hour < res.most_likely_crossing_hour
    assert "High Risk Threshold (≥ 50.0) expected in ~7.5h" in res.human_status_message


def test_lead_time_solver_already_breached():
    horizons = [0, 1, 3, 6, 12, 24, 48]
    risks = [55.0, 60.0, 70.0, 80.0, 85.0, 90.0, 75.0]
    p90s = [65.0, 70.0, 80.0, 90.0, 95.0, 98.0, 85.0]

    res = timeline_service._calculate_lead_time_to_threshold(horizons, risks, p90s, threshold_value=50.0)
    assert res.is_crossed is True
    assert res.lead_time_hours == 0.0
    assert "CURRENTLY BREACHED" in res.human_status_message


def test_lead_time_solver_no_crossing():
    horizons = [0, 1, 3, 6, 12, 24, 48]
    risks = [10.0, 12.0, 15.0, 18.0, 22.0, 20.0, 14.0]
    p90s = [15.0, 18.0, 22.0, 26.0, 30.0, 28.0, 20.0]

    res = timeline_service._calculate_lead_time_to_threshold(horizons, risks, p90s, threshold_value=50.0)
    assert res.is_crossed is False
    assert res.lead_time_hours is None
    assert "not expected to be crossed within 48h horizon" in res.human_status_message


def test_explainable_risk_drivers():
    drivers = timeline_service._compute_explainable_risk_drivers(
        calibrated_prob=0.5,
        rain_rate=25.0,
        river_surge=0.4,
        soil_sat=70.0,
        slope=20.0
    )
    assert len(drivers) == 4
    # All contributions must be positive
    for d in drivers:
        assert d.contribution_points >= 0.0
        assert len(d.driver_name) > 0
        assert len(d.physical_impact_description) > 0


def test_location_hierarchy_and_detailed_timeline_integration():
    db = SessionLocal()
    try:
        hierarchy = timeline_service.get_location_hierarchy(db)
        assert len(hierarchy.states) > 0
        
        # Test detailed timeline on first settlement
        first_village_id = hierarchy.states[0].districts[0].settlements[0].id
        detailed = timeline_service.get_detailed_timeline(first_village_id, db, force_refresh=True)
        
        assert detailed.settlement.id == first_village_id
        assert len(detailed.forecast_horizons) == 6
        assert len(detailed.historical_series) == 7
        assert detailed.current_situation.rainfall_rate_mm_hr >= 0.0
        assert detailed.data_quality.active_mode in ["LIVE", "DEMO"]
    finally:
        db.close()


def test_buxar_ganga_detailed_timeline():
    """Verify authentic CWC Ganga station binding and zero-fabrication hydrology for Buxar, Bihar."""
    db = SessionLocal()
    try:
        detailed = timeline_service.get_detailed_timeline("bh-07-buxar", db, force_refresh=True)
        assert detailed.settlement.id == "bh-07-buxar"
        assert detailed.settlement.district == "Buxar"
        assert detailed.settlement.state == "Bihar"

        # River & CWC Gauge verification
        assert detailed.hydrology.river_name == "Ganga River (Buxar Reach)"
        assert "Buxar CWC Station" in detailed.hydrology.gauge_station_name
        assert detailed.hydrology.warning_mark_meters == 59.32
        assert detailed.hydrology.danger_mark_meters == 60.32
        assert detailed.hydrology.current_stage_meters == 58.20
        assert detailed.hydrology.margin_to_danger_meters == -2.12

        # Anti-fabrication assertions: no fake dam, no fabricated hydro discharge
        assert detailed.hydrology.upstream_dam_discharge_cumec is None
        assert detailed.hydrology.dam_name is None

        # Series verification: 7 historical points (-6h to NOW), 6 forecast horizons (+1h to +48h)
        assert len(detailed.historical_series) == 7
        assert len(detailed.forecast_horizons) == 6
    finally:
        db.close()

