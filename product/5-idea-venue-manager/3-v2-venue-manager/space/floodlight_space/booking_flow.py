from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


REQUIRED_FIELDS = {
    "customer.name": "your name",
    "customer.phone": "a phone number",
    "sport": "the sport",
    "date_text": "the date",
    "time_window": "the time slot",
    "players": "the number of players",
}


def apply_booking_flow(
    *,
    extraction: dict[str, Any],
    venue_context: dict[str, Any],
    trace_id: str,
) -> dict[str, Any]:
    """Turn model extraction into owner/player booking state.

    The model extracts intent and fields. This function is deterministic business
    logic: it checks missing information, venue/slot fit, and what reply may be
    prepared for the player.
    """
    events = [
        _event("intake", "Player message received by backend"),
        _event("model_result", "Model extraction returned" if extraction.get("ok") else "Model extraction blocked"),
    ]
    if not extraction.get("ok"):
        events.append(_event("blocked", "No deterministic extraction fallback used", "error"))
        return {
            "ok": False,
            "trace_id": trace_id,
            "flow_state": "model_blocked",
            "booking_record": None,
            "player_message": {
                "channel": "whatsapp_simulator",
                "delivery_state": "not_sent",
                "text": "",
                "reason": "model extraction failed; owner should retry or inspect blocker",
            },
            "owner_next_action": "Inspect the model/runtime blocker before replying.",
            "agent_trace": events,
        }

    booking = extraction.get("booking") or {}
    missing = _missing_fields(booking)
    if missing:
        reply = _missing_info_reply(booking, missing)
        events.append(_event("missing_info", f"Missing fields: {', '.join(missing)}", "warning"))
        events.append(_event("reply_drafted", "Clarification reply drafted for owner review"))
        return {
            "ok": True,
            "trace_id": trace_id,
            "flow_state": "needs_player_info",
            "booking_record": _booking_record(booking, venue_context, status="needs_clarification"),
            "missing_fields": missing,
            "player_message": {
                "channel": "whatsapp_simulator",
                "delivery_state": "drafted_for_owner",
                "text": reply,
                "reason": "missing booking information",
            },
            "owner_next_action": "Review the clarification message, then send it to the player.",
            "agent_trace": events,
        }

    slot_match = _match_slot(booking, venue_context)
    if not slot_match:
        reply = _slot_clarification_reply(booking, venue_context)
        events.append(_event("slot_unmatched", "Requested venue or slot did not match current inventory", "warning"))
        events.append(_event("reply_drafted", "Alternative-slot reply drafted for owner review"))
        return {
            "ok": True,
            "trace_id": trace_id,
            "flow_state": "slot_clarification",
            "booking_record": _booking_record(booking, venue_context, status="slot_clarification"),
            "missing_fields": ["available_slot"],
            "player_message": {
                "channel": "whatsapp_simulator",
                "delivery_state": "drafted_for_owner",
                "text": reply,
                "reason": "requested slot not matched",
            },
            "owner_next_action": "Offer an available slot or edit the booking request.",
            "agent_trace": events,
        }

    status = slot_match["slot"].get("status")
    if status in {"booked", "conflict"}:
        reply = _slot_clarification_reply(booking, venue_context)
        events.append(_event("conflict", "Requested slot is not cleanly available", "warning"))
        events.append(_event("reply_drafted", "Conflict reply drafted for owner review"))
        return {
            "ok": True,
            "trace_id": trace_id,
            "flow_state": "conflict_possible",
            "booking_record": _booking_record(booking, venue_context, status="conflict_possible", slot_match=slot_match),
            "missing_fields": [],
            "player_message": {
                "channel": "whatsapp_simulator",
                "delivery_state": "drafted_for_owner",
                "text": reply,
                "reason": "requested slot has conflict",
            },
            "owner_next_action": "Choose an alternative or manually approve a waitlisted hold.",
            "agent_trace": events,
        }

    record = _booking_record(booking, venue_context, status="ready_for_owner_review", slot_match=slot_match)
    reply = str(booking.get("reply_draft") or "").strip() or _ready_reply(record)
    events.append(_event("availability_checked", "Requested slot is available"))
    events.append(_event("owner_review", "Booking moved to owner review before outbound send"))
    return {
        "ok": True,
        "trace_id": trace_id,
        "flow_state": "ready_for_owner_review",
        "booking_record": record,
        "missing_fields": [],
        "player_message": {
            "channel": "whatsapp_simulator",
            "delivery_state": "drafted_for_owner",
            "text": reply,
            "reason": "owner approval required before send",
        },
        "owner_next_action": "Approve, edit, reject, or ask for clarification.",
        "agent_trace": events,
    }


