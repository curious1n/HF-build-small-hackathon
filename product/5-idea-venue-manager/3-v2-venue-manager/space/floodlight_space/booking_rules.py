from __future__ import annotations

from copy import deepcopy
from typing import Any

from floodlight_space.whatsapp_adapter import normalize_phone


REQUIRED_FIELDS = {
    "customer.name": "your name",
    "customer.phone": "a phone number",
    "sport": "the sport",
    "date_text": "the date",
    "time_window": "the time slot",
    "players": "the number of players",
}

BLOCKING_BOOKING_STATUSES = {
    "confirmed",
    "confirmed_simulated",
    "pending_owner_review",
    "held",
}


def evaluate_booking_candidate(candidate: dict[str, Any], venue_context: dict[str, Any]) -> dict[str, Any]:
    booking = deepcopy(candidate)
    missing_fields = required_missing_fields(booking)
    player = resolve_player(booking, venue_context)
    team = resolve_team(player, venue_context)

    base = {
        "status": "incomplete",
        "flow_state": "needs_player_info",
        "matched_venue_id": None,
        "matched_slot_id": None,
        "matched_player_id": player.get("id") if player else None,
        "matched_team_id": team.get("id") if team else None,
        "matched_team_name": team.get("name") if team else None,
        "conflicts": [],
        "missing_fields": missing_fields,
        "eligible_for_hold": False,
        "provisional_hold": {"eligible": False, "hold_key": None},
        "owner_review_required": True,
        "alternatives": available_alternatives(venue_context),
    }
    if missing_fields:
        return base

    slot_match = match_slot(booking, venue_context)
    if slot_match is None:
        return {
            **base,
            "status": "slot_unmatched",
            "flow_state": "slot_clarification",
            "missing_fields": ["available_slot"],
        }

    conflicts = slot_conflicts(booking, slot_match, venue_context)
    matched = {
        **base,
        "matched_venue_id": slot_match["venue"].get("id"),
        "matched_venue_name": slot_match["venue"].get("name"),
        "matched_slot_id": slot_match["slot_id"],
        "matched_slot_label": slot_match["slot_definition"].get("label"),
        "quoted_price": slot_match["slot"].get("rate"),
        "missing_fields": [],
        "conflicts": conflicts,
    }
    if conflicts:
        return {
            **matched,
            "status": "conflict",
            "flow_state": "conflict_possible",
            "eligible_for_hold": False,
        }

    return {
        **matched,
        "status": "available",
        "flow_state": "ready_for_owner_review",
        "eligible_for_hold": True,
        "hold_key": f"{slot_match['venue'].get('id')}:{slot_match['slot_id']}:{_norm(booking.get('date_text'))}",
        "provisional_hold": {
            "eligible": True,
            "hold_key": f"{slot_match['venue'].get('id')}:{slot_match['slot_id']}:{_norm(booking.get('date_text'))}",
            "policy": "owner_approval_required_before_send",
        },
    }


def build_booking_record(candidate: dict[str, Any], truth_check: dict[str, Any]) -> dict[str, Any]:
    customer = candidate.get("customer") if isinstance(candidate.get("customer"), dict) else {}
    budget = candidate.get("budget") if isinstance(candidate.get("budget"), dict) else {}
    return {
        "customer_name": customer.get("name"),
        "phone": customer.get("phone"),
        "registered_player_id": truth_check.get("matched_player_id"),
        "registered_team_id": truth_check.get("matched_team_id"),
        "registered_team_name": truth_check.get("matched_team_name"),
        "sport": candidate.get("sport"),
        "date_text": candidate.get("date_text"),
        "time_window": candidate.get("time_window"),
        "venue_id": truth_check.get("matched_venue_id"),
        "venue_name": truth_check.get("matched_venue_name") or candidate.get("venue_preference"),
        "slot_id": truth_check.get("matched_slot_id"),
        "players": candidate.get("players"),
        "budget_amount": budget.get("amount"),
        "budget_currency": budget.get("currency"),
        "quoted_price": truth_check.get("quoted_price"),
        "status": truth_check.get("flow_state"),
        "source": "model_shaped_fixture_plus_backend_rules",
    }


