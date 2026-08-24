"""LangGraph SQLite checkpointer."""

from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from typing import AsyncIterator

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.config import get_settings

_checkpointer: SqliteSaver | None = None


def get_checkpointer() -> SqliteSaver:
    """Sync saver for tests and linear invoke."""
    global _checkpointer
    if _checkpointer is None:
        settings = get_settings()
        conn = sqlite3.connect(str(settings.checkpoint_path), check_same_thread=False)
        _checkpointer = SqliteSaver(conn)
        _checkpointer.setup()
    return _checkpointer


@asynccontextmanager
async def async_checkpointer() -> AsyncIterator[AsyncSqliteSaver]:
    """Async saver required by graph.astream / ainvoke."""
    settings = get_settings()
    async with AsyncSqliteSaver.from_conn_string(str(settings.checkpoint_path)) as saver:
        yield saver
