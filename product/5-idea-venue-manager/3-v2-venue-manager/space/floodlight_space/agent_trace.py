from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def trace_event(step: str, label: str, tone: str = "neutral", **data: Any) -> dict[str, Any]:
    event: dict[str, Any] = {
        "step": step,
        "label": label,
        "tone": tone,
        "timestamp": utc_now(),
    }
    for key, value in data.items():
        if value is not None:
            event[key] = value
    return event


def add_trace(session: dict[str, Any], step: str, label: str, tone: str = "neutral", **data: Any) -> dict[str, Any]:
    event = trace_event(step, label, tone, **data)
    session.setdefault("agent_trace", []).append(event)
    return event


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