def build_reply_draft(candidate: dict[str, Any], truth_check: dict[str, Any]) -> dict[str, Any]:
    flow_state = truth_check.get("flow_state")
    if flow_state == "ready_for_owner_review":
        text = str(candidate.get("reply_draft") or "").strip() or _ready_reply(candidate, truth_check)
        kind = "confirmation"
    elif flow_state == "needs_player_info":
        text = _missing_info_reply(candidate, truth_check.get("missing_fields") or [])
        kind = "clarification"
    elif flow_state in {"slot_clarification", "conflict_possible"}:
        text = _alternative_reply(candidate, truth_check)
        kind = "alternative"
    else:
        text = ""
        kind = "blocked"
    return {
        "channel": "whatsapp_simulator",
        "delivery_state": "drafted_for_owner" if text else "not_sent",
        "text": text,
        "kind": kind,
        "reason": flow_state,
    }


def required_missing_fields(candidate: dict[str, Any]) -> list[str]:
    customer = candidate.get("customer") if isinstance(candidate.get("customer"), dict) else {}
    checks = {
        "customer.name": customer.get("name"),
        "customer.phone": customer.get("phone"),
        "sport": candidate.get("sport"),
        "date_text": candidate.get("date_text"),
        "time_window": candidate.get("time_window"),
        "players": candidate.get("players"),
    }
    missing = {
        str(item)
        for item in candidate.get("missing_fields") or []
        if item in REQUIRED_FIELDS or str(item).startswith("customer.")
    }
    for field, value in checks.items():
        if value is None or str(value).strip() == "":
            missing.add(field)
    return sorted(missing)


def match_slot(candidate: dict[str, Any], venue_context: dict[str, Any]) -> dict[str, Any] | None:
    wanted_venue = _norm(candidate.get("venue_preference"))
    wanted_time = _norm(candidate.get("time_window"))
    slots = {
        str(slot.get("id")): slot
        for slot in venue_context.get("slots") or []
        if isinstance(slot, dict)
    }
    for venue in venue_context.get("venues") or []:
        if not isinstance(venue, dict):
            continue
        venue_name = _norm(venue.get("name"))
        if wanted_venue and wanted_venue not in venue_name and venue_name not in wanted_venue:
            continue
        for slot_id, slot in (venue.get("slots") or {}).items():
            slot_definition = slots.get(str(slot_id), {})
            slot_label = _norm(slot_definition.get("label"))
            slot_period = _norm(slot_definition.get("period"))
            if wanted_time and not time_matches(wanted_time, slot_label, slot_period):
                continue
            return {
                "venue": venue,
                "slot_id": str(slot_id),
                "slot_definition": slot_definition,
                "slot": slot,
            }
    return None


