"""
apps/api/app/services/risk_engine.py
Flowshield — Operational Risk & Administrative Policy Engine (v2.4)

Decouples statistical ML flood probability from administrative prioritization.
Reads rules and weights from config/operational_policy.yaml with resilient defaults.
"""

import os
import yaml
import logging
from typing import Tuple, Dict, Any, List, Optional

logger = logging.getLogger("flowshield.risk_engine")

CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../config/operational_policy.yaml")
)

# Hardened default policy if config file is missing or unreadable
DEFAULT_POLICY: Dict[str, Any] = {
    "version": "2.4.0",
    "decision_threshold": 0.08,
    "severity_bands": {
        "critical": {"min_probability": 0.50, "min_policy_score": 75, "color_hex": "#ef4444"},
        "high": {"min_probability": 0.08, "min_policy_score": 50, "color_hex": "#f97316"},
        "watch": {"min_probability": 0.04, "min_policy_score": 25, "color_hex": "#f59e0b"},
        "low": {"min_probability": 0.00, "min_policy_score": 0, "color_hex": "#10b981"},
        "insufficient_data": {"color_hex": "#6b7280"},
    },
    "prioritization_weights": {
        "demographic_vulnerability": 0.35,
        "critical_infrastructure": 0.25,
        "population_density": 0.20,
        "topographic_exposure": 0.20,
    },
    "trend_multipliers": {
        "rising": {"threshold_delta": 15.0, "multiplier": 1.20},
        "falling": {"threshold_delta": -10.0, "multiplier": 0.85},
        "stable": {"multiplier": 1.00},
    },
    "safety_guardrails": {
        "stale_data_seconds": 3600,
        "min_data_quality_score": 0.60,
        "degraded_score_cap": 55,
    },
}


class RiskEngine:
    """
    Evaluates Operational Decision Risk Score (0-100) and Severity Tiers
    governed by disaster management administrative policy.
    """

    def __init__(self, config_path: str = CONFIG_PATH):
        self.config_path = config_path
        self.policy = self._load_policy()

    def _load_policy(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        return data
            except Exception as e:
                logger.warning(f"Failed to parse {self.config_path}: {e}. Using DEFAULT_POLICY.")
        return DEFAULT_POLICY

    def reload_policy(self) -> None:
        """Hot-reload operational policy parameters."""
        self.policy = self._load_policy()

    def compute_operational_risk(
        self,
        flood_probability: float,
        trend_factor: float = 1.0,
        vulnerability_index: float = 0.5,
        data_quality_score: float = 1.0,
        freshness_seconds: int = 0,
        critical_infrastructure_index: float = 0.5,
        population_density_index: float = 0.5,
        topographic_factor: float = 0.5,
    ) -> Tuple[int, str, str, bool]:
        """
        Computes the operational prioritization score (0-100) and maps the operational severity tier.
        Returns:
            (risk_score, risk_level, color_hex, is_capped_by_quality)
        """
        # Guardrail: Check for insufficient data
        if data_quality_score < 0.1:
            return 0, "INSUFFICIENT_DATA", "#6b7280", True

        weights = self.policy.get("prioritization_weights", DEFAULT_POLICY["prioritization_weights"])
        w_vuln = weights.get("demographic_vulnerability", 0.35)
        w_infra = weights.get("critical_infrastructure", 0.25)
        w_pop = weights.get("population_density", 0.20)
        w_topo = weights.get("topographic_exposure", 0.20)

        # 1. Normalized piecewise hazard ratio scaled to 0.50 at threshold tau
        prob = max(0.0, min(1.0, float(flood_probability)))
        tau = float(self.policy.get("decision_threshold", DEFAULT_POLICY["decision_threshold"]))

        if prob < tau:
            hazard_ratio = (prob / max(1e-4, tau)) * 0.50
        else:
            hazard_ratio = 0.50 + 0.50 * ((prob - tau) / max(1e-4, 1.0 - tau))
        hazard_ratio = max(0.0, min(1.0, hazard_ratio))

        # 2. Exposure & vulnerability factor from administrative policy
        exposure_factor = (
            w_vuln * max(0.0, min(1.0, vulnerability_index))
            + w_infra * max(0.0, min(1.0, critical_infrastructure_index))
            + w_pop * max(0.0, min(1.0, population_density_index))
            + w_topo * max(0.0, min(1.0, topographic_factor))
        )
        exposure_factor = max(0.0, min(1.0, exposure_factor))

        # 3. Base operational score combining physical hazard and societal exposure
        w_hazard = float(self.policy.get("hazard_weight", 0.50))
        base_operational = (hazard_ratio * w_hazard) + (exposure_factor * (1.0 - w_hazard))
        raw_score = base_operational * float(trend_factor) * 100.0

        # 4. Data quality & staleness guardrails
        guardrails = self.policy.get("safety_guardrails", DEFAULT_POLICY["safety_guardrails"])
        max_age = guardrails.get("stale_data_seconds", 3600)
        min_quality = guardrails.get("min_data_quality_score", 0.60)
        cap_val = guardrails.get("degraded_score_cap", 55)

        is_capped = False
        if data_quality_score < min_quality or freshness_seconds > max_age:
            if raw_score > cap_val:
                raw_score = float(cap_val)
                is_capped = True

        risk_score = int(round(min(100.0, max(0.0, raw_score))))

        # 5. Operational Severity Tier Mapping
        # Strictly decoupled: uses probability thresholds OR administrative policy scores
        bands = self.policy.get("severity_bands", DEFAULT_POLICY["severity_bands"])
        crit_band = bands.get("critical", {})
        high_band = bands.get("high", {})
        watch_band = bands.get("watch", {})
        low_band = bands.get("low", {})

        tau = self.policy.get("decision_threshold", 0.08)

        if prob >= crit_band.get("min_probability", 0.50) or risk_score >= crit_band.get("min_policy_score", 75):
            risk_level = "CRITICAL"
            color_hex = crit_band.get("color_hex", "#ef4444")
        elif prob >= tau or risk_score >= high_band.get("min_policy_score", 50):
            risk_level = "HIGH"
            color_hex = high_band.get("color_hex", "#f97316")
        elif prob >= watch_band.get("min_probability", 0.04) or risk_score >= watch_band.get("min_policy_score", 25):
            risk_level = "WATCH"
            color_hex = watch_band.get("color_hex", "#f59e0b")
        else:
            risk_level = "LOW"
            color_hex = low_band.get("color_hex", "#10b981")

        return risk_score, risk_level, color_hex, is_capped

    def calculate_trend_factor(self, previous_scores: List[float]) -> Tuple[float, str]:
        """Calculates trend direction and multiplier from recent historical risk snapshots."""
        if not previous_scores or len(previous_scores) < 2:
            return 1.0, "STABLE"

        delta = previous_scores[-1] - previous_scores[0]
        trends = self.policy.get("trend_multipliers", DEFAULT_POLICY["trend_multipliers"])
        rising = trends.get("rising", {"threshold_delta": 15.0, "multiplier": 1.20})
        falling = trends.get("falling", {"threshold_delta": -10.0, "multiplier": 0.85})

        if delta >= rising.get("threshold_delta", 15.0):
            return float(rising.get("multiplier", 1.20)), "RISING"
        elif delta <= falling.get("threshold_delta", -10.0):
            return float(falling.get("multiplier", 0.85)), "FALLING"
        else:
            return 1.00, "STABLE"


risk_engine = RiskEngine()
