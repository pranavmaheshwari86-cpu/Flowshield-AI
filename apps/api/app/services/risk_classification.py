"""
apps/api/app/services/risk_classification.py
Flowshield — Centralized Risk Classification Engine
Smart India Hackathon 2026 (Problem Statement ID: 26192)

Single source of truth for flood risk classification:
- LOW: 0% to 24% (probability < 0.25)
- WATCH: 25% to 49% (0.25 <= probability < 0.50)
- HIGH: 50% to 74% (0.50 <= probability < 0.75)
- CRITICAL: 75% to 100% (probability >= 0.75)
"""

from typing import Dict, Any, Literal, Tuple

RiskTier = Literal["LOW", "WATCH", "HIGH", "CRITICAL"]

# Centralized threshold boundaries
RISK_THRESHOLDS = {
    "LOW": {"min": 0.0, "max": 0.25, "score_max": 25.0, "color": "#10B981", "badge": "Normal State"},
    "WATCH": {"min": 0.25, "max": 0.50, "score_max": 50.0, "color": "#EAB308", "badge": "Advisory Warning"},
    "HIGH": {"min": 0.50, "max": 0.75, "score_max": 75.0, "color": "#F97316", "badge": "Elevated Danger"},
    "CRITICAL": {"min": 0.75, "max": 1.0, "score_max": 100.0, "color": "#EF4444", "badge": "Emergency Surge"},
}


def classify_flood_probability(probability: float) -> RiskTier:
    """
    Classifies a flood probability in [0.0, 1.0] into one of 4 standardized tiers:
    LOW (<0.25), WATCH (0.25-0.49), HIGH (0.50-0.74), CRITICAL (>=0.75).
    """
    prob = max(0.0, min(1.0, float(probability)))
    if prob >= RISK_THRESHOLDS["CRITICAL"]["min"]:
        return "CRITICAL"
    elif prob >= RISK_THRESHOLDS["HIGH"]["min"]:
        return "HIGH"
    elif prob >= RISK_THRESHOLDS["WATCH"]["min"]:
        return "WATCH"
    return "LOW"


def classify_risk_score(score: float) -> RiskTier:
    """
    Classifies an operational multi-factor score in [0.0, 100.0] into a standardized tier.
    """
    s = max(0.0, min(100.0, float(score)))
    if s >= 75.0:
        return "CRITICAL"
    elif s >= 50.0:
        return "HIGH"
    elif s >= 25.0:
        return "WATCH"
    return "LOW"


def get_risk_metadata(tier: RiskTier) -> Dict[str, Any]:
    """Returns visual and operational metadata for a risk tier."""
    return RISK_THRESHOLDS.get(tier, RISK_THRESHOLDS["LOW"])


def format_probability_percentage(probability: float) -> str:
    """Formats float in [0.0, 1.0] as a human-readable percentage string (e.g. 0.68 -> '68%')."""
    pct = round(max(0.0, min(1.0, float(probability))) * 100.0)
    return f"{pct}%"
