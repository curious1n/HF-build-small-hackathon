#!/usr/bin/env python3
"""Run one v2 world-demo scenario through the Modal-backed extractor."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
import signal
import sys
import time
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
from floodlight_space.modal_client import SAMPLE_USER_MESSAGE, modal_status  # noqa: E402


RUN_LABEL = "venue-manager-v2-world-modal-smoke"
APPROVAL = (
    "COAGENTS.md standing bounded approval: Venue Manager v2 Modal/Nemotron "
    "single-scenario smoke; max $20; max 15 minutes; stop after one world-demo "
    "scenario returns schema-valid fallback_used=false result or exact blocker."
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default="normal")
    parser.add_argument("--session-id", default=f"{RUN_LABEL}-normal-001")
    parser.add_argument("--trace-id", default=f"{RUN_LABEL}-normal-001")
    parser.add_argument("--message", default=SAMPLE_USER_MESSAGE)
    parser.add_argument("--max-seconds", type=float, default=900.0)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    load_env(REPO_ROOT / ".env")
    load_env(IDEA_ROOT / ".env.modal.local")

    previous_timeout = os.environ.get("APP_MODAL_TIMEOUT_SECONDS")
    os.environ["APP_MODAL_TIMEOUT_SECONDS"] = str(args.max_seconds)
    started = time.monotonic()
    response_status = 0
    body: dict[str, Any]
    trace_body: dict[str, Any] | None = None

    try:
        with deadline(args.max_seconds):
            client = TestClient(app_module.app)
            response = client.post(
                "/api/whatsapp/simulated-model-message",
                json={
                    "session_id": args.session_id,
                    "message_id": f"{args.session_id}-1",
                    "sender_phone": "+91 98765 43210",
                    "text": args.message,
                    "trace_id": args.trace_id,
                    "scenario": args.scenario,
                },
                timeout=args.max_seconds,
            )
            response_status = response.status_code
            body = response.json()
            if response_status == 200:
                trace_response = client.get(f"/api/conversations/{args.session_id}/trace")
                trace_body = trace_response.json()
    except TimeoutError as exc:
        body = {
            "ok": False,
            "conversation": None,
            "blocker": str(exc),
        }
    finally:
        if previous_timeout is None:
            os.environ.pop("APP_MODAL_TIMEOUT_SECONDS", None)
        else:
            os.environ["APP_MODAL_TIMEOUT_SECONDS"] = previous_timeout

    row = build_evidence_row(
        args=args,
        body=body,
        trace_body=trace_body,
        response_status=response_status,
        wall_clock_seconds=round(time.monotonic() - started, 3),
    )
    if args.write:
        path = evidence_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
        row["artifact"] = str(path.relative_to(REPO_ROOT))

    print(json.dumps(row, indent=2, sort_keys=True))
    return 0 if row["passed"] else 1


def build_evidence_row(
    *,
    args: argparse.Namespace,
    body: dict[str, Any],
    trace_body: dict[str, Any] | None,
    response_status: int,
    wall_clock_seconds: float,
) -> dict[str, Any]:
    conversation = body.get("conversation") if isinstance(body.get("conversation"), dict) else {}
    extraction = conversation.get("model_extraction") if isinstance(conversation.get("model_extraction"), dict) else {}
    validation = extraction.get("validation") if isinstance(extraction.get("validation"), dict) else {}
    runtime_axes = {}
    if isinstance(trace_body, dict):
        trace = trace_body.get("trace") if isinstance(trace_body.get("trace"), dict) else {}
        runtime_axes = trace.get("runtime_axes") if isinstance(trace.get("runtime_axes"), dict) else {}

    passed = bool(
        response_status == 200
        and body.get("ok")
        and extraction.get("ok")
        and extraction.get("fallback_used") is False
        and validation.get("valid") is True
        and conversation.get("terminal_state") != "failed_model"
    )
    return {
        "run_label": RUN_LABEL,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "approval": APPROVAL,
        "scenario": args.scenario,
        "session_id": args.session_id,
        "trace_id": args.trace_id,
        "max_seconds": args.max_seconds,
        "wall_clock_seconds": wall_clock_seconds,
        "http_status": response_status,
        "modal_status": redacted_modal_status(),
        "runtime_axes": runtime_axes or runtime_axes_from_extraction(extraction),
        "passed": passed,
        "fallback_used": extraction.get("fallback_used"),
        "validation": validation,
        "terminal_state": conversation.get("terminal_state"),
        "backend_action": conversation.get("status"),
        "first_failure": "" if passed else exact_failure(body, extraction),
        "proof_boundary": (
            "One local v2 world-demo simulator scenario through server-side Modal extraction. "
            "No broad eval, public release, live WhatsApp send, HF Space proof, or judge-ready claim."
        ),
        "response": body,
        "trace_response": trace_body,
    }


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


def redacted_modal_status() -> dict[str, Any]:
    status = modal_status()
    return {
        "configured": status.get("configured"),
        "base_url_configured": status.get("base_url_configured"),
        "auth_configured": status.get("auth_configured"),
        "model_id": status.get("model_id"),
        "timeout_seconds": status.get("timeout_seconds"),
    }


def exact_failure(body: dict[str, Any], extraction: dict[str, Any]) -> str:
    blocker = extraction.get("blocker") or body.get("blocker")
    if blocker:
        return str(blocker)
    validation = extraction.get("validation") if isinstance(extraction.get("validation"), dict) else {}
    errors = validation.get("errors") if isinstance(validation.get("errors"), list) else []
    if errors:
        return f"validation_errors={errors}"
    return "world_modal_smoke_failed"


def evidence_path() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return ROOT / "evidence" / f"modal-world-smoke-{timestamp}.json"


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
        raise TimeoutError(f"Modal world smoke exceeded approved guardrail after {round(seconds, 3)} seconds.")

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
