"""
apps/api/app/services/event_bus.py
Flowshield — Real-Time Disaster Event Bus & SSE PubSub (v3.0)
Smart India Hackathon 2026 (PS ID: 26192)

Provides an asynchronous, zero-dependency event bus for broadcasting
real-time telemetry updates, risk level escalations, and newly triggered
disaster alerts to frontend dashboards via Server-Sent Events (SSE).
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Set

logger = logging.getLogger("flowshield.event_bus")


class DisasterEventBus:
    """Pub/Sub event dispatcher for real-time early warning streaming."""

    def __init__(self):
        # Maps queue to optional village_id filter (None = receive all)
        self._subscribers: Dict[asyncio.Queue, Optional[str]] = {}
        self._lock = asyncio.Lock()

    async def register(self, village_id: Optional[str] = None) -> asyncio.Queue:
        """Subscribes a new client and returns their listening queue."""
        q = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers[q] = village_id
        logger.info(f"New SSE client registered (filter: village_id={village_id}). Total: {len(self._subscribers)}")
        return q

    async def unregister(self, q: asyncio.Queue):
        """Unsubscribes a client queue upon disconnection."""
        async with self._lock:
            if q in self._subscribers:
                del self._subscribers[q]
        logger.info(f"SSE client disconnected. Remaining active: {len(self._subscribers)}")

    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        village_id: Optional[str] = None
    ):
        """
        Broadcasts an event to matching subscribers.
        Events include: 'telemetry_update', 'risk_escalation', 'new_alert', 'alert_resolved', 'heartbeat'.
        """
        message = {
            "event": event_type,
            "village_id": village_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        }

        async with self._lock:
            subscribers_snapshot = list(self._subscribers.items())

        for q, target_village in subscribers_snapshot:
            # Deliver if subscriber is global (target_village is None) or matches specific village
            if target_village is None or target_village == village_id:
                try:
                    q.put_nowait(message)
                except asyncio.QueueFull:
                    # Queue is overflowing; discard oldest or skip
                    try:
                        q.get_nowait()
                        q.put_nowait(message)
                    except Exception:
                        pass

    def publish_sync(self, event_type: str, payload: Dict[str, Any], village_id: Optional[str] = None):
        """Synchronous wrapper to safely schedule broadcast onto the running event loop."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.publish(event_type, payload, village_id))
        except RuntimeError:
            pass


# Global singleton instance
event_bus = DisasterEventBus()
