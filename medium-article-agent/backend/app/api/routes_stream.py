"""SSE streaming routes."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.events.event_bus import event_bus

router = APIRouter()


@router.get("/{run_id}")
async def stream_run(run_id: str, request: Request):
    async def event_generator():
        q = event_bus.subscribe(run_id)
        try:
            yield {"event": "connected", "data": json.dumps({"run_id": run_id})}
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield {
                        "event": event.get("type", "log"),
                        "data": json.dumps(event.get("data", event)),
                    }
                except asyncio.TimeoutError:
                    yield {"event": "heartbeat", "data": "{}"}
        finally:
            event_bus.unsubscribe(run_id, q)

    return EventSourceResponse(event_generator())
