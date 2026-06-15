from __future__ import annotations

from copy import deepcopy
from typing import Any

from floodlight_space.agent_trace import add_trace, utc_now
from floodlight_space.booking_rules import (
    build_booking_record,
    build_reply_draft,
    evaluate_booking_candidate,
)
from floodlight_space.send_adapter import simulator_send


def apply_owner_review(
    *,
    session: dict[str, Any],
    payload: dict[str, Any],
    venue_context: dict[str, Any],
) -> dict[str, Any]:
    action = str(payload.get("action") or "approve")
    approval_source = str(payload.get("approval_source") or "owner")
    edits = payload.get("edits") if isinstance(payload.get("edits"), dict) else {}

    add_trace(
        session,
        "owner_review_action",
        f"Owner review action received: {action}",
        approval_source=approval_source,
    )
    session["owner_review_action"] = {
        "action": action,
        "approval_source": approval_source,
        "received_at": utc_now(),
    }
    session["approval_source"] = approval_source

    if action == "reject":
        session["status"] = "cancelled"
        session["terminal_state"] = "cancelled"
        session["send_adapter"] = {"adapter": "simulator", "delivery_state": "not_sent", "reason": "owner_rejected"}
        add_trace(session, "terminal_state", "Owner rejected the booking request", "warning", terminal_state="cancelled")
        session["updated_at"] = utc_now()
        return session

    if action == "clarify":
        message = dict(session.get("outbound_message") or {})
        message = _apply_reply_edit(session, message, payload)
        delivery = simulator_send(session_id=session["session_id"], envelope=_latest_envelope(session), message=message)
        session["send_adapter"] = delivery
        session["outbound_message"] = {**message, "delivery_state": delivery["delivery_state"], "sent_at": delivery.get("sent_at")}
        session["status"] = "waiting_for_player"
        session["terminal_state"] = None
        add_trace(session, "send_adapter", "Clarification sent through simulator", "success", delivery_state=delivery["delivery_state"])
        session["updated_at"] = utc_now()
        return session

    approved = deepcopy(session.get("candidate_extraction") or session.get("approved_extraction") or {})
    if edits:
        before = deepcopy(approved)
        approved = merge_candidate(approved, edits)
        diff = correction_diff(before, approved)
        if diff:
            session.setdefault("owner_correction_diff", []).append(
                {
                    "action": "edit_extraction",
                    "edited_by": payload.get("edited_by", "owner"),
                    "before": before,
                    "after": approved,
                    "reason": payload.get("reason", ""),
                    "diff": diff,
                    "recorded_at": utc_now(),
                }
            )
            add_trace(session, "owner_correction_diff", "Owner edited extracted values", "warning", changed_fields=[item["field"] for item in diff])

    session["approved_extraction"] = approved
    truth_final = evaluate_booking_candidate(approved, venue_context)
    session["truth_check_final"] = truth_final
    session["booking_record"] = build_booking_record(approved, truth_final)
    session["outbound_message"] = build_reply_draft(approved, truth_final)
    session["outbound_message"] = _apply_reply_edit(session, session["outbound_message"], payload)
    session["status"] = truth_final["flow_state"]
    session["owner_review_required"] = True
    add_trace(session, "truth_check_final", "Deterministic truth check re-run after owner review", flow_state=truth_final["flow_state"])

    if action in {"accept", "edit_extraction"}:
        session["updated_at"] = utc_now()
        return session

    if action == "approve":
        if truth_final["flow_state"] != "ready_for_owner_review":
            session["send_adapter"] = {
                "adapter": "simulator",
                "delivery_state": "not_sent",
                "reason": f"cannot_confirm_{truth_final['flow_state']}",
            }
            add_trace(
                session,
                "send_policy_blocked",
                "Approval did not send because final truth check is not confirmable",
                "warning",
                flow_state=truth_final["flow_state"],
            )
            session["updated_at"] = utc_now()
            return session

        delivery = simulator_send(
            session_id=session["session_id"],
            envelope=_latest_envelope(session),
            message=session["outbound_message"],
        )
        session["send_adapter"] = delivery
        session["outbound_message"] = {
            **session["outbound_message"],
            "delivery_state": delivery["delivery_state"],
            "sent_at": delivery.get("sent_at"),
        }
        session["status"] = "confirmed_simulated"
        session["terminal_state"] = "confirmed_simulated"
        session["booking_record"]["status"] = "confirmed_simulated"
        add_trace(session, "send_adapter", "Approved reply sent through simulator", "success", delivery_state=delivery["delivery_state"])
        add_trace(session, "terminal_state", "Conversation completed through simulator", "success", terminal_state="confirmed_simulated")

    session["updated_at"] = utc_now()
    return session


def merge_candidate(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in updates.items():
        if value is None or value == "":
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_candidate(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def correction_diff(before: dict[str, Any], after: dict[str, Any], prefix: str = "") -> list[dict[str, Any]]:
    fields = set(before) | set(after)
    diff: list[dict[str, Any]] = []
    for key in sorted(fields):
        field = f"{prefix}.{key}" if prefix else str(key)
        before_value = before.get(key)
        after_value = after.get(key)
        if isinstance(before_value, dict) and isinstance(after_value, dict):
            diff.extend(correction_diff(before_value, after_value, field))
        elif before_value != after_value:
            diff.append({"field": field, "before": before_value, "after": after_value})
    return diff


def _apply_reply_edit(session: dict[str, Any], message: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    edited_text = payload.get("reply_draft")
    outbound = payload.get("outbound_message") if isinstance(payload.get("outbound_message"), dict) else {}
    if edited_text is None:
        edited_text = outbound.get("text")
    if edited_text is None:
        return message
    text = str(edited_text).strip()
    if not text:
        return message
    before = message.get("text")
    if before == text:
        return message
    add_trace(session, "owner_reply_edit", "Owner edited outbound reply draft", changed=True)
    return {**message, "text": text, "edited_by_owner": True}


def _latest_envelope(session: dict[str, Any]) -> dict[str, Any]:
    turns = session.get("turns") or []
    if not turns:
        return {"adapter": "simulator", "sender_phone": session.get("player_phone")}
    return dict(turns[-1].get("adapter_envelope") or {})
