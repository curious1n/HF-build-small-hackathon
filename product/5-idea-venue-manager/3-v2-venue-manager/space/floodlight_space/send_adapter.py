from __future__ import annotations

from typing import Any

from floodlight_space.agent_trace import utc_now


def simulator_send(*, session_id: str, envelope: dict[str, Any], message: dict[str, Any]) -> dict[str, Any]:
    text = str(message.get("text") or "").strip()
    if not text:
        return {
            "adapter": "simulator",
            "delivery_state": "not_sent",
            "reason": "empty_message",
        }
    return {
        "adapter": "simulator",
        "delivery_state": "simulated_sent",
        "sent_at": utc_now(),
        "session_id": session_id,
        "recipient_phone": envelope.get("sender_phone"),
        "message_text": text,
        "provider_message_id": f"sim-out-{session_id}-{utc_now()}",
    }
