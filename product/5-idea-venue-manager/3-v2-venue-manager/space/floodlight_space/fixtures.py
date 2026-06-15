from __future__ import annotations

from copy import deepcopy
from typing import Any

from floodlight_space.state_snapshot import build_bootstrap_from_snapshot, load_state_snapshot


def build_bootstrap(scenario: str = "normal") -> dict[str, Any]:
    payload = _base_payload()
    return _apply_scenario(payload, scenario)


def _base_payload() -> dict[str, Any]:
    return build_bootstrap_from_snapshot(load_state_snapshot())


def _legacy_base_payload() -> dict[str, Any]:
    return {
        "runtime": {
            "app": "floodlight-venue-ops-agent",
            "version": "v1-design-prototype",
            "channel_label": "WhatsApp simulator",
            "channel_status": "simulator-connected",
            "channel_copy": "Demo channel connected. No live WhatsApp send proof claimed.",
            "pending_count": 7,
            "confirmed_today": 12,
            "occupancy_today": 68,
            "proof_boundary": "Static fixture prototype; live WhatsApp, external scoring/admin, video, model, and HF deployment proof are not claimed."
        },
        "slots": [
            {"id": "morning", "label": "8 AM - 12 PM", "period": "Morning"},
            {"id": "afternoon", "label": "2 PM - 6 PM", "period": "Afternoon"}
        ],
        "venues": [
            {
                "id": "north-field",
                "name": "North Field",
                "surface": "Grass",
                "grass_type": "Natural",
                "slots": {
                    "morning": {"status": "available", "rate": 6000, "request_count": 0},
                    "afternoon": {"status": "partial", "rate": 6500, "request_count": 2}
                }
            },
            {
                "id": "south-field",
                "name": "South Field",
                "surface": "Grass",
                "grass_type": "Astro turf",
                "slots": {
                    "morning": {"status": "available", "rate": 5500, "request_count": 0},
                    "afternoon": {"status": "partial", "rate": 6000, "request_count": 1}
                }
            }
        ],
        "bookings": [
            {
                "id": "north-afternoon-rohit",
                "venue_id": "north-field",
                "slot_id": "afternoon",
                "date_text": "tomorrow",
                "status": "pending_owner_review",
                "team_id": "friends-rohit",
                "players": 10
            },
            {
                "id": "south-afternoon-local-league",
                "venue_id": "south-field",
                "slot_id": "afternoon",
                "date_text": "tomorrow",
                "status": "pending_owner_review",
                "team_id": "league-karan",
                "players": 14
            }
        ],
        "registered_teams": [
            {
                "id": "corporate-aman",
                "name": "Aman Corporate XI",
                "sport": "cricket",
                "captain_player_id": "aman-sharma",
                "usual_players": 12,
                "notes": "Prefers North Field natural grass."
            },
            {
                "id": "friends-rohit",
                "name": "Rohit's Friends",
                "sport": "cricket",
                "captain_player_id": "rohit-verma",
                "usual_players": 10,
                "notes": "Flexible between North Field and South Field."
            },
            {
                "id": "league-karan",
                "name": "Karan League Squad",
                "sport": "cricket",
                "captain_player_id": "karan-mehta",
                "usual_players": 14,
                "notes": "League booking; owner approval required."
            }
        ],
        "players": [
            {
                "id": "aman-sharma",
                "name": "Aman Sharma",
                "phone": "+91 98765 43210",
                "team_id": "corporate-aman"
            },
            {
                "id": "rohit-verma",
                "name": "Rohit Verma",
                "phone": "+91 90123 45678",
                "team_id": "friends-rohit"
            },
            {
                "id": "karan-mehta",
                "name": "Karan Mehta",
                "phone": "+91 99887 76655",
                "team_id": "league-karan"
            }
        ],
        "requests": [
            {
                "id": "aman-sharma",
                "customer_name": "Aman Sharma",
                "phone": "+91 98765 43210",
                "received_label": "1 min ago",
                "activity": "Cricket",
                "date_label": "Tomorrow, 25 May 2025",
                "requested_slot_id": "north-field:morning",
                "players": 12,
                "group_type": "Corporate",
                "status": "new",
                "tone": "ready",
                "missing_fields": [],
                "summary": "12 players · Corporate",
                "reply_draft": "Hi Aman, North Field is available tomorrow from 8 AM - 12 PM. The slot is ₹6,000 for natural grass. Reply YES and we will hold it after owner approval."
            },
            {
                "id": "rohit-verma",
                "customer_name": "Rohit Verma",
                "phone": "+91 90123 45678",
                "received_label": "3 min ago",
                "activity": "Cricket",
                "date_label": "Tomorrow, 25 May 2025",
                "requested_slot_id": "north-field:afternoon",
                "players": 10,
                "group_type": "Friends",
                "status": "new",
                "tone": "partial",
                "missing_fields": [],
                "summary": "10 players · Friends",
                "reply_draft": "Hi Rohit, North Field has partial demand tomorrow from 2 PM - 6 PM at ₹6,500. We can confirm after owner approval, or offer South Field at ₹6,000."
            },
            {
                "id": "karan-mehta",
                "customer_name": "Karan Mehta",
                "phone": "+91 99887 76655",
                "received_label": "5 min ago",
                "activity": "Cricket",
                "date_label": "Tomorrow, 25 May 2025",
                "requested_slot_id": "south-field:morning",
                "players": 14,
                "group_type": "League",
                "status": "new",
                "tone": "ready",
                "missing_fields": [],
                "summary": "14 players · League",
                "reply_draft": "Hi Karan, South Field is available tomorrow from 8 AM - 12 PM. Astro turf surface, ₹5,500. I can hold it after owner approval."
            },
            {
                "id": "vikas-singh",
                "customer_name": "Vikas Singh",
                "phone": "+91 91234 87650",
                "received_label": "7 min ago",
                "activity": "Cricket",
                "date_label": "Today",
                "requested_slot_id": "south-field:afternoon",
                "players": 12,
                "group_type": "Corporate",
                "status": "conflict",
                "tone": "conflict",
                "missing_fields": [],
                "summary": "12 players · Corporate",
                "reply_draft": "Hi Vikas, the requested afternoon slot has other demand. North Field morning is open, or South Field morning is open. Which one should I hold for you?"
            },
            {
                "id": "neha-iyer",
                "customer_name": "Neha Iyer",
                "phone": "+91 95555 45670",
                "received_label": "9 min ago",
                "activity": "Cricket",
                "date_label": "Tomorrow, 25 May 2025",
                "requested_slot_id": "south-field:afternoon",
                "players": 8,
                "group_type": "Friends",
                "status": "clarification",
                "tone": "clarification",
                "missing_fields": ["format/overs"],
                "summary": "8 players · Friends",
                "reply_draft": "Hi Neha, South Field afternoon is available with one existing request. Could you confirm format or overs before I ask the owner to hold it?"
            }
        ],
        "decision": {
            "selected_request_id": "aman-sharma",
            "selected_slot_id": "north-field:morning",
            "selected_price": 6000,
            "notes": "",
            "state": "ready"
        },
        "integrations": [
            {
                "id": "video",
                "label": "Video Telecast",
                "state": "disabled",
                "copy": "Disabled"
            },
            {
                "id": "external-scoring",
                "label": "External scoring/admin app",
                "state": "not-connected",
                "copy": "Not connected · Disabled"
            }
        ],
        "trace": [
            {"id": "intake", "label": "Intake received from simulator", "tone": "neutral", "timestamp_label": "now"},
            {"id": "policy", "label": "Approval required before outbound reply", "tone": "warning", "timestamp_label": "now"},
            {"id": "draft", "label": "Reply drafted and pending owner review", "tone": "neutral", "timestamp_label": "now"}
        ],
        "scenarios": [
            {"id": "normal", "label": "Live queue"},
            {"id": "clarification", "label": "Clarification"},
            {"id": "conflict", "label": "Slot conflict"},
            {"id": "provider-error", "label": "Provider error"},
            {"id": "empty", "label": "Empty queue"}
        ],
        "active_scenario": "normal"
    }


