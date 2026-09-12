"""
apps/api/tests/test_ai_intelligence.py
Unit tests for AI explanations, web intelligence feeds, and provider failover.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ai_status_endpoint():
    """Tests GET /api/v1/ai/status."""
    response = client.get("/api/v1/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "active_provider" in data
    assert "fallback_ready" in data
    assert data["fallback_ready"] is True


def test_ai_explanation_english():
    """Tests POST /api/v1/ai/explain with English language request."""
    payload = {
        "village_id": "mandi_sadar",
        "village_name": "Mandi Sadar",
        "risk_score": 82.5,
        "risk_level": "CRITICAL",
        "flood_probability": 0.88,
        "key_factors": ["Torrential rainfall 65mm/3h", "Soil saturation 88%"],
        "telemetry_summary": {
            "rainfall_1h_mm": 24.5,
            "rainfall_24h_mm": 95.0,
            "soil_saturation_pct": 88.0,
            "dist_to_river_m": 85.0
        },
        "language": "en"
    }
    response = client.post("/api/v1/ai/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert len(data["summary"]) > 10
    assert "detailed_analysis" in data
    assert "immediate_actions" in data
    assert isinstance(data["immediate_actions"], list)
    assert len(data["immediate_actions"]) > 0
    assert "provider" in data


def test_ai_explanation_hindi():
    """Tests POST /api/v1/ai/explain with Hindi language request."""
    payload = {
        "village_id": "pandoh_dam",
        "village_name": "Pandoh Dam Sector",
        "risk_score": 76.0,
        "risk_level": "CRITICAL",
        "flood_probability": 0.82,
        "key_factors": ["High reservoir discharge"],
        "telemetry_summary": {
            "rainfall_1h_mm": 18.0,
            "rainfall_24h_mm": 80.0,
            "soil_saturation_pct": 91.0
        },
        "language": "hi"
    }
    response = client.post("/api/v1/ai/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "detailed_analysis" in data
    assert "immediate_actions" in data


def test_web_intelligence_feed():
    """Tests GET /api/v1/ai/intelligence."""
    response = client.get("/api/v1/ai/intelligence?region=Himachal%20Pradesh")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0
    assert "total" in data
    assert "region_summary" in data
