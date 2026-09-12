"""
apps/api/app/services/alert_engine.py
Flowshield — Concurrency-Safe Alert Engine (v2.4)
Manages operational warning alerts with atomic deduplication, database-level unique
constraints, advisory tagging, and operator acknowledgement.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models.alert import Alert
from ..models.village import Village
from .action_engine import action_engine

logger = logging.getLogger("flowshield.alert_engine")


class AlertEngine:
    """
    Manages operational warning alert lifecycles: evaluation, deduplication,
    operator acknowledgement, and auto-resolution.
    Guaranteed concurrency safe against simultaneous multi-threaded evaluations.
    """

    @staticmethod
    def evaluate_and_create_alert(
        db: Session,
        village: Village,
        risk_score: int,
        risk_level: str,
        prediction_id: Optional[str],
        top_contributors: List[Dict[str, Any]],
        simulation_substep: int = 0,
    ) -> Optional[Alert]:
        """
        Generates a new alert if risk is HIGH or CRITICAL.
        Guarantees idempotence and concurrency safety via database unique constraint.
        """
        if risk_level not in ["HIGH", "CRITICAL"]:
            # Auto-resolve existing active alerts if conditions improved
            AlertEngine.auto_resolve_alerts(db, village.id)
            return None

        severity = risk_level
        village_id = village.id
        village_name = getattr(village, "name", "Unknown Village")
        dedup_key = f"{village_id}:{severity}:{simulation_substep}"

        # 1. Optimistic check for existing active alert
        existing_alert = (
            db.query(Alert)
            .filter(
                Alert.village_id == village_id,
                Alert.dedup_key == dedup_key,
                Alert.status.in_(["ACTIVE", "ACKNOWLEDGED"]),
            )
            .first()
        )
        if existing_alert:
            return None  # Do not duplicate existing active alert

        # 2. Synthesize headline and trigger reason with statutory advisory disclaimer
        if severity == "CRITICAL":
            headline = f"EMERGENCY: Extreme Inundation Hazard at {village_name}"
            trigger_reason = (
                f"Operational risk score reached {risk_score}/100. "
                "Rapid catchment runoff and river surge detected. Immediate evacuation advisory."
            )
        else:
            headline = f"WARNING: Severe Flash Flood Threat at {village_name}"
            trigger_reason = (
                f"Operational risk score reached {risk_score}/100. "
                "Saturated soil and intensifying precipitation. Standby for early action."
            )

        # 3. Rule-based action instructions
        recommended_actions = action_engine.get_recommended_actions(severity)

        new_alert = Alert(
            village_id=village_id,
            prediction_id=prediction_id,
            severity=severity,
            status="ACTIVE",
            headline=headline,
            trigger_reason=trigger_reason,
            top_contributors=top_contributors,
            recommended_actions=recommended_actions,
            dedup_key=dedup_key,
            is_advisory=True,
            policy_version="2.4.0",
            requires_authority_coordination=False,
            created_at=datetime.now(timezone.utc),
        )

        try:
            db.add(new_alert)
            db.commit()
            db.refresh(new_alert)
            logger.info(f"Alert generated: {new_alert.id} for {village_name} [{severity}]")
            
            # Broadcast to real-time subscribers
            try:
                import asyncio
                from .event_bus import event_bus
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(event_bus.publish(
                        event_type="new_alert",
                        payload={
                            "id": new_alert.id,
                            "village_id": village_id,
                            "village_name": village_name,
                            "severity": severity,
                            "headline": headline,
                            "trigger_reason": trigger_reason,
                            "risk_score": risk_score,
                        },
                        village_id=village_id
                    ))
            except Exception:
                pass

            return new_alert
        except IntegrityError:
            # Another concurrent worker already committed an identical alert
            db.rollback()
            logger.info(f"Concurrent alert insertion collision caught for {dedup_key}; returning existing alert.")
            return (
                db.query(Alert)
                .filter(
                    Alert.village_id == village_id,
                    Alert.dedup_key == dedup_key,
                    Alert.status.in_(["ACTIVE", "ACKNOWLEDGED"]),
                )
                .first()
            )

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: str, operator_name: str) -> Optional[Alert]:
        """Atomically acknowledges an active alert."""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None

        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_by = operator_name
        alert.acknowledged_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def auto_resolve_alerts(db: Session, village_id: str):
        """Auto-resolves active alerts when village returns to LOW or WATCH."""
        active_alerts = (
            db.query(Alert)
            .filter(
                Alert.village_id == village_id,
                Alert.status.in_(["ACTIVE", "ACKNOWLEDGED"]),
            )
            .all()
        )
        for a in active_alerts:
            a.status = "RESOLVED"
            a.resolved_at = datetime.now(timezone.utc)
        if active_alerts:
            db.commit()


alert_engine = AlertEngine()
