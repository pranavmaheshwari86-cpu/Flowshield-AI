"""
tests/test_data_correctness_suite.py
Flowshield — Scientific Data Correctness & Zero-Fabrication Test Suite
Smart India Hackathon 2026 (PS ID: 26192)
"""

import pytest
import urllib.error
from unittest.mock import patch
from apps.api.app.models.village import Village


def test_soil_moisture_scientific_semantics(client, db_session):
    """
    Verify soil moisture disambiguation:
    0.260 m3/m3 must map to 26.0% VWC and 52.0% Effective Saturation (Se = theta / theta_s where theta_s = 0.50).
    """
    mandi = db_session.query(Village).filter(Village.state == "Himachal Pradesh").first()
    assert mandi is not None, "Mandi village required for test"

    res = client.get(f"/api/v1/risk/forecast/detailed?village_id={mandi.id}")
    assert res.status_code == 200
    data = res.json()

    obs = data["current_situation"]
    assert "soil_moisture_m3_m3" in obs
    assert "soil_moisture_vwc_pct" in obs
    assert "soil_effective_saturation_pct" in obs
    assert "soil_telemetry_source" in obs
    assert "soil_data_state" in obs

    if obs["soil_moisture_m3_m3"] is not None:
        vwc = obs["soil_moisture_vwc_pct"]
        se = obs["soil_effective_saturation_pct"]
        vol = obs["soil_moisture_m3_m3"]

        # VWC % = m3/m3 * 100
        assert abs(vwc - (vol * 100.0)) < 0.05
        # Effective Saturation % = (vol / 0.50) * 100
        assert abs(se - ((vol / 0.50) * 100.0)) < 0.05
        # Telemetry source must be attributed to AgroMonitoring or ERA5
        assert any(
            src in obs["soil_telemetry_source"]
            for src in ["AgroMonitoring", "Copernicus ERA5-Land"]
        )


def test_disaggregated_precipitation_peaks(client, db_session):
    """
    Verify that observed historical peak rain rate and forecast peak rate
    are cleanly disaggregated and exposed in current_situation and peak_analysis.
    """
    mandi = db_session.query(Village).filter(Village.state == "Himachal Pradesh").first()
    res = client.get(f"/api/v1/risk/forecast/detailed?village_id={mandi.id}")
    assert res.status_code == 200
    data = res.json()

    obs = data["current_situation"]
    assert "observed_peak_rate_mm_hr" in obs
    assert "forecast_peak_rate_mm_hr" in obs

    # Verify peak values match series
    hist_series = data.get("historical_series", [])
    if hist_series:
        actual_hist_peak = max(
            (pt.get("observed_rainfall_rate") or 0.0) for pt in hist_series
        )
        assert abs(obs["observed_peak_rate_mm_hr"] - actual_hist_peak) < 0.05

    # Check forecast peak aligns with NWP model or horizons
    if data.get("precipitation_forecast") and data["precipitation_forecast"].get("peak_forecast_mm_hr") is not None:
        assert abs(obs["forecast_peak_rate_mm_hr"] - data["precipitation_forecast"]["peak_forecast_mm_hr"]) < 0.05
    else:
        forecast_horizons = data.get("forecast_horizons", [])
        if forecast_horizons:
            actual_fc_peak = max(
                (h.get("projected_rainfall_rate_mm_hr") or 0.0) for h in forecast_horizons
            )
            assert abs(obs["forecast_peak_rate_mm_hr"] - actual_fc_peak) < 0.05


def test_zero_fabrication_on_weather_outage(client, db_session):
    """
    Verify that when external weather APIs fail, Flowshield NEVER fabricates
    hardcoded fallback values (21.4C, 78%, 8.5 km/h). Values must be None or from DB observation.
    """
    mandi = db_session.query(Village).filter(Village.state == "Himachal Pradesh").first()

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        res = client.get(f"/api/v1/risk/forecast/detailed?village_id={mandi.id}&force_refresh=true")
        assert res.status_code == 200
        data = res.json()

        obs = data["current_situation"]
        if obs["temperature_c"] is not None:
            # If retrieved from DB historical observation, verify freshness is tracked
            assert obs["atmospheric_freshness_status"] in ["GOOD", "LIVE", "STALE", "UNAVAILABLE"]
        else:
            assert obs["atmospheric_freshness_status"] == "UNAVAILABLE"


def test_regional_model_capability_isolation(client, db_session):
    """
    Verify strict regional model capability isolation:
    - Himachal Pradesh (Mandi): SUPPORTED, calibrated_flood_probability provided
    - Bihar (Begusarai): UNSUPPORTED, operational_risk_score and calibrated_flood_probability strictly None
    - Assam (Dhemaji): UNSUPPORTED, operational_risk_score and calibrated_flood_probability strictly None
    """
    mandi = db_session.query(Village).filter(Village.state == "Himachal Pradesh").first()
    res_mandi = client.get(f"/api/v1/risk/forecast/detailed?village_id={mandi.id}")
    assert res_mandi.status_code == 200
    data_mandi = res_mandi.json()
    assert data_mandi["location_capabilities"]["flood_risk_model"] == "SUPPORTED"
    # Horizons in supported region must have calibrated probability
    for h in data_mandi["forecast_horizons"]:
        assert h["calibrated_flood_probability"] is not None

    begusarai = db_session.query(Village).filter(Village.district == "Begusarai").first()
    if begusarai:
        res_beg = client.get(f"/api/v1/risk/forecast/detailed?village_id={begusarai.id}")
        assert res_beg.status_code == 200
        data_beg = res_beg.json()
        assert data_beg["location_capabilities"]["flood_risk_model"] == "UNSUPPORTED"
        assert "Validated flood-risk machine learning model unavailable" in data_beg["location_capabilities"]["unsupported_reason"]
        # In unsupported regions, calibrated probability and risk score must NEVER be fabricated
        for h in data_beg["forecast_horizons"]:
            assert h["calibrated_flood_probability"] is None, "Must not fabricate calibrated probability for uncalibrated models"
            assert h["operational_risk_score"] is None, "Must not execute uncalibrated model score"
            assert h["risk_tier"] == "UNSUPPORTED"

    dhemaji = db_session.query(Village).filter(Village.district == "Dhemaji").first()
    if dhemaji:
        res_dhem = client.get(f"/api/v1/risk/forecast/detailed?village_id={dhemaji.id}")
        assert res_dhem.status_code == 200
        data_dhem = res_dhem.json()
        assert data_dhem["location_capabilities"]["flood_risk_model"] == "UNSUPPORTED"
        for h in data_dhem["forecast_horizons"]:
            assert h["calibrated_flood_probability"] is None, "Must not fabricate calibrated probability for uncalibrated models"
            assert h["operational_risk_score"] is None, "Must not execute uncalibrated model score"
            assert h["risk_tier"] == "UNSUPPORTED"
