from __future__ import annotations

from typing import Any

from floodlight_space.agent_trace import add_trace, utc_now
from floodlight_space.booking_rules import (
    build_booking_record,
    build_reply_draft,
    evaluate_booking_candidate,
)
from floodlight_space.conversation_store import InMemoryConversationStore, public_session
from floodlight_space.extraction_adapter import fixture_extraction_from_payload
from floodlight_space.owner_review import merge_candidate
from floodlight_space.whatsapp_adapter import conversation_key, normalize_baileys_envelope, normalize_simulator_envelope


def process_simulated_message(
    *,
    payload: dict[str, Any],
    venue_context: dict[str, Any],
    store: InMemoryConversationStore,
) -> dict[str, Any]:
    trace_id = str(payload.get("trace_id") or payload.get("message_id") or "simulated-conversation")
    envelope = normalize_simulator_envelope(payload)
    extraction = fixture_extraction_from_payload(payload, trace_id=trace_id)
    return process_message_with_extraction(
        envelope=envelope,
        payload=payload,
        extraction=extraction,
        venue_context=venue_context,
        store=store,
        trace_id=trace_id,
        trace_label="Simulator WhatsApp message normalized",
        validation_label="Fixture model-shaped extraction validated",
    )


def process_simulated_model_message(
    *,
    payload: dict[str, Any],
    venue_context: dict[str, Any],
    store: InMemoryConversationStore,
    extraction_provider: Any,
) -> dict[str, Any]:
    trace_id = str(payload.get("trace_id") or payload.get("message_id") or "simulated-model-conversation")
    envelope = normalize_simulator_envelope(payload)
    extraction = extraction_provider(
        message=envelope["text"],
        venue_context=venue_context,
        trace_id=trace_id,
    )
    return process_message_with_extraction(
        envelope=envelope,
        payload=payload,
        extraction=extraction,
        venue_context=venue_context,
        store=store,
        trace_id=trace_id,
        trace_label="Simulator WhatsApp message normalized",
        validation_label="Model extraction validated",
    )


def process_baileys_message(
    *,
    payload: dict[str, Any],
    venue_context: dict[str, Any],
    store: InMemoryConversationStore,
    extraction_mode: str,
    extraction_provider: Any | None = None,
) -> dict[str, Any]:
    trace_id = str(payload.get("trace_id") or payload.get("message_id") or "baileys-conversation")
    envelope = normalize_baileys_envelope(payload)
    if extraction_mode == "modal":
        if extraction_provider is None:
            raise ValueError("modal_extraction_provider_missing")
        extraction = extraction_provider(
            message=envelope["text"],
            venue_context=venue_context,
            trace_id=trace_id,
        )
        validation_label = "Modal extraction validated"
    elif extraction_mode == "fixture_dry_run":
        extraction = fixture_extraction_from_payload(payload, trace_id=trace_id)
        validation_label = "Fixture model-shaped extraction validated"
    else:
        raise ValueError("unsupported_live_adapter_mode")

    return process_message_with_extraction(
        envelope=envelope,
        payload=payload,
        extraction=extraction,
        venue_context=venue_context,
        store=store,
        trace_id=trace_id,
        trace_label="Baileys WhatsApp message normalized",
        validation_label=validation_label,
    )


def process_message_with_extraction(
    *,
    envelope: dict[str, Any],
    payload: dict[str, Any],
    extraction: dict[str, Any],
    venue_context: dict[str, Any],
    store: InMemoryConversationStore,
    trace_id: str,
    trace_label: str,
    validation_label: str,
) -> dict[str, Any]:
    session_id = conversation_key(payload, envelope)
    session = store.get_or_create(session_id, envelope, trace_id)
    session["trace_id"] = trace_id
    session["player_phone"] = envelope.get("sender_phone") or session.get("player_phone")
    session["turn_count"] = int(session.get("turn_count") or 0) + 1
    session.setdefault("turns", []).append(
        {
            "turn_index": session["turn_count"],
            "adapter_envelope": envelope,
            "raw_message": envelope["text"],
            "received_at": envelope["received_at"],
        }
    )
    add_trace(session, "adapter_envelope", trace_label, adapter=envelope["adapter"], message_id=envelope["message_id"])

    session["model_extraction"] = extraction
    session["model_validation"] = extraction.get("validation") or {}
    add_trace(
        session,
        "model_validation",
        validation_label if extraction.get("ok") else "Model extraction blocked",
        "neutral" if extraction.get("ok") else "error",
        validation=session["model_validation"],
    )

    if not extraction.get("ok"):
        session["status"] = "failed_model"
        session["terminal_state"] = "failed_model"
        session["outbound_message"] = {"channel": "whatsapp_simulator", "delivery_state": "not_sent", "text": "", "reason": "failed_model"}
        session["send_adapter"] = {"adapter": "simulator", "delivery_state": "not_sent", "reason": "failed_model"}
        add_trace(session, "terminal_state", "Model/runtime/schema path blocked; no fallback extraction used", "error", fallback_used=False)
        session["updated_at"] = utc_now()
        return public_session(store.save(session))

    candidate = merge_candidate(session.get("candidate_extraction") or {}, extraction.get("booking") or {})
    session["candidate_extraction"] = candidate
    truth_initial = evaluate_booking_candidate(candidate, venue_context)
    session["truth_check_initial"] = truth_initial
    session["booking_record"] = build_booking_record(candidate, truth_initial)
    session["outbound_message"] = build_reply_draft(candidate, truth_initial)
    session["status"] = truth_initial["flow_state"]
    session["terminal_state"] = None
    session["owner_review_required"] = True
    add_trace(session, "truth_check_initial", "Deterministic truth check completed before owner review", flow_state=truth_initial["flow_state"])
    add_trace(session, "owner_review_pending", "Owner review required before outbound send", owner_review_required=True)
    session["updated_at"] = utc_now()
    return public_session(store.save(session))