def approve_booking_flow(flow: dict[str, Any], *, decision: str = "approve") -> dict[str, Any]:
    trace_id = str(flow.get("trace_id") or "booking-flow-decision")
    events = list(flow.get("agent_trace") or [])
    message = dict(flow.get("player_message") or {})
    record = dict(flow.get("booking_record") or {})
    if decision == "reject":
        record["status"] = "rejected"
        message["delivery_state"] = "drafted_for_owner"
        message["reason"] = "owner rejected request"
        events.append(_event("owner_rejected", "Owner rejected the booking request", "warning"))
    elif decision == "clarify":
        record["status"] = "needs_clarification"
        message["delivery_state"] = "drafted_for_owner"
        message["reason"] = "owner requested clarification"
        events.append(_event("owner_clarify", "Owner requested a clarification draft", "warning"))
    elif flow.get("flow_state") != "ready_for_owner_review":
        record["status"] = flow.get("flow_state") or record.get("status") or "not_confirmable"
        message["delivery_state"] = "not_sent"
        message["reason"] = f"cannot_confirm_{flow.get('flow_state') or 'unknown'}"
        events.append(_event("approval_blocked", "Owner approval blocked by non-confirmable backend state", "warning"))
    else:
        record["status"] = "confirmed_simulated"
        message["delivery_state"] = "simulated_sent"
        message["sent_at"] = _now()
        events.append(_event("sent", "Message sent through WhatsApp simulator", "success"))
    return {
        **flow,
        "trace_id": trace_id,
        "booking_record": record,
        "player_message": message,
        "agent_trace": events,
    }


def _missing_fields(booking: dict[str, Any]) -> list[str]:
    missing = set(str(item) for item in booking.get("missing_fields") or [] if item)
    customer = booking.get("customer") if isinstance(booking.get("customer"), dict) else {}
    checks = {
        "customer.name": customer.get("name"),
        "customer.phone": customer.get("phone"),
        "sport": booking.get("sport"),
        "date_text": booking.get("date_text"),
        "time_window": booking.get("time_window"),
        "players": booking.get("players"),
    }
    for key, value in checks.items():
        if value is None or str(value).strip() == "":
            missing.add(key)
    return sorted(missing)


def _match_slot(booking: dict[str, Any], venue_context: dict[str, Any]) -> dict[str, Any] | None:
    wanted_venue = _norm(booking.get("venue_preference"))
    wanted_time = _norm(booking.get("time_window"))
    venues = venue_context.get("venues") or []
    slot_defs = venue_context.get("slots") or []
    slot_by_id = {str(slot.get("id")): slot for slot in slot_defs if isinstance(slot, dict)}
    for venue in venues:
        if not isinstance(venue, dict):
            continue
        venue_name = _norm(venue.get("name"))
        if wanted_venue and wanted_venue not in venue_name and venue_name not in wanted_venue:
            continue
        for slot_id, slot in (venue.get("slots") or {}).items():
            slot_label = _norm(slot_by_id.get(slot_id, {}).get("label"))
            slot_period = _norm(slot_by_id.get(slot_id, {}).get("period"))
            if wanted_time and not _time_matches(wanted_time, slot_label, slot_period):
                continue
            return {
                "venue": venue,
                "slot_id": slot_id,
                "slot_definition": slot_by_id.get(slot_id, {}),
                "slot": slot,
            }
    return None


