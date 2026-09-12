"""
apps/api/app/routers/realtime.py
Flowshield — Real-Time Server-Sent Events (SSE) Stream Router (v3.0)
Smart India Hackathon 2026 (PS ID: 26192)

Streams live telemetry updates, ML risk score changes, and disaster alerts
directly to connected dashboards without continuous HTTP polling.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, Query
from sse_starlette.sse import EventSourceResponse

from ..services.event_bus import event_bus

router = APIRouter(prefix="/realtime", tags=["Real-Time Streaming"])
logger = logging.getLogger("flowshield.realtime")


@router.get("/stream")
async def stream_live_updates(
    request: Request,
    village_id: Optional[str] = Query(None, description="Optional village filter; omit for regional feed")
):
    """
    Establishes an HTTP Server-Sent Events (SSE) connection.
    Pushes instantaneous telemetry, risk score shifts, and high-priority alerts.
    """
    queue = await event_bus.register(village_id=village_id)

    async def event_generator():
        # 1. Immediate handshake event
        yield {
            "event": "handshake",
            "data": json.dumps({
                "status": "connected",
                "filter_village_id": village_id,
                "connected_at": datetime.now(timezone.utc).isoformat(),
                "keepalive_interval_sec": 15
            })
        }

        try:
            while True:
                # Check if client closed the connection
                if await request.is_disconnected():
                    logger.info("Client disconnected from SSE stream.")
                    break

                try:
                    # Wait for an event from the bus with a 15-second timeout for keepalive
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {
                        "event": msg.get("event", "message"),
                        "data": json.dumps(msg)
                    }
                except asyncio.TimeoutError:
                    # Send periodic keepalive heartbeat ping
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({
                            "type": "ping",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                    }
        except asyncio.CancelledError:
            logger.info("SSE streaming task cancelled by client.")
        finally:
            await event_bus.unregister(queue)

    return EventSourceResponse(
        event_generator(),
        ping=15,
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/broadcast")
async def trigger_manual_broadcast(
    event_type: str = Query("manual_test", description="Event name"),
    village_id: Optional[str] = Query(None, description="Village ID"),
    payload: Dict[str, Any] = None
):
    """Test utility to broadcast custom events to active clients."""
    data = payload or {"message": "Test broadcast from Flowshield command console"}
    await event_bus.publish(event_type=event_type, payload=data, village_id=village_id)
    return {"status": "broadcast_dispatched", "event": event_type, "village_id": village_id}
