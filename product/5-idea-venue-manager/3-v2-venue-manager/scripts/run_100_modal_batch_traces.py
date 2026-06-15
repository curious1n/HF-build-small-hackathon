#!/usr/bin/env python3
"""Run the 100 synthetic Venue Manager cases through Modal batch extraction.

This script is built for human-operated runs: it writes a log, progress file,
JSONL trace rows, and a summary while avoiding token/secret output. Actual paid
Modal work requires --approved-paid-modal-run.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from multiprocessing import get_context
from pathlib import Path
from queue import Empty
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
IDEA_ROOT = ROOT.parent
REPO_ROOT = ROOT.parents[2]
SPACE_ROOT = ROOT / "space"
sys.path.insert(0, str(SPACE_ROOT))

from floodlight_space.conversation_service import process_message_with_extraction  # noqa: E402
from floodlight_space.conversation_store import InMemoryConversationStore  # noqa: E402
from floodlight_space.fixtures import build_bootstrap  # noqa: E402
from floodlight_space.modal_client import modal_status  # noqa: E402
from floodlight_space.whatsapp_adapter import normalize_simulator_envelope  # noqa: E402


RUN_LABEL = "venue-manager-v2-100-modal-batch-traces"
MODEL_ID = "nvidia/Nemotron-Cascade-2-30B-A3B"
SOURCE_CASES = (
    IDEA_ROOT
    / "2-sport-agnostic-venue-agent"
    / "eval"
    / "cases"
    / "booking_100_message_cases.jsonl"
)
DEFAULT_RUNS_ROOT = ROOT / "eval" / "runs"
APPROVAL_TEXT = (
    "User-operated 100-case Venue Manager Modal/Nemotron batch trace run. "
    "Requires explicit --approved-paid-modal-run; recommended guard: max $20, "
    "max 20 minutes, stop after all 100 cases, first global Modal blocker, or timeout."
)


class RunLogger:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.log_path.open("a", encoding="utf-8")
        self.started = time.monotonic()

    def close(self) -> None:
        self._handle.close()

    def __call__(self, message: str) -> None:
        elapsed = time.monotonic() - self.started
        line = f"[{elapsed:8.1f}s] {message}"
        print(line, flush=True)
        self._handle.write(line + "\n")
        self._handle.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases-jsonl", type=Path, default=SOURCE_CASES)
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--max-seconds", type=float, default=1200.0)
    parser.add_argument("--chunk-size", type=int, default=10)
    parser.add_argument("--chunk-timeout-seconds", type=float, default=300.0)
    parser.add_argument("--warmup-timeout-seconds", type=float, default=900.0)
    parser.add_argument("--scaledown-window", type=int, default=900)
    parser.add_argument("--deploy-warm", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--warmup", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--scale-down", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and print paths without Modal/HF calls.")
    parser.add_argument(
        "--approved-paid-modal-run",
        action="store_true",
        help="Required before deploying warm Modal containers or calling the GPU endpoint.",
    )
    parser.add_argument("--upload-hf-dataset", action="store_true")
    parser.add_argument("--dataset-id", help="HF Dataset repo id, e.g. namespace/venue-manager-v2-agent-traces.")
    parser.add_argument("--dataset-private", action="store_true")
    parser.add_argument("--hf-token-env", default="HF_TOKEN_2")
    parser.add_argument("--no-create-dataset", action="store_true")
    args = parser.parse_args()

    if args.chunk_size < 1 or args.chunk_size > 12:
        raise SystemExit("--chunk-size must be between 1 and 12 because the Modal endpoint caps batch items at 12.")

    load_env(REPO_ROOT / ".env")
    load_env(IDEA_ROOT / ".env.modal.local")

    cases = load_cases(args.cases_jsonl)
    run_dir = args.runs_root / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    latest_link = args.runs_root / "latest"

    logger = RunLogger(run_dir / "run.log")
    progress_path = run_dir / "progress.json"
    summary_path = run_dir / "summary.json"
    rows_path = run_dir / "agent_trace.jsonl"
    dataset_card_path = run_dir / "README.md"

    started = time.monotonic()
    rows: list[dict[str, Any]] = []
    stopped_reason = ""
    scaled_down = False
    uploaded: dict[str, Any] | None = None

    try:
        logger(f"run_dir={repo_path(run_dir)}")
        logger(f"cases={len(cases)} source={repo_path(args.cases_jsonl)}")
        logger(f"monitor: tail -f {repo_path(run_dir / 'run.log')}")
        logger(f"monitor: python3 -m json.tool {repo_path(progress_path)}")
        write_progress(progress_path, stage="validated", args=args, rows=rows, total=len(cases), run_dir=run_dir)

        if args.dry_run:
            summary = build_summary(args, rows, "dry_run", started, run_dir, uploaded=None, scaled_down=False)
            write_json(summary_path, summary)
            write_dataset_card(dataset_card_path, summary, args, source_cases=args.cases_jsonl)
            logger("dry-run complete; no Modal deploy/call or HF upload performed")
            return 0

        if not args.approved_paid_modal_run:
            stopped_reason = "paid_modal_approval_missing"
            logger("blocked: pass --approved-paid-modal-run to start paid Modal GPU work")
            logger("recommended guard: max $20, max 20 minutes, stop after 100 cases, first global blocker, or timeout")
            return 2

        update_latest_link(latest_link, run_dir)
        logger(f"latest symlink now points to {repo_path(run_dir)}")

        if args.deploy_warm:
            write_progress(progress_path, stage="deploying_warm_modal", args=args, rows=rows, total=len(cases), run_dir=run_dir)
            run_command(
                [
                    str(REPO_ROOT / ".venv" / "bin" / "python"),
                    str(REPO_ROOT / "scripts" / "setup_modal_usage.py"),
                    "deploy-venue-manager",
                    "--min-containers",
                    "1",
                    "--scaledown-window",
                    str(args.scaledown_window),
                ],
                logger=logger,
                check=True,
            )

        if args.warmup:
            write_progress(progress_path, stage="warmup_modal_preload", args=args, rows=rows, total=len(cases), run_dir=run_dir)
            logger(
                "warmup request started; Modal preload can look quiet for several minutes "
                "while the H100 container starts and loads vLLM weights"
            )
            warmup_result = post_modal_batch_with_heartbeat(
                {"items": [modal_item(cases[0], index=0, run_id=args.run_id, warmup=True)]},
                timeout=args.warmup_timeout_seconds,
                logger=logger,
                label="warmup/preload",
            )
            logger(
                "warmup complete: "
                f"ok={warmup_result.get('ok')} latency_ms={warmup_result.get('latency_ms')} "
                f"blocker={short(warmup_result.get('blocker'))}"
            )
            if not warmup_result.get("ok"):
                stopped_reason = "warmup_blocked"
                rows.append(global_blocker_row(warmup_result, args.run_id, "warmup"))
                write_rows(rows_path, rows)
                write_progress(progress_path, stage=stopped_reason, args=args, rows=rows, total=len(cases), run_dir=run_dir)
                return 1

        store = InMemoryConversationStore()
        venue_context = model_context(build_bootstrap("normal"))
        chunks = list(chunked(cases, args.chunk_size))
        logger(f"sending {len(cases)} cases in {len(chunks)} Modal batch chunks of up to {args.chunk_size}")

        for chunk_index, chunk in enumerate(chunks, start=1):
            elapsed = time.monotonic() - started
            if elapsed >= args.max_seconds:
                stopped_reason = "deadline_before_next_chunk"
                logger(stopped_reason)
                break

            write_progress(
                progress_path,
                stage=f"running_chunk_{chunk_index}_of_{len(chunks)}",
                args=args,
                rows=rows,
                total=len(cases),
                run_dir=run_dir,
            )
            payload = {
                "items": [
                    modal_item(case, index=len(rows) + offset + 1, run_id=args.run_id)
                    for offset, case in enumerate(chunk)
                ]
            }
            chunk_started = time.monotonic()
            batch_timeout = min(args.chunk_timeout_seconds, max(1.0, args.max_seconds - elapsed))
            batch = post_modal_batch_with_heartbeat(
                payload,
                timeout=batch_timeout,
                logger=logger,
                label=f"chunk {chunk_index}/{len(chunks)}",
            )
            batch_seconds = round(time.monotonic() - chunk_started, 3)
            if not isinstance(batch.get("results"), list):
                rows.append(global_blocker_row(batch, args.run_id, f"chunk-{chunk_index}"))
                stopped_reason = "global_modal_batch_blocker"
                logger(f"chunk {chunk_index}/{len(chunks)} global blocker: {short(batch.get('blocker'))}")
                write_rows(rows_path, rows)
                break

            results_by_case = {
                str(result.get("case_id")): result
                for result in batch.get("results", [])
                if isinstance(result, dict)
            }
            for offset, case in enumerate(chunk):
                index = len(rows) + 1
                extraction = results_by_case.get(case["case_id"]) or missing_result(case, args.run_id, index)
                row = build_trace_row(
                    case=case,
                    extraction=extraction,
                    index=index,
                    run_id=args.run_id,
                    venue_context=venue_context,
                    store=store,
                    batch=batch,
                    batch_seconds=batch_seconds,
                )
                rows.append(row)
            write_rows(rows_path, rows)
            failed = len([row for row in rows if not row.get("passed")])
            fallback = len([row for row in rows if row.get("fallback_used") is True])
            logger(
                f"chunk {chunk_index}/{len(chunks)} complete: attempted={len(rows)}/{len(cases)} "
                f"passed={len(rows) - failed} failed={failed} fallback_true={fallback} "
                f"batch_seconds={batch_seconds}"
            )
            if rows and rows[-1].get("blocker_is_global"):
                stopped_reason = "global_blocker"
                break

        if not stopped_reason:
            stopped_reason = "completed_requested_cases" if len(rows) == len(cases) else "incomplete_without_global_blocker"

        summary = build_summary(args, rows, stopped_reason, started, run_dir, uploaded=uploaded, scaled_down=False)
        write_json(summary_path, summary)
        write_dataset_card(dataset_card_path, summary, args, source_cases=args.cases_jsonl)
        write_progress(progress_path, stage="local_artifacts_written", args=args, rows=rows, total=len(cases), run_dir=run_dir)

        if args.upload_hf_dataset:
            uploaded = upload_dataset(args, rows_path, summary_path, dataset_card_path, logger)
            summary = build_summary(args, rows, stopped_reason, started, run_dir, uploaded=uploaded, scaled_down=False)
            write_json(summary_path, summary)
            write_dataset_card(dataset_card_path, summary, args, source_cases=args.cases_jsonl)

        return 0 if rows and len(rows) == len(cases) and not any(row.get("blocker_is_global") for row in rows) else 1
    except SystemExit as exc:
        if not stopped_reason:
            stopped_reason = "script_blocked"
        logger(f"stopped: {short(exc)}")
        return int(exc.code) if isinstance(exc.code, int) else 1
    except KeyboardInterrupt:
        stopped_reason = "keyboard_interrupt"
        logger("keyboard interrupt received; moving to scale-down/final summary")
        return_code = 130
        return return_code
    finally:
        if not args.dry_run and args.approved_paid_modal_run and args.scale_down:
            try:
                logger("scaling Modal endpoint back to min_containers=0 scaledown_window=60")
                run_command(
                    [
                        str(REPO_ROOT / ".venv" / "bin" / "python"),
                        str(REPO_ROOT / "scripts" / "setup_modal_usage.py"),
                        "deploy-venue-manager",
                        "--min-containers",
                        "0",
                        "--scaledown-window",
                        "60",
                    ],
                    logger=logger,
                    check=False,
                )
                scaled_down = True
            except Exception as exc:  # pragma: no cover - best-effort emergency path
                logger(f"scale-down failed: {type(exc).__name__}: {short(exc)}")
        final_summary = build_summary(
            args,
            rows,
            stopped_reason or ("dry_run" if args.dry_run else "finished"),
            started,
            run_dir,
            uploaded=uploaded,
            scaled_down=scaled_down,
        )
        write_json(summary_path, final_summary)
        write_dataset_card(dataset_card_path, final_summary, args, source_cases=args.cases_jsonl)
        if uploaded and args.upload_hf_dataset:
            try:
                refresh_dataset_metadata(args, summary_path, dataset_card_path, logger, uploaded)
            except Exception as exc:  # pragma: no cover - best-effort metadata refresh
                logger(f"final HF dataset metadata refresh failed: {type(exc).__name__}: {short(exc)}")
        write_progress(progress_path, stage=final_summary["stopped_reason"], args=args, rows=rows, total=len(cases), run_dir=run_dir)
        logger(f"summary={repo_path(summary_path)}")
        logger(f"agent_trace_jsonl={repo_path(rows_path)}")
        logger.close()


def load_cases(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Case file not found: {path}")
    cases: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        raw = json.loads(line)
        turns = raw.get("turns")
        if not isinstance(turns, list) or len(turns) != 1:
            raise SystemExit(f"Expected exactly one turn at {path}:{line_number}")
        turn = turns[0] if isinstance(turns[0], dict) else {}
        text = str(turn.get("text") or "").strip()
        if not text:
            raise SystemExit(f"Missing turn text at {path}:{line_number}")
        case = dict(raw)
        case["message"] = text
        case["phone"] = str(turn.get("sender_phone") or "")
        case["turn_index"] = turn.get("turn_index", 1)
        cases.append(case)
    if len(cases) != 100:
        raise SystemExit(f"Expected 100 cases, found {len(cases)} in {path}")
    return cases


def modal_item(case: dict[str, Any], *, index: int, run_id: str, warmup: bool = False) -> dict[str, Any]:
    trace_id = f"{RUN_LABEL}-{run_id}-{'warmup' if warmup else f'{index:03d}-{case['case_id']}'}"
    return {
        "case_id": f"warmup-{case['case_id']}" if warmup else case["case_id"],
        "trace_id": trace_id,
        "message": case["message"],
        "venue_context": model_context(build_bootstrap("normal")),
    }


def post_modal_batch(payload: dict[str, Any], *, timeout: float) -> dict[str, Any]:
    url = os.environ.get("APP_MODAL_BATCH_URL", "").strip() or os.environ.get("APP_MODAL_BASE_URL", "").strip()
    token = os.environ.get("APP_MODAL_AUTH_TOKEN")
    status = modal_status()
    if not url or not token:
        return {
            "ok": False,
            "backend": "modal_http",
            "model_id": status.get("model_id", MODEL_ID),
            "fallback_used": False,
            "results": [],
            "blocker": "APP_MODAL_BASE_URL/APP_MODAL_BATCH_URL and APP_MODAL_AUTH_TOKEN must be configured.",
            "validation": {"valid": False, "errors": ["modal_batch_config_missing"]},
        }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        return blocked_batch(f"Modal batch HTTP {exc.code}: {detail}", started)
    except Exception as exc:
        return blocked_batch(f"{type(exc).__name__}: {str(exc)[:800]}", started)
    result.setdefault("client_latency_ms", round((time.time() - started) * 1000))
    result.setdefault("fallback_used", False)
    result.setdefault("backend", "modal_http")
    result.setdefault("model_id", status.get("model_id", MODEL_ID))
    return result


def post_modal_batch_with_heartbeat(
    payload: dict[str, Any],
    *,
    timeout: float,
    logger: RunLogger,
    label: str,
    heartbeat_seconds: float = 30.0,
) -> dict[str, Any]:
    started = time.monotonic()
    wall_started = time.time()
    context = get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=_post_modal_batch_child, args=(payload, timeout, queue))
    process.start()
    try:
        while process.is_alive():
            process.join(timeout=heartbeat_seconds)
            if process.is_alive():
                elapsed = round(time.monotonic() - started, 1)
                logger(f"{label} still waiting after {elapsed}s; request timeout is {timeout}s")
                if elapsed > timeout + heartbeat_seconds:
                    process.terminate()
                    process.join(timeout=5)
                    return blocked_batch(f"{label} exceeded request timeout watchdog", wall_started)

        try:
            status, result = queue.get_nowait()
        except Empty:
            return blocked_batch(f"{label} process exited without a result", wall_started)
        logger(f"{label} returned after {round(time.monotonic() - started, 1)}s")
        if status == "ok":
            return result
        return blocked_batch(str(result), wall_started)
    except KeyboardInterrupt:
        logger(f"{label} interrupted; terminating in-flight Modal request process")
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
        raise


def _post_modal_batch_child(payload: dict[str, Any], timeout: float, queue: Any) -> None:
    try:
        queue.put(("ok", post_modal_batch(payload, timeout=timeout)))
    except BaseException as exc:  # pragma: no cover - only used during operator runs
        queue.put(("error", f"{type(exc).__name__}: {str(exc)[:800]}"))


def blocked_batch(blocker: str, started: float) -> dict[str, Any]:
    return {
        "ok": False,
        "backend": "modal_http",
        "model_id": MODEL_ID,
        "fallback_used": False,
        "latency_ms": round((time.time() - started) * 1000),
        "results": [],
        "blocker": blocker,
        "validation": {"valid": False, "errors": ["modal_batch_request_failed"]},
    }


def build_trace_row(
    *,
    case: dict[str, Any],
    extraction: dict[str, Any],
    index: int,
    run_id: str,
    venue_context: dict[str, Any],
    store: InMemoryConversationStore,
    batch: dict[str, Any],
    batch_seconds: float,
) -> dict[str, Any]:
    session_id = f"{RUN_LABEL}-{run_id}-{index:03d}-{case['case_id']}"
    payload = {
        "session_id": session_id,
        "message_id": f"{session_id}-1",
        "sender_phone": case.get("phone", ""),
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
        trace_label="Synthetic WhatsApp example normalized",
        validation_label="Modal batch extraction validated",
    )
    validation = extraction.get("validation") if isinstance(extraction.get("validation"), dict) else {}
    booking = extraction.get("booking") if isinstance(extraction.get("booking"), dict) else {}
    checks = trace_checks(case=case, extraction=extraction, validation=validation, session=session, booking=booking)
    return {
        "record_type": "agent_trace",
        "run_label": RUN_LABEL,
        "run_id": run_id,
        "case_index": index,
        "case_id": case["case_id"],
        "suite_id": case.get("suite_id"),
        "category": case.get("category"),
        "scenario": case.get("scenario"),
        "language_hint": case.get("language_hint"),
        "privacy": case.get("privacy", "synthetic"),
        "input_text": case["message"],
        "source_case": case,
        "session_id": session_id,
        "trace_id": session.get("trace_id"),
        "passed": all(check["passed"] for check in checks),
        "first_failure": next((check["name"] for check in checks if not check["passed"]), ""),
        "checks": checks,
        "fallback_used": extraction.get("fallback_used"),
        "validation": validation,
        "backend_action": session.get("status"),
        "expected_final_backend_state": case.get("expected_final_backend_state"),
        "expected_model_intent": case.get("expected_model_intent"),
        "model_extraction": extraction,
        "agent_trace": session.get("agent_trace", []),
        "truth_check_initial": session.get("truth_check_initial"),
        "outbound_message": session.get("outbound_message"),
        "send_adapter": session.get("send_adapter"),
        "terminal_state": session.get("terminal_state"),
        "runtime_axes": runtime_axes_from_extraction(extraction),
        "batch_latency_ms": batch.get("latency_ms"),
        "batch_client_latency_ms": batch.get("client_latency_ms"),
        "batch_timing_ms": batch.get("timing_ms"),
        "batch_seconds": batch_seconds,
        "blocker": extraction.get("blocker", ""),
        "blocker_is_global": False,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def trace_checks(
    *,
    case: dict[str, Any],
    extraction: dict[str, Any],
    validation: dict[str, Any],
    session: dict[str, Any],
    booking: dict[str, Any],
) -> list[dict[str, Any]]:
    checks = [
        check("model_ok", extraction.get("ok") is True, extraction.get("ok")),
        check("fallback_false", extraction.get("fallback_used") is False, extraction.get("fallback_used")),
        check("schema_valid", validation.get("valid") is True, validation),
        check("agent_trace_present", bool(session.get("agent_trace")), len(session.get("agent_trace", []))),
    ]
    expected_intent = case.get("expected_model_intent")
    if expected_intent:
        checks.append(check("expected_model_intent", norm(booking.get("intent")) == norm(expected_intent), booking.get("intent")))
    expected_backend = case.get("expected_final_backend_state")
    if expected_backend in {"ready_for_owner_review", "needs_player_info", "conflict_possible"}:
        checks.append(check("expected_backend_state", session.get("status") == expected_backend, session.get("status")))
    return checks


def check(name: str, passed: bool, observed: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "observed": observed}


def missing_result(case: dict[str, Any], run_id: str, index: int) -> dict[str, Any]:
    return {
        "ok": False,
        "trace_id": f"{RUN_LABEL}-{run_id}-{index:03d}-{case['case_id']}",
        "case_id": case["case_id"],
        "model_id": MODEL_ID,
        "backend": "modal_http",
        "fallback_used": False,
        "booking": None,
        "blocker": "batch_result_missing_for_case",
        "validation": {"valid": False, "errors": ["batch_result_missing_for_case"]},
    }


def global_blocker_row(batch: dict[str, Any], run_id: str, stage: str) -> dict[str, Any]:
    return {
        "record_type": "agent_trace",
        "run_label": RUN_LABEL,
        "run_id": run_id,
        "case_index": 0,
        "case_id": stage,
        "privacy": "synthetic",
        "input_text": "",
        "source_case": {},
        "session_id": f"{RUN_LABEL}-{run_id}-{stage}",
        "trace_id": f"{RUN_LABEL}-{run_id}-{stage}",
        "passed": False,
        "first_failure": "global_modal_batch_blocker",
        "checks": [check("modal_batch_ok", False, batch.get("blocker"))],
        "fallback_used": batch.get("fallback_used", False),
        "validation": batch.get("validation", {}),
        "backend_action": None,
        "expected_final_backend_state": None,
        "expected_model_intent": None,
        "model_extraction": batch,
        "agent_trace": [],
        "truth_check_initial": None,
        "outbound_message": None,
        "send_adapter": None,
        "terminal_state": "global_blocker",
        "runtime_axes": runtime_axes_from_extraction(batch),
        "batch_latency_ms": batch.get("latency_ms"),
        "batch_client_latency_ms": batch.get("client_latency_ms"),
        "batch_timing_ms": batch.get("timing_ms"),
        "batch_seconds": None,
        "blocker": batch.get("blocker", "modal_batch_failed"),
        "blocker_is_global": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def build_summary(
    args: argparse.Namespace,
    rows: list[dict[str, Any]],
    stopped_reason: str,
    started: float,
    run_dir: Path,
    *,
    uploaded: dict[str, Any] | None,
    scaled_down: bool,
) -> dict[str, Any]:
    attempted = len([row for row in rows if row.get("case_index")])
    failed_rows = [row for row in rows if row.get("passed") is not True]
    fallback_true = [row for row in rows if row.get("fallback_used") is True]
    schema_invalid = [row for row in rows if (row.get("validation") or {}).get("valid") is not True]
    return {
        "run_label": RUN_LABEL,
        "run_id": args.run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "approval": APPROVAL_TEXT,
        "proof_boundary": (
            "User-operated 100-case synthetic trace generation through local-to-Modal batch extraction. "
            "This is trace capture, not hosted Space proof, live WhatsApp proof, public release, "
            "judge readiness, or human-reviewed model-quality evaluation."
        ),
        "source_cases": repo_path(args.cases_jsonl),
        "run_dir": repo_path(run_dir),
        "max_seconds": args.max_seconds,
        "chunk_size": args.chunk_size,
        "wall_clock_seconds": round(time.monotonic() - started, 3),
        "requested": 100,
        "attempted": attempted,
        "passed": len([row for row in rows if row.get("passed") is True]),
        "failed": len(failed_rows),
        "fallback_true": len(fallback_true),
        "schema_invalid": len(schema_invalid),
        "stopped_reason": stopped_reason,
        "modal_status": redacted_modal_status(),
        "runtime_axes": runtime_axes_from_extraction(rows[0].get("model_extraction", {}) if rows else {}),
        "uploaded": uploaded,
        "scaled_down": scaled_down,
        "artifacts": {
            "agent_trace_jsonl": repo_path(run_dir / "agent_trace.jsonl"),
            "summary": repo_path(run_dir / "summary.json"),
            "progress": repo_path(run_dir / "progress.json"),
            "log": repo_path(run_dir / "run.log"),
            "dataset_card": repo_path(run_dir / "README.md"),
        },
        "category_results": category_results(rows),
        "failed_case_ids": [row.get("case_id") for row in failed_rows[:25]],
    }


def category_results(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for row in rows:
        category = str(row.get("category") or "uncategorized")
        bucket = out.setdefault(category, {"attempted": 0, "passed": 0, "failed": 0})
        if row.get("case_index"):
            bucket["attempted"] += 1
        if row.get("passed") is True:
            bucket["passed"] += 1
        elif row.get("case_index"):
            bucket["failed"] += 1
    return out


def write_dataset_card(path: Path, summary: dict[str, Any], args: argparse.Namespace, *, source_cases: Path) -> None:
    uploaded = summary.get("uploaded") if isinstance(summary.get("uploaded"), dict) else {}
    dataset_id = uploaded.get("dataset_id") or args.dataset_id
    if not dataset_id and args.upload_hf_dataset:
        try:
            dataset_id = default_dataset_id()
        except SystemExit:
            dataset_id = "<not uploaded>"
    dataset_id = dataset_id or "<not uploaded>"
    text = f"""---
