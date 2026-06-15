from __future__ import annotations

from copy import deepcopy
from typing import Any

from floodlight_space.agent_trace import utc_now


class InMemoryConversationStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    def reset(self) -> None:
        self._sessions = {}

    def get(self, session_id: str) -> dict[str, Any] | None:
        session = self._sessions.get(session_id)
        return deepcopy(session) if session else None

    def get_mutable(self, session_id: str) -> dict[str, Any] | None:
        return self._sessions.get(session_id)

    def save(self, session: dict[str, Any]) -> dict[str, Any]:
        self._sessions[str(session["session_id"])] = session
        return deepcopy(session)

    def get_or_create(self, session_id: str, envelope: dict[str, Any], trace_id: str) -> dict[str, Any]:
        session = self._sessions.get(session_id)
        if session:
            return session
        session = {
            "session_id": session_id,
            "trace_id": trace_id,
            "player_phone": envelope.get("sender_phone"),
            "status": "new",
            "terminal_state": None,
            "turn_count": 0,
            "turns": [],
            "candidate_extraction": {},
            "approved_extraction": {},
            "model_validation": {},
            "truth_check_initial": {},
            "truth_check_final": {},
            "booking_record": {},
            "owner_review_action": None,
            "owner_correction_diff": [],
            "outbound_message": {"channel": "whatsapp_simulator", "delivery_state": "not_sent", "text": ""},
            "send_adapter": {"adapter": "simulator", "delivery_state": "not_sent"},
            "owner_review_required": False,
            "approval_source": None,
            "agent_trace": [],
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
        self._sessions[session_id] = session
        return session


def public_session(session: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(session)
