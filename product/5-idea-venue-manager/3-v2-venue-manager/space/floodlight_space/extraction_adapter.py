from __future__ import annotations

from copy import deepcopy
from typing import Any


BOOKING_KEYS = {
    "intent",
    "customer",
    "sport",
    "date_text",
    "time_window",
    "venue_preference",
    "surface_preference",
    "players",
    "budget",
    "missing_fields",
    "confidence",
    "reply_draft",
}


def fixture_extraction_from_payload(payload: dict[str, Any], *, trace_id: str) -> dict[str, Any]:
    """Normalize fixture/model-shaped extraction without calling a model."""
    raw = (
        payload.get("model_result")
        or payload.get("extraction")
        or payload.get("candidate_extraction")
        or payload.get("booking")
    )
    if raw is None:
        return _blocked(trace_id, "fixture_extraction_missing")

    if not isinstance(raw, dict):
        return _blocked(trace_id, "fixture_extraction_not_object")

    if raw.get("ok") is False:
        result = deepcopy(raw)
        result.setdefault("trace_id", trace_id)
        result.setdefault("fallback_used", False)
        result.setdefault("backend", "fixture_extractor")
        result.setdefault("booking", None)
        result.setdefault("validation", {"valid": False, "errors": ["model_blocked"]})
        return result

    booking = raw.get("booking") if isinstance(raw.get("booking"), dict) else raw
    validation = validate_candidate_booking(booking)
    return {
        "ok": validation["valid"],
        "trace_id": trace_id,
        "model_id": raw.get("model_id", "fixture-model-shaped-json"),
        "backend": raw.get("backend", "fixture_extractor"),
        "fallback_used": bool(raw.get("fallback_used", False)),
        "booking": deepcopy(booking) if validation["valid"] else None,
        "validation": validation,
        "blocker": None if validation["valid"] else "Fixture extraction failed schema validation.",
    }


def validate_candidate_booking(candidate: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(candidate, dict):
        return {"valid": False, "errors": ["booking_not_object"]}

    unknown_shape = not any(key in candidate for key in BOOKING_KEYS)
    if unknown_shape:
        errors.append("booking_missing_known_fields")

    customer = candidate.get("customer")
    if customer is not None and not isinstance(customer, dict):
        errors.append("customer_not_object")

    budget = candidate.get("budget")
    if budget is not None and not isinstance(budget, dict):
        errors.append("budget_not_object")

    players = candidate.get("players")
    if players is not None:
        try:
            int(players)
        except (TypeError, ValueError):
            errors.append("players_not_integer")

    missing_fields = candidate.get("missing_fields")
    if missing_fields is not None and not isinstance(missing_fields, list):
        errors.append("missing_fields_not_list")

    return {"valid": not errors, "errors": errors}


def _blocked(trace_id: str, reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "trace_id": trace_id,
        "model_id": "fixture-model-shaped-json",
        "backend": "fixture_extractor",
        "fallback_used": False,
        "booking": None,
        "blocker": reason,
        "validation": {"valid": False, "errors": [reason]},
    }
