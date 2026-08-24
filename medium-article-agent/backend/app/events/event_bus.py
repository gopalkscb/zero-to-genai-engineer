"""In-process pub/sub event bus by run_id."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, AsyncIterator


class EventBus:
    def __init__(self):
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, run_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._queues[run_id].append(q)
        return q

    def unsubscribe(self, run_id: str, queue: asyncio.Queue):
        if run_id in self._queues and queue in self._queues[run_id]:
            self._queues[run_id].remove(queue)

    async def publish(self, run_id: str, event: dict[str, Any]):
        for q in self._queues.get(run_id, []):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    async def stream(self, run_id: str) -> AsyncIterator[dict[str, Any]]:
        q = self.subscribe(run_id)
        try:
            while True:
                event = await q.get()
                yield event
        finally:
            self.unsubscribe(run_id, q)


event_bus = EventBus()
