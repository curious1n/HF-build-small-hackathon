from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


DATA_ROOT = Path(__file__).resolve().parent / "data"
DEFAULT_SNAPSHOT_PATH = DATA_ROOT / "state_snapshot.v1.json"


def load_state_snapshot(path: Path | None = None) -> dict[str, Any]:
    snapshot_path = path or DEFAULT_SNAPSHOT_PATH
    snapshot = json.loads(snapshot_path.read_text())
    validate_state_snapshot(snapshot)
    return snapshot


def build_bootstrap_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    validate_state_snapshot(snapshot)
    payload = {
        "runtime": deepcopy(snapshot["runtime"]),
        "slots": deepcopy(snapshot["slots"]),
        "venues": deepcopy(snapshot["venues"]),
        "bookings": deepcopy(snapshot.get("bookings", [])),
        "registered_teams": deepcopy(snapshot.get("registered_teams", [])),
        "players": deepcopy(snapshot.get("players", [])),
        "requests": deepcopy(snapshot.get("requests", [])),
        "decision": deepcopy(snapshot["decision"]),
        "integrations": deepcopy(snapshot.get("integrations", [])),
        "trace": deepcopy(snapshot.get("trace", [])),
        "scenarios": deepcopy(snapshot.get("scenarios", [])),
        "active_scenario": snapshot.get("active_scenario", "normal"),
        "state_snapshot": {
            "schema_version": snapshot["schema_version"],
            "snapshot_id": snapshot["snapshot_id"],
            "description": snapshot.get("description", ""),
            "time_anchor": deepcopy(snapshot.get("time_anchor", {})),
            "conversation_threads": deepcopy(snapshot.get("conversation_threads", [])),
            "proof_boundary": snapshot.get("proof_boundary", ""),
        },
    }
    payload["runtime"]["pending_count"] = sum(
        1 for request in payload["requests"] if request.get("status") != "sent"
    )
    return payload


def validate_state_snapshot(snapshot: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "snapshot_id",
        "runtime",
        "slots",
        "venues",
        "decision",
    }
    missing = sorted(key for key in required if key not in snapshot)
    if missing:
        raise ValueError(f"state_snapshot_missing_required_fields:{','.join(missing)}")
    if snapshot["schema_version"] != "state_snapshot.v1":
        raise ValueError("state_snapshot_unsupported_schema_version")
    if not isinstance(snapshot.get("slots"), list) or not snapshot["slots"]:
        raise ValueError("state_snapshot_slots_required")
    if not isinstance(snapshot.get("venues"), list) or not snapshot["venues"]:
        raise ValueError("state_snapshot_venues_required")
    if not isinstance(snapshot.get("requests", []), list):
        raise ValueError("state_snapshot_requests_must_be_list")
