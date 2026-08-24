"""JSON-safe snapshots so a reload does not lose the draft."""

from __future__ import annotations

from typing import Any

_SKIP_KEYS = {"uploaded_files"}


def jsonable(value: Any, *, _key: str | None = None) -> Any:
    if _key in _SKIP_KEYS:
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(k): jsonable(v, _key=str(k)) for k, v in value.items() if k not in _SKIP_KEYS}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, bytes):
        return ""
    if hasattr(value, "value"):
        try:
            return value.value
        except Exception:
            pass
    return str(value)


def snapshot_for_db(state: dict[str, Any]) -> dict[str, Any]:
    return jsonable(state)