def _apply_scenario(payload: dict[str, Any], scenario: str) -> dict[str, Any]:
    data = deepcopy(payload)
    data["active_scenario"] = scenario

    if scenario == "clarification":
        data["decision"]["selected_request_id"] = "neha-iyer"
        data["decision"]["selected_slot_id"] = "south-field:afternoon"
        data["decision"]["selected_price"] = 6000
        data["trace"].append({"id": "missing-fields", "label": "Missing field: format/overs", "tone": "warning", "timestamp_label": "now"})
    elif scenario == "conflict":
        data["decision"]["selected_request_id"] = "vikas-singh"
        data["decision"]["selected_slot_id"] = "south-field:afternoon"
        data["decision"]["selected_price"] = 6000
        data["venues"][1]["slots"]["afternoon"]["status"] = "conflict"
        data["trace"].append({"id": "conflict", "label": "Requested slot has competing demand; alternatives visible", "tone": "warning", "timestamp_label": "now"})
    elif scenario == "provider-error":
        data["runtime"]["channel_status"] = "provider-error"
        data["runtime"]["channel_copy"] = "Simulator provider error. No outbound reply can be marked sent."
        data["decision"]["state"] = "error"
        data["trace"].append({"id": "provider-error", "label": "Provider error state active; retry required", "tone": "error", "timestamp_label": "now"})
    elif scenario == "empty":
        data["runtime"]["pending_count"] = 0
        data["requests"] = []
        data["decision"]["selected_request_id"] = ""
        data["decision"]["selected_slot_id"] = "north-field:morning"
        data["decision"]["state"] = "idle"
        data["trace"] = [{"id": "empty", "label": "Queue empty; board remains reviewable", "tone": "neutral", "timestamp_label": "now"}]

    return data
