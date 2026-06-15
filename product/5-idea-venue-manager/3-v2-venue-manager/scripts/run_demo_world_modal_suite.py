#!/usr/bin/env python3
"""Run the v2 demo-world seed requests through the Modal-backed extractor."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
IDEA_ROOT = ROOT.parent
REPO_ROOT = ROOT.parents[2]
SPACE_ROOT = ROOT / "space"
sys.path.insert(0, str(SPACE_ROOT))

import app as app_module  # noqa: E402
from floodlight_space.conversation_service import process_message_with_extraction  # noqa: E402
from floodlight_space.conversation_store import InMemoryConversationStore  # noqa: E402
from floodlight_space.fixtures import build_bootstrap  # noqa: E402
from floodlight_space.modal_client import modal_status  # noqa: E402
from floodlight_space.whatsapp_adapter import normalize_simulator_envelope  # noqa: E402


RUN_LABEL = "venue-manager-v2-demo-world-modal-suite"
APPROVAL = (
    "User-approved Venue Manager v2 Modal/Nemotron demo-world scenario suite: "
    "max $20, max 15 minutes, stop after requested seeded scenarios complete "
    "or an exact blocker is recorded."
)

MESSAGE_OVERRIDES = {
    "aman-sharma": (
        "Hi, this is Aman Sharma. Need a cricket ground tomorrow morning "
        "8 AM to 12 PM for 12 players. Natural grass preferred, North Field if "
        "available. Budget is around Rs 6000. My number is +91 98765 43210."
    ),
    "rohit-verma": (
        "Rohit Verma here. Need North Field tomorrow afternoon, 2 PM to 6 PM, "
        "for cricket with 10 friends. Budget around Rs 6500. My number is "
        "+91 90123 45678."
    ),
    "karan-mehta": (
        "Hi, Karan Mehta from the league squad. Need South Field tomorrow "
        "morning 8 AM to 12 PM for cricket, 14 players, astro turf is fine. "
        "Budget Rs 5500. Phone +91 99887 76655."
    ),
    "vikas-singh": (
        "Vikas Singh here. Need South Field today afternoon, 2 PM to 6 PM, "
        "for corporate cricket with 12 players. Budget Rs 6000. My phone is "
        "+91 91234 87650."
    ),
    "neha-iyer": (
        "Hi, Neha Iyer. Need South Field tomorrow for cricket with "
        "8 players. We have not decided the format, overs, or exact time yet. My phone is "
        "+91 95555 45670."
    ),
    "arjun-nair": (
        "Arjun Nair here. Need South Field tomorrow morning, 8 AM to 12 PM, "
        "for football practice with 16 players. Budget Rs 5500. Phone "
        "+91 97400 66778."
    ),
    "siddharth-rao": (
        "Siddharth Rao here. Need North Field tomorrow afternoon, 2 PM to "
        "6 PM, for cricket with 11 friends. Budget around Rs 6500. My number "
        "is +91 96500 88990."
    ),
    "meera-rao": (
        "Hi, this is Meera Rao. Need North Field tomorrow for cricket with "
        "8 friends, but I still need to confirm the exact time window. My "
        "number is +91 77777 88888."
    ),
    "priya-menon": (
        "Priya Menon here. Confirming North Field today morning, 8 AM to "
        "12 PM, for cricket with 9 corporate players. Phone +91 93333 20009."
    ),
    "dev-arora": (
        "Dev Arora here. Need South Field tomorrow morning, 8 AM to 12 PM, "
        "for hockey practice with 10 players. Budget Rs 5500. Phone "
        "+91 94444 10004."
    ),
}

EXPECTED_BACKEND_ACTION = {
    "aman-sharma": "ready_for_owner_review",
    "rohit-verma": "conflict_possible",
    "karan-mehta": "ready_for_owner_review",
    "vikas-singh": "conflict_possible",
    "neha-iyer": "needs_player_info",
    "arjun-nair": "ready_for_owner_review",
    "siddharth-rao": "conflict_possible",
    "meera-rao": "needs_player_info",
    "priya-menon": "ready_for_owner_review",
    "dev-arora": "ready_for_owner_review",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-seconds", type=float, default=900.0)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--transport", choices=["batch", "per-case"], default="batch")
    parser.add_argument(
        "--case-id",
        action="append",
        help="Run only this seed request id. Can be repeated. Defaults to all demo-world requests.",
    )
    args = parser.parse_args()

    load_env(REPO_ROOT / ".env")
    load_env(IDEA_ROOT / ".env.modal.local")

    bootstrap = build_bootstrap("normal")
    cases = build_cases(bootstrap, selected=set(args.case_id or []))
    if not cases:
        raise SystemExit("No demo-world cases selected.")

    previous_timeout = os.environ.get("APP_MODAL_TIMEOUT_SECONDS")
    os.environ["APP_MODAL_TIMEOUT_SECONDS"] = str(args.max_seconds)
    started = time.monotonic()
    rows: list[dict[str, Any]] = []
    stopped_reason = ""

    try:
        with deadline(args.max_seconds):
            if args.transport == "batch":
                rows, stopped_reason = run_batch(cases, max_seconds=args.max_seconds)
            else:
                client = TestClient(app_module.app)
                for index, case in enumerate(cases, start=1):
                    remaining = args.max_seconds - (time.monotonic() - started)
                    if remaining <= 0:
                        stopped_reason = "deadline_before_next_case"
                        break
                    row = run_case(client, case, index=index, max_seconds=max(1.0, remaining))
                    rows.append(row)
                    if row["blocker_is_global"]:
                        stopped_reason = "global_blocker"
                        break
    except TimeoutError as exc:
        stopped_reason = "suite_deadline_exceeded"
        rows.append(timeout_row(str(exc), len(rows) + 1))
    finally:
        if previous_timeout is None:
            os.environ.pop("APP_MODAL_TIMEOUT_SECONDS", None)
        else:
            os.environ["APP_MODAL_TIMEOUT_SECONDS"] = previous_timeout

    if not stopped_reason:
        stopped_reason = "completed_requested_cases"

    summary = build_summary(
        args=args,
        cases=cases,
        rows=rows,
        stopped_reason=stopped_reason,
        wall_clock_seconds=round(time.monotonic() - started, 3),
    )
    if args.write:
        paths = write_artifacts(summary, rows)
        summary["artifacts"] = paths

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["failed"] == 0 and summary["attempted"] == summary["requested"] else 1


def build_cases(bootstrap: dict[str, Any], *, selected: set[str]) -> list[dict[str, Any]]:
    requests = bootstrap.get("requests") if isinstance(bootstrap.get("requests"), list) else []
    cases = []
    for request in requests:
        if not isinstance(request, dict):
            continue
        case_id = str(request.get("id") or "")
        if selected and case_id not in selected:
            continue
        message = MESSAGE_OVERRIDES.get(case_id)
        if not message:
            continue
        cases.append(
            {
                "case_id": case_id,
                "customer_name": request.get("customer_name"),
                "phone": request.get("phone"),
                "activity": request.get("activity"),
                "players": request.get("players"),
                "seed_status": request.get("status"),
                "seed_tone": request.get("tone"),
                "expected_backend_action": EXPECTED_BACKEND_ACTION.get(case_id),
                "message": message,
            }
        )
    return cases


def run_case(client: TestClient, case: dict[str, Any], *, index: int, max_seconds: float) -> dict[str, Any]:
    session_id = f"{RUN_LABEL}-{index:02d}-{case['case_id']}"
    started = time.monotonic()
    try:
        response = client.post(
            "/api/whatsapp/simulated-model-message",
            json={
                "session_id": session_id,
                "message_id": f"{session_id}-1",
                "sender_phone": case["phone"],
                "text": case["message"],
                "trace_id": session_id,
                "scenario": "normal",
            },
            timeout=max_seconds,
        )
        body = response.json()
        status_code = response.status_code
        trace_body = None
        if status_code == 200:
            trace_body = client.get(f"/api/conversations/{session_id}/trace").json()
    except Exception as exc:
        body = {"ok": False, "conversation": None, "blocker": f"{type(exc).__name__}: {str(exc)[:500]}"}
        status_code = 0
        trace_body = None

    row = build_row(
        case=case,
        session_id=session_id,
        status_code=status_code,
        body=body,
        trace_body=trace_body,
        wall_clock_seconds=round(time.monotonic() - started, 3),
    )
    return row


def run_batch(cases: list[dict[str, Any]], *, max_seconds: float) -> tuple[list[dict[str, Any]], str]:
    started = time.monotonic()
    bootstrap = build_bootstrap("normal")
    venue_context = model_context(bootstrap)
    items = []
    for index, case in enumerate(cases, start=1):
        session_id = f"{RUN_LABEL}-{index:02d}-{case['case_id']}"
        items.append(
            {
                "case_id": case["case_id"],
                "trace_id": session_id,
                "message": case["message"],
                "venue_context": venue_context,
            }
        )

    batch = post_modal_batch({"items": items}, timeout=max_seconds)
    if not batch.get("ok") and not isinstance(batch.get("results"), list):
        return [batch_blocker_row(batch, cases[0] if cases else {}, round(time.monotonic() - started, 3))], "global_blocker"

    results_by_case = {
        str(result.get("case_id")): result
        for result in batch.get("results", [])
        if isinstance(result, dict)
    }
    rows: list[dict[str, Any]] = []
    store = InMemoryConversationStore()
    for index, case in enumerate(cases, start=1):
        session_id = f"{RUN_LABEL}-{index:02d}-{case['case_id']}"
        extraction = results_by_case.get(case["case_id"])
        if extraction is None:
            extraction = {
                "ok": False,
                "trace_id": session_id,
                "case_id": case["case_id"],
                "model_id": modal_status()["model_id"],
                "backend": "modal_http",
                "fallback_used": False,
                "booking": None,
                "blocker": "batch_result_missing_for_case",
                "validation": {"valid": False, "errors": ["batch_result_missing_for_case"]},
            }
        row_started = time.monotonic()
        body = process_case_with_extraction(
            case=case,
            extraction=extraction,
            session_id=session_id,
            venue_context=venue_context,
            store=store,
        )
        row = build_row(
            case=case,
            session_id=session_id,
            status_code=200 if body.get("ok") else 502,
            body=body,
            trace_body={"ok": True, "trace": body.get("trace")},
            wall_clock_seconds=round(time.monotonic() - row_started, 3),
        )
        row["batch_latency_ms"] = batch.get("latency_ms")
        row["batch_timing_ms"] = batch.get("timing_ms")
        rows.append(row)
    return rows, "completed_requested_cases"


def post_modal_batch(payload: dict[str, Any], *, timeout: float) -> dict[str, Any]:
    url = modal_batch_url()
    token = os.environ.get("APP_MODAL_AUTH_TOKEN")
    if not url or not token:
        return {
            "ok": False,
            "backend": "modal_http",
            "fallback_used": False,
            "results": [],
            "blocker": "APP_MODAL_BATCH_URL/APP_MODAL_BASE_URL and APP_MODAL_AUTH_TOKEN must be configured.",
            "validation": {"valid": False, "errors": ["modal_batch_config_missing"]},
        }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        return {
            "ok": False,
            "backend": "modal_http",
            "fallback_used": False,
            "results": [],
            "blocker": f"Modal batch HTTP {exc.code}: {detail}",
            "validation": {"valid": False, "errors": ["modal_batch_http_error"]},
        }
    except Exception as exc:
        return {
            "ok": False,
            "backend": "modal_http",
            "fallback_used": False,
            "results": [],
            "blocker": f"{type(exc).__name__}: {str(exc)[:800]}",
            "validation": {"valid": False, "errors": ["modal_batch_request_failed"]},
        }


def modal_batch_url() -> str:
    explicit = os.environ.get("APP_MODAL_BATCH_URL", "").strip()
    if explicit:
        return explicit
    base = os.environ.get("APP_MODAL_BASE_URL", "").strip()
    if not base:
        return ""
    return base


def process_case_with_extraction(
    *,
    case: dict[str, Any],
    extraction: dict[str, Any],
    session_id: str,
    venue_context: dict[str, Any],
    store: InMemoryConversationStore,
) -> dict[str, Any]:
    payload = {
        "session_id": session_id,
        "message_id": f"{session_id}-1",
        "sender_phone": case["phone"],
        "text": case["message"],
        "trace_id": session_id,
        "scenario": "normal",
    }
    envelope = normalize_simulator_envelope(payload)
    session = process_message_with_extraction(
        envelope=envelope,
        payload=payload,
        extraction=extraction,
        venue_context=venue_context,
        store=store,
        trace_id=session_id,
        trace_label="Simulator WhatsApp message normalized",
        validation_label="Modal batch extraction validated",
    )
    return {
        "ok": session["terminal_state"] != "failed_model",
        "conversation": session,
        "trace": {
            "session_id": session_id,
            "trace_id": session.get("trace_id"),
            "raw_message": ((session.get("turns") or [{}])[-1].get("raw_message", "")),
            "model_extraction": session.get("model_extraction"),
            "model_validation": session.get("model_validation"),
            "truth_check_initial": session.get("truth_check_initial"),
            "backend_action": session.get("status"),
            "outbound_message": session.get("outbound_message"),
            "send_adapter": session.get("send_adapter"),
            "terminal_state": session.get("terminal_state"),
            "runtime_axes": runtime_axes_from_extraction(extraction),
            "agent_trace": session.get("agent_trace", []),
        },
    }


def batch_blocker_row(batch: dict[str, Any], case: dict[str, Any], wall_clock_seconds: float) -> dict[str, Any]:
    return {
        "case_id": case.get("case_id", "batch"),
        "seed_status": case.get("seed_status"),
        "seed_tone": case.get("seed_tone"),
        "session_id": f"{RUN_LABEL}-batch-blocker",
        "http_status": 0,
        "wall_clock_seconds": wall_clock_seconds,
        "passed": False,
        "first_failure": "modal_batch",
        "blocker": batch.get("blocker", "modal_batch_failed"),
        "blocker_is_global": True,
        "fallback_used": batch.get("fallback_used"),
        "validation": batch.get("validation", {}),
        "backend_action": None,
        "expected_backend_action": case.get("expected_backend_action"),
        "runtime_axes": runtime_axes_from_extraction(batch),
        "checks": [check("modal_batch_ok", False, batch.get("blocker"))],
        "model_extraction": batch,
        "trace_response": None,
    }


def build_row(
    *,
    case: dict[str, Any],
    session_id: str,
    status_code: int,
    body: dict[str, Any],
    trace_body: dict[str, Any] | None,
    wall_clock_seconds: float,
) -> dict[str, Any]:
    conversation = body.get("conversation") if isinstance(body.get("conversation"), dict) else {}
    extraction = conversation.get("model_extraction") if isinstance(conversation.get("model_extraction"), dict) else {}
    booking = extraction.get("booking") if isinstance(extraction.get("booking"), dict) else {}
    validation = extraction.get("validation") if isinstance(extraction.get("validation"), dict) else {}
    checks = objective_checks(case, status_code, body, conversation, extraction, booking, validation)
    first_failure = next((check["name"] for check in checks if not check["passed"]), "")
    blocker = str(extraction.get("blocker") or body.get("blocker") or "")
    return {
        "case_id": case["case_id"],
        "seed_status": case.get("seed_status"),
        "seed_tone": case.get("seed_tone"),
        "session_id": session_id,
        "http_status": status_code,
        "wall_clock_seconds": wall_clock_seconds,
        "passed": all(check["passed"] for check in checks),
        "first_failure": first_failure,
        "blocker": blocker,
        "blocker_is_global": bool(blocker and not extraction.get("raw_text") and status_code in {0, 401, 502}),
        "fallback_used": extraction.get("fallback_used"),
        "validation": validation,
        "backend_action": conversation.get("status"),
        "expected_backend_action": case.get("expected_backend_action"),
        "runtime_axes": runtime_axes_from_extraction(extraction),
        "checks": checks,
        "model_extraction": extraction,
        "trace_response": trace_body,
    }


def objective_checks(
    case: dict[str, Any],
    status_code: int,
    body: dict[str, Any],
    conversation: dict[str, Any],
    extraction: dict[str, Any],
    booking: dict[str, Any],
    validation: dict[str, Any],
) -> list[dict[str, Any]]:
    customer = booking.get("customer") if isinstance(booking.get("customer"), dict) else {}
    expected_backend = case.get("expected_backend_action")
    checks = [
        check("http_200", status_code == 200, status_code),
        check("response_ok", body.get("ok") is True, body.get("ok")),
        check("model_ok", extraction.get("ok") is True, extraction.get("ok")),
        check("fallback_false", extraction.get("fallback_used") is False, extraction.get("fallback_used")),
        check("schema_valid", validation.get("valid") is True, validation),
        check("customer_name", norm(customer.get("name")) == norm(case.get("customer_name")), customer.get("name")),
        check("customer_phone", norm_phone(customer.get("phone")) == norm_phone(case.get("phone")), customer.get("phone")),
        check("sport", norm(booking.get("sport")) == norm(case.get("activity")), booking.get("sport")),
    ]
    if case.get("players") is not None:
        checks.append(check("players", booking.get("players") == case.get("players"), booking.get("players")))
    if expected_backend:
        checks.append(check("backend_action", conversation.get("status") == expected_backend, conversation.get("status")))
    return checks


def model_context(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "slots": context["slots"],
        "venues": context["venues"],
        "bookings": context.get("bookings", []),
        "registered_teams": context.get("registered_teams", []),
        "players": context.get("players", []),
        "decision": context["decision"],
    }


def check(name: str, passed: bool, observed: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "observed": observed}


def runtime_axes_from_extraction(extraction: dict[str, Any]) -> dict[str, Any]:
    return {
        "lifecycle_stage": "testing",
        "app_host": "local",
        "model_runtime": "modal",
        "model_backend": extraction.get("backend", "modal_http"),
        "inference_engine": extraction.get("inference_engine", "unknown"),
        "model_artifact_format": extraction.get("model_artifact_format", "unknown"),
        "quantization": extraction.get("quantization", "unknown"),
        "model_id": extraction.get("model_id", modal_status()["model_id"]),
        "fallback_used": extraction.get("fallback_used", False),
    }


def build_summary(
    *,
    args: argparse.Namespace,
    cases: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    stopped_reason: str,
    wall_clock_seconds: float,
) -> dict[str, Any]:
    failed_rows = [row for row in rows if not row.get("passed")]
    return {
        "run_label": RUN_LABEL,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "approval": APPROVAL,
        "max_seconds": args.max_seconds,
        "transport": args.transport,
        "wall_clock_seconds": wall_clock_seconds,
        "requested": len(cases),
        "attempted": len([row for row in rows if row.get("case_id") != "suite-timeout"]),
        "passed": len([row for row in rows if row.get("passed")]),
        "failed": len(failed_rows),
        "stopped_reason": stopped_reason,
        "modal_status": redacted_modal_status(),
        "proof_boundary": (
            "Local v2 seeded demo-world requests through server-side Modal extraction. "
            "This is a seed smoke set, not a broad eval, hosted Space proof, live WhatsApp proof, "
            "public release, or judge-ready claim."
        ),
        "runtime_axes": runtime_axes_from_extraction(rows[0].get("model_extraction", {}) if rows else {}),
        "case_results": [
            {
                "case_id": row.get("case_id"),
                "passed": row.get("passed"),
                "first_failure": row.get("first_failure"),
                "backend_action": row.get("backend_action"),
                "expected_backend_action": row.get("expected_backend_action"),
                "fallback_used": row.get("fallback_used"),
                "validation": row.get("validation"),
                "wall_clock_seconds": row.get("wall_clock_seconds"),
            }
            for row in rows
        ],
    }


def timeout_row(message: str, index: int) -> dict[str, Any]:
    return {
        "case_id": "suite-timeout",
        "session_id": f"{RUN_LABEL}-{index:02d}-timeout",
        "http_status": 0,
        "wall_clock_seconds": 0,
        "passed": False,
        "first_failure": "suite_deadline_exceeded",
        "blocker": message,
        "blocker_is_global": True,
        "fallback_used": False,
        "validation": {"valid": False, "errors": ["suite_deadline_exceeded"]},
        "backend_action": None,
        "expected_backend_action": None,
        "runtime_axes": runtime_axes_from_extraction({}),
        "checks": [check("suite_deadline", False, message)],
        "model_extraction": {},
        "trace_response": None,
    }


def write_artifacts(summary: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, str]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    evidence_root = ROOT / "evidence" / f"modal-demo-world-suite-{timestamp}"
    evidence_root.mkdir(parents=True, exist_ok=True)
    summary_path = evidence_root / "summary.json"
    rows_path = evidence_root / "rows.jsonl"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    rows_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n")
    return {
        "summary": str(summary_path.relative_to(REPO_ROOT)),
        "rows_jsonl": str(rows_path.relative_to(REPO_ROOT)),
    }


def redacted_modal_status() -> dict[str, Any]:
    status = modal_status()
    return {
        "configured": status.get("configured"),
        "base_url_configured": status.get("base_url_configured"),
        "auth_configured": status.get("auth_configured"),
        "model_id": status.get("model_id"),
        "timeout_seconds": status.get("timeout_seconds"),
    }


def norm(value: Any) -> str:
    return " ".join(str(value or "").lower().replace("-", " ").split())


def norm_phone(value: Any) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in os.environ:
            continue
        os.environ[key] = value.strip().strip("'\"")


@contextmanager
def deadline(seconds: float):
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def raise_timeout(signum: int, frame: object) -> None:
        raise TimeoutError(f"Modal demo-world suite exceeded approved guardrail after {round(seconds, 3)} seconds.")

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


if __name__ == "__main__":
    raise SystemExit(main())