def _booking_record(
    booking: dict[str, Any],
    venue_context: dict[str, Any],
    *,
    status: str,
    slot_match: dict[str, Any] | None = None,
) -> dict[str, Any]:
    customer = booking.get("customer") if isinstance(booking.get("customer"), dict) else {}
    budget = booking.get("budget") if isinstance(booking.get("budget"), dict) else {}
    team = _match_registered_team(customer, venue_context)
    return {
        "id": f"{_slug(customer.get('name') or 'player')}-{_slug(booking.get('date_text') or 'date')}",
        "status": status,
        "customer_name": customer.get("name"),
        "phone": customer.get("phone"),
        "registered_team_id": team.get("id") if team else None,
        "registered_team_name": team.get("name") if team else None,
        "sport": booking.get("sport"),
        "date_text": booking.get("date_text"),
        "time_window": booking.get("time_window"),
        "venue_id": (slot_match or {}).get("venue", {}).get("id"),
        "venue_name": (slot_match or {}).get("venue", {}).get("name") or booking.get("venue_preference"),
        "slot_id": (slot_match or {}).get("slot_id"),
        "players": booking.get("players"),
        "budget_amount": budget.get("amount"),
        "budget_currency": budget.get("currency"),
        "quoted_price": (slot_match or {}).get("slot", {}).get("rate"),
        "source": "model_extraction_plus_backend_rules",
    }


def _match_registered_team(customer: dict[str, Any], venue_context: dict[str, Any]) -> dict[str, Any] | None:
    phone = str(customer.get("phone") or "")
    teams = venue_context.get("registered_teams") or []
    players = venue_context.get("players") or []
    player_team_by_phone = {
        str(player.get("phone")): player.get("team_id")
        for player in players
        if isinstance(player, dict) and player.get("phone")
    }
    team_id = player_team_by_phone.get(phone)
    for team in teams:
        if isinstance(team, dict) and team.get("id") == team_id:
            return team
    return None


def _missing_info_reply(booking: dict[str, Any], missing: list[str]) -> str:
    customer = booking.get("customer") if isinstance(booking.get("customer"), dict) else {}
    name = str(customer.get("name") or "there").split(" ")[0]
    labels = [REQUIRED_FIELDS.get(field, field.replace("_", " ")) for field in missing[:3]]
    if len(labels) == 1:
        ask = labels[0]
    elif len(labels) == 2:
        ask = f"{labels[0]} and {labels[1]}"
    else:
        ask = f"{', '.join(labels[:-1])}, and {labels[-1]}"
    return f"Hi {name}, could you confirm {ask} so I can check the booking?"


def _slot_clarification_reply(booking: dict[str, Any], venue_context: dict[str, Any]) -> str:
    customer = booking.get("customer") if isinstance(booking.get("customer"), dict) else {}
    name = str(customer.get("name") or "there").split(" ")[0]
    options = _available_options(venue_context)
    suffix = f" Available options: {options}." if options else ""
    return f"Hi {name}, I need to check an alternate slot for this request.{suffix}"


def _ready_reply(record: dict[str, Any]) -> str:
    name = str(record.get("customer_name") or "there").split(" ")[0]
    price = record.get("quoted_price") or record.get("budget_amount")
    price_text = f" at Rs {price}" if price else ""
    return (
        f"Hi {name}, I have your {record.get('sport')} request for "
        f"{record.get('venue_name')} {record.get('time_window')}{price_text}. "
        "The owner will review and confirm shortly."
    )


def _available_options(venue_context: dict[str, Any]) -> str:
    labels: list[str] = []
    slots = {str(slot.get("id")): slot for slot in venue_context.get("slots") or [] if isinstance(slot, dict)}
    for venue in venue_context.get("venues") or []:
        if not isinstance(venue, dict):
            continue
        for slot_id, slot in (venue.get("slots") or {}).items():
            if slot.get("status") == "available":
                labels.append(f"{venue.get('name')} {slots.get(slot_id, {}).get('label')}")
    return "; ".join(labels[:3])


def _time_matches(wanted_time: str, slot_label: str, slot_period: str) -> bool:
    if wanted_time in slot_label or slot_label in wanted_time or slot_period in wanted_time:
        return True
    wanted_digits = "".join(char for char in wanted_time if char.isdigit())
    slot_digits = "".join(char for char in slot_label if char.isdigit())
    return bool(wanted_digits and wanted_digits == slot_digits)


def _event(event_id: str, label: str, tone: str = "neutral") -> dict[str, str]:
    return {
        "id": event_id,
        "label": label,
        "tone": tone,
        "timestamp": _now(),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _norm(value: Any) -> str:
    return str(value or "").lower().replace("–", "-").strip()


def _slug(value: Any) -> str:
    text = _norm(value)
    cleaned = "".join(char if char.isalnum() else "-" for char in text)
    return "-".join(part for part in cleaned.split("-") if part)[:48] or "unknown"
