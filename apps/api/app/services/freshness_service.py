"""
apps/api/app/services/freshness_service.py
Flowshield — Telemetry Freshness & 5-Tier Degradation Service (v2.4)
Enforces provider-specific freshness policies, graceful degradation, and offline survivability.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from ..models.observation import EnvironmentalObservation
from ..models.telemetry_sync_log import TelemetrySyncLog


class FreshnessState(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    UNAVAILABLE = "UNAVAILABLE"


class DegradationTier(int, Enum):
    TIER_1_ONLINE_FULL = 1        # All live scientific feeds active (<30 min old)
    TIER_2_CACHED_FRESH = 2       # Live feeds delayed, serving recent cache (<1 hour old)
    TIER_3_DEGRADED_STALE = 3     # Feeds unreachable, cache 1h-24h old; score capped at 55
    TIER_4_OFFLINE_FALLBACK = 4   # Extended outage (>24h old); static baselines served
    TIER_5_EMERGENCY_MINIMAL = 5  # Complete isolation; SMS / text cards only


class FreshnessService:
    """
    Evaluates observation age against provider-specific freshness policies
    and coordinates the 5-tier system degradation hierarchy.
    """

    def __init__(self):
        # Default policy bounds (in seconds)
        self.default_stale_after = 1800   # 30 minutes
        self.default_hard_expiry = 86400  # 24 hours

    def evaluate_freshness(
        self,
        observation_time: Optional[datetime],
        stale_after_seconds: Optional[int] = None,
        hard_expiry_seconds: Optional[int] = None,
        now: Optional[datetime] = None,
    ) -> Tuple[FreshnessState, int, float]:
        """
        Evaluates the freshness state of an observation.
        Returns:
            (FreshnessState, age_seconds, freshness_factor [0.0 to 1.0])
        """
        if observation_time is None:
            return FreshnessState.UNAVAILABLE, 999999, 0.0

        if now is None:
            now = datetime.now(timezone.utc)

        # Ensure tz-awareness
        if observation_time.tzinfo is None:
            obs_tz = observation_time.replace(tzinfo=timezone.utc)
        else:
            obs_tz = observation_time

        if now.tzinfo is None:
            now_tz = now.replace(tzinfo=timezone.utc)
        else:
            now_tz = now

        age_seconds = max(0, int((now_tz - obs_tz).total_seconds()))

        stale_limit = stale_after_seconds or self.default_stale_after
        expiry_limit = hard_expiry_seconds or self.default_hard_expiry

        if age_seconds <= stale_limit:
            freshness_factor = 1.0 - (0.30 * (age_seconds / max(1, stale_limit)))
            return FreshnessState.FRESH, age_seconds, round(freshness_factor, 3)
        elif age_seconds <= expiry_limit:
            freshness_factor = 0.70 * (1.0 - ((age_seconds - stale_limit) / max(1, expiry_limit - stale_limit)))
            return FreshnessState.STALE, age_seconds, round(max(0.1, freshness_factor), 3)
        else:
            return FreshnessState.EXPIRED, age_seconds, 0.0

    def evaluate_system_status(self, db: Session) -> Dict[str, Any]:
        """
        Queries database for latest telemetry observations and sync logs
        to compute the active 5-Tier Degradation state.
        """
        now = datetime.now(timezone.utc)

        # 1. Latest observation across the database
        latest_obs = (
            db.query(EnvironmentalObservation)
            .order_by(EnvironmentalObservation.timestamp.desc())
            .first()
        )

        latest_time = latest_obs.timestamp if latest_obs else None
        state, age_seconds, factor = self.evaluate_freshness(latest_time, now=now)

        # 2. Determine active Degradation Tier
        if state == FreshnessState.FRESH and age_seconds <= 1800:
            tier = DegradationTier.TIER_1_ONLINE_FULL
            tier_desc = "Online Full Telemetry (Live feeds streaming normally)"
        elif age_seconds <= 3600:
            tier = DegradationTier.TIER_2_CACHED_FRESH
            tier_desc = "Cached Fresh Telemetry (Telemetry within 1 hour)"
        elif age_seconds <= 86400:
            tier = DegradationTier.TIER_3_DEGRADED_STALE
            tier_desc = "Degraded Mode (Telemetry 1h - 24h old; risk scores capped at 55)"
        elif latest_obs is not None:
            tier = DegradationTier.TIER_4_OFFLINE_FALLBACK
            tier_desc = "Offline Fallback (Telemetry >24h old; verified historical baseline)"
        else:
            tier = DegradationTier.TIER_5_EMERGENCY_MINIMAL
            tier_desc = "Emergency Minimal (No telemetry available; emergency cards only)"

        # 3. Query sync logs for provider health
        sync_logs = (
            db.query(TelemetrySyncLog)
            .order_by(TelemetrySyncLog.timestamp.desc())
            .limit(5)
            .all()
        )

        provider_summary = []
        for log in sync_logs:
            provider_summary.append({
                "provider": log.provider,
                "status": log.status,
                "records_updated": log.records_updated,
                "timestamp": log.timestamp.isoformat(),
                "error_message": log.error_message,
            })

        total_obs_count = db.query(EnvironmentalObservation).count()

        return {
            "status": "HEALTHY" if tier.value <= 2 else ("DEGRADED" if tier.value <= 4 else "CRITICAL_OFFLINE"),
            "degradation_tier": tier.value,
            "degradation_tier_name": tier.name,
            "degradation_description": tier_desc,
            "freshness_state": state.value,
            "latest_observation_age_seconds": age_seconds,
            "freshness_quality_factor": factor,
            "latest_observation_timestamp": latest_time.isoformat() if latest_time else None,
            "total_cached_observations": total_obs_count,
            "recent_sync_events": provider_summary,
            "timestamp": now.isoformat(),
        }


freshness_service = FreshnessService()
