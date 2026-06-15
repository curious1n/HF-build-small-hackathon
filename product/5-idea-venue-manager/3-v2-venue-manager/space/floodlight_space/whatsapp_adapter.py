from __future__ import annotations

from hashlib import sha256
from typing import Any
from uuid import uuid4

from floodlight_space.agent_trace import utc_now


def normalize_simulator_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    text = str(payload.get("text") or payload.get("message") or "").strip()
    sender_phone = str(payload.get("sender_phone") or payload.get("phone") or "").strip()
    return {
        "adapter": "simulator",
        "message_id": str(payload.get("message_id") or f"sim-{uuid4().hex[:12]}"),
        "sender_phone": sender_phone,
        "received_at": str(payload.get("received_at") or utc_now()),
        "text": text,
        "provider_metadata": payload.get("provider_metadata") if isinstance(payload.get("provider_metadata"), dict) else {},
    }


def normalize_baileys_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    if str(payload.get("adapter") or "").strip() != "baileys":
        raise ValueError("unsupported_adapter")

    text = str(payload.get("text") or payload.get("message") or "").strip()
    if not text:
        raise ValueError("empty_text")

    provider_metadata = payload.get("provider_metadata") if isinstance(payload.get("provider_metadata"), dict) else {}
    message_type = str(provider_metadata.get("message_type") or "conversation")
    if message_type != "conversation":
        raise ValueError("unsupported_message_type")

    chat_jid = str(payload.get("chat_jid") or "")
    sender_jid = str(payload.get("sender_jid") or chat_jid)
    sender_phone = str(payload.get("sender_phone") or "").strip()
    if not normalize_phone(sender_phone):
        sender_phone = f"+{_phone_from_jid(sender_jid or chat_jid)}" if _phone_from_jid(sender_jid or chat_jid) else ""

    safe_metadata = {
        key: value
        for key, value in provider_metadata.items()
        if key not in {"chat_jid", "sender_jid", "raw_jid", "jid"}
    }
    if chat_jid:
        safe_metadata["chat_jid_hash"] = _hash_identifier(chat_jid)
    if sender_jid:
        safe_metadata["sender_jid_hash"] = _hash_identifier(sender_jid)
    safe_metadata.setdefault("message_type", message_type)
    safe_metadata.setdefault("source", "baileys")

    return {
        "adapter": "baileys",
        "message_id": str(payload.get("message_id") or f"baileys-{uuid4().hex[:12]}"),
        "sender_phone": sender_phone,
        "received_at": str(payload.get("received_at") or utc_now()),
        "text": text,
        "provider_metadata": safe_metadata,
    }


def conversation_key(payload: dict[str, Any], envelope: dict[str, Any]) -> str:
    explicit = payload.get("session_id") or payload.get("conversation_id")
    if explicit:
        return str(explicit)
    phone = normalize_phone(envelope.get("sender_phone"))
    if phone:
        if envelope.get("adapter") == "baileys":
            return f"wa-{phone}"
        return f"sim-{phone}"
    return f"sim-message-{envelope['message_id']}"


def normalize_phone(value: Any) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _phone_from_jid(value: str) -> str:
    return normalize_phone(str(value or "").split("@")[0])


def _hash_identifier(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:16]}"