def slot_conflicts(candidate: dict[str, Any], slot_match: dict[str, Any], venue_context: dict[str, Any]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    slot_status = str(slot_match["slot"].get("status") or "available")
    if slot_status != "available":
        conflicts.append({"type": "slot_status", "status": slot_status})

    venue_id = str(slot_match["venue"].get("id"))
    slot_id = str(slot_match["slot_id"])
    date_text = _norm(candidate.get("date_text"))
    for booking in venue_context.get("bookings") or []:
        if not isinstance(booking, dict):
            continue
        if str(booking.get("venue_id")) != venue_id or str(booking.get("slot_id")) != slot_id:
            continue
        if _norm(booking.get("date_text")) != date_text:
            continue
        if str(booking.get("status")) in BLOCKING_BOOKING_STATUSES:
            conflicts.append(
                {
                    "type": "existing_booking",
                    "booking_id": booking.get("id"),
                    "status": booking.get("status"),
                    "team_id": booking.get("team_id"),
                }
            )
    return conflicts


def available_alternatives(venue_context: dict[str, Any]) -> list[dict[str, Any]]:
    alternatives: list[dict[str, Any]] = []
    slot_defs = {
        str(slot.get("id")): slot
        for slot in venue_context.get("slots") or []
        if isinstance(slot, dict)
    }
    for venue in venue_context.get("venues") or []:
        if not isinstance(venue, dict):
            continue
        for slot_id, slot in (venue.get("slots") or {}).items():
            if slot.get("status") != "available":
                continue
            slot_definition = slot_defs.get(str(slot_id), {})
            alternatives.append(
                {
                    "venue_id": venue.get("id"),
                    "venue_name": venue.get("name"),
                    "slot_id": str(slot_id),
                    "slot_label": slot_definition.get("label"),
                    "rate": slot.get("rate"),
                }
            )
    return alternatives


def resolve_player(candidate: dict[str, Any], venue_context: dict[str, Any]) -> dict[str, Any] | None:
    customer = candidate.get("customer") if isinstance(candidate.get("customer"), dict) else {}
    phone = normalize_phone(customer.get("phone"))
    if not phone:
        return None
    for player in venue_context.get("players") or []:
        if isinstance(player, dict) and normalize_phone(player.get("phone")) == phone:
            return player
    return None


def resolve_team(player: dict[str, Any] | None, venue_context: dict[str, Any]) -> dict[str, Any] | None:
    if not player:
        return None
    team_id = player.get("team_id")
    for team in venue_context.get("registered_teams") or []:
        if isinstance(team, dict) and team.get("id") == team_id:
            return team
    return None


def time_matches(wanted_time: str, slot_label: str, slot_period: str) -> bool:
    if wanted_time in slot_label or slot_label in wanted_time or slot_period in wanted_time:
        return True
    wanted_digits = "".join(char for char in wanted_time if char.isdigit())
    slot_digits = "".join(char for char in slot_label if char.isdigit())
    return bool(wanted_digits and wanted_digits == slot_digits)


def _missing_info_reply(candidate: dict[str, Any], missing: list[str]) -> str:
    name = _first_name(candidate)
    labels = [REQUIRED_FIELDS.get(field, field.replace("_", " ")) for field in missing[:3]]
    if not labels:
        labels = ["the missing details"]
    if len(labels) == 1:
        ask = labels[0]
    elif len(labels) == 2:
        ask = f"{labels[0]} and {labels[1]}"
    else:
        ask = f"{', '.join(labels[:-1])}, and {labels[-1]}"
    return f"Hi {name}, could you confirm {ask} so I can check the booking?"


def _alternative_reply(candidate: dict[str, Any], truth_check: dict[str, Any]) -> str:
    name = _first_name(candidate)
    options = truth_check.get("alternatives") or []
    option_text = "; ".join(
        f"{option.get('venue_name')} {option.get('slot_label')} at Rs {option.get('rate')}"
        for option in options[:3]
    )
    suffix = f" Available options: {option_text}." if option_text else ""
    return f"Hi {name}, the requested slot is not cleanly available.{suffix}"


def _ready_reply(candidate: dict[str, Any], truth_check: dict[str, Any]) -> str:
    name = _first_name(candidate)
    venue = truth_check.get("matched_venue_name") or candidate.get("venue_preference") or "the venue"
    slot = truth_check.get("matched_slot_label") or candidate.get("time_window")
    price = truth_check.get("quoted_price")
    price_text = f" at Rs {price}" if price else ""
    return f"Hi {name}, {venue} is available for {slot}{price_text}. Reply YES and we will hold it after owner approval."


def _first_name(candidate: dict[str, Any]) -> str:
    customer = candidate.get("customer") if isinstance(candidate.get("customer"), dict) else {}
    return str(customer.get("name") or "there").strip().split(" ")[0]


def _norm(value: Any) -> str:
    return str(value or "").lower().replace("–", "-").strip()