license: apache-2.0
task_categories:
- text-generation
language:
- en
tags:
- synthetic
- agent-trace
- venue-manager
- modal
- nemotron
pretty_name: Venue Manager v2 Agent Traces
---

# Venue Manager v2 Agent Traces

Synthetic 100-case trace capture for Floodlight Venue Manager v2.

- Source cases: `{repo_path(source_cases)}`
- Dataset target: `{dataset_id}`
- Model: `{MODEL_ID}`
- Runtime: Modal HTTP / vLLM / safetensors / bf16
- Privacy: synthetic booking messages only
- Proof boundary: trace capture only; not judge readiness, public release, hosted Space proof, live WhatsApp proof, or human-reviewed quality evaluation.

## Run Summary

```json
{json.dumps(summary, indent=2, sort_keys=True)}
```

## Files

- `data/agent_trace.jsonl`: one trace record per case
- `summary.json`: compact run summary and runtime axes
"""
    path.write_text(text, encoding="utf-8")


def refresh_dataset_metadata(
    args: argparse.Namespace,
    summary_path: Path,
    dataset_card_path: Path,
    logger: RunLogger,
    uploaded: dict[str, Any],
) -> None:
    dataset_id = str(uploaded.get("dataset_id") or args.dataset_id or default_dataset_id())
    token = os.environ.get(args.hf_token_env) or os.environ.get("HF_TOKEN")
    if not token:
        logger(f"skipping final HF metadata refresh: missing {args.hf_token_env} or HF_TOKEN")
        return
    try:
        from huggingface_hub import HfApi
    except ImportError:
        logger("skipping final HF metadata refresh: missing huggingface_hub")
        return

    api = HfApi(token=token)
    commit_message = f"Refresh Venue Manager v2 trace metadata {args.run_id}"
    api.upload_file(
        repo_id=dataset_id,
        repo_type="dataset",
        path_or_fileobj=str(summary_path),
        path_in_repo="summary.json",
        commit_message=commit_message,
    )
    api.upload_file(
        repo_id=dataset_id,
        repo_type="dataset",
        path_or_fileobj=str(dataset_card_path),
        path_in_repo="README.md",
        commit_message=commit_message,
    )
    logger(f"HF dataset metadata refreshed: https://huggingface.co/datasets/{dataset_id}")


def upload_dataset(
    args: argparse.Namespace,
    rows_path: Path,
    summary_path: Path,
    dataset_card_path: Path,
    logger: RunLogger,
) -> dict[str, Any]:
    dataset_id = args.dataset_id or default_dataset_id()
    token = os.environ.get(args.hf_token_env) or os.environ.get("HF_TOKEN")
    if not token:
        raise SystemExit(f"Missing {args.hf_token_env} or HF_TOKEN for HF Dataset upload.")
    try:
        from huggingface_hub import HfApi
    except ImportError as exc:
        raise SystemExit("Missing huggingface_hub in .venv.") from exc

    api = HfApi(token=token)
    if not args.no_create_dataset:
        api.create_repo(repo_id=dataset_id, repo_type="dataset", private=args.dataset_private, exist_ok=True)
        logger(f"HF dataset repo ready: {dataset_id}")
    commit_message = f"Add Venue Manager v2 100-case traces {args.run_id}"
    api.upload_file(
        repo_id=dataset_id,
        repo_type="dataset",
        path_or_fileobj=str(rows_path),
        path_in_repo="data/agent_trace.jsonl",
        commit_message=commit_message,
    )
    api.upload_file(
        repo_id=dataset_id,
        repo_type="dataset",
        path_or_fileobj=str(summary_path),
        path_in_repo="summary.json",
        commit_message=commit_message,
    )
    api.upload_file(
        repo_id=dataset_id,
        repo_type="dataset",
        path_or_fileobj=str(dataset_card_path),
        path_in_repo="README.md",
        commit_message=commit_message,
    )
    logger(f"HF dataset upload complete: https://huggingface.co/datasets/{dataset_id}")
    return {"dataset_id": dataset_id, "url": f"https://huggingface.co/datasets/{dataset_id}"}


def default_dataset_id() -> str:
    namespace = os.environ.get("HF_HACKATHON") or os.environ.get("HF_2")
    if not namespace:
        raise SystemExit("Pass --dataset-id or set HF_HACKATHON/HF_2.")
    return f"{namespace}/venue-manager-v2-agent-traces"


def run_command(command: list[str], *, logger: RunLogger, check: bool) -> subprocess.CompletedProcess[str]:
    logger(f"running: {display_command(command)}")
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=os.environ.copy(),
    )
    for line in result.stdout.splitlines():
        if line.strip():
            logger(f"  {line}")
    if check and result.returncode != 0:
        raise SystemExit(f"Command failed with exit code {result.returncode}: {display_command(command)}")
    return result


def display_command(command: list[str]) -> str:
    return " ".join(str(part) for part in command)


def write_progress(
    path: Path,
    *,
    stage: str,
    args: argparse.Namespace,
    rows: list[dict[str, Any]],
    total: int,
    run_dir: Path,
) -> None:
    attempted = len([row for row in rows if row.get("case_index")])
    failed = len([row for row in rows if row.get("passed") is not True])
    payload = {
        "stage": stage,
        "run_label": RUN_LABEL,
        "run_id": args.run_id,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_dir": repo_path(run_dir),
        "requested": total,
        "attempted": attempted,
        "passed": len([row for row in rows if row.get("passed") is True]),
        "failed": failed,
        "fallback_true": len([row for row in rows if row.get("fallback_used") is True]),
        "latest_case_id": rows[-1].get("case_id") if rows else None,
    }
    write_json(path, payload)


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + ("\n" if rows else ""), encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def update_latest_link(link: Path, run_dir: Path) -> None:
    try:
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(run_dir.name, target_is_directory=True)
    except OSError:
        pass


def model_context(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "slots": context["slots"],
        "venues": context["venues"],
        "bookings": context.get("bookings", []),
        "registered_teams": context.get("registered_teams", []),
        "players": context.get("players", []),
        "decision": context["decision"],
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


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in os.environ:
            continue
        os.environ[key] = value.strip().strip("'\"")


def chunked(values: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def norm(value: Any) -> str:
    return " ".join(str(value or "").lower().replace("-", " ").split())


def short(value: Any, limit: int = 180) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[: limit - 3] + "..."


if __name__ == "__main__":
    raise SystemExit(main())
