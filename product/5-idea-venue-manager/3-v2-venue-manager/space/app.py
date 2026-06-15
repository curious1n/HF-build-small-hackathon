from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def load_local_modal_env() -> None:
    current = Path(__file__).resolve()
    env_path = next(
        (parent / ".env.modal.local" for parent in current.parents if (parent / ".env.modal.local").exists()),
        None,
    )
    if env_path is None:
        return
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("APP_MODAL_"):
            os.environ.setdefault(key, value.strip().strip("'\""))


load_local_modal_env()

from fastapi import Body, Header
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from gradio import Server
from starlette.concurrency import run_in_threadpool

from floodlight_space.booking_flow import approve_booking_flow
from floodlight_space.conversation_service import (
    process_baileys_message,
    process_simulated_message,
    process_simulated_model_message,
)
from floodlight_space.conversation_store import InMemoryConversationStore
from floodlight_space.fixtures import build_bootstrap
from floodlight_space.modal_client import (
    SAMPLE_USER_MESSAGE,
    call_booking_extractor,
    modal_status as get_modal_status,
)
from floodlight_space.owner_review import apply_owner_review
from floodlight_space.whatsapp_adapter import normalize_baileys_envelope, normalize_phone


ROOT = Path(__file__).resolve().parent
FRONTEND_ROOT = ROOT / "frontend"
ASSETS_ROOT = FRONTEND_ROOT / "assets"
CONVERSATION_STORE = InMemoryConversationStore()


def build_server() -> Server:
    app = Server(
        title="Floodlight Venue Ops Agent",
        description="A custom Floodlight venue-ops UI served by a Gradio Server.",
        docs_url=None,
        redoc_url=None,
    )

    app.mount("/frontend", StaticFiles(directory=FRONTEND_ROOT), name="frontend")
    app.mount("/assets", StaticFiles(directory=ASSETS_ROOT), name="assets")

    @app.get("/")
    async def homepage() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "index.html")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "app": "floodlight-venue-ops-agent",
            "frontend": "fully-custom-ui",
            "version": "v2-active-demo",
            "model_runtime": "modal",
            "model_id": get_modal_status()["model_id"],
        }

    @app.get("/api/model-status")
    async def model_status_endpoint() -> JSONResponse:
        return JSONResponse(get_modal_status())

    @app.get("/api/bootstrap")
    async def bootstrap(scenario: str = "normal") -> JSONResponse:
        return JSONResponse(build_bootstrap(scenario))

    @app.post("/api/reload-demo")
    async def reload_demo() -> JSONResponse:
        CONVERSATION_STORE.reset()
        data = build_bootstrap("normal")
        data["demo_reset"] = {
            "state": "reloaded",
            "source": data.get("state_snapshot", {}).get("snapshot_id", "state_snapshot.v1"),
            "temporary_sessions_cleared": True,
        }
        return JSONResponse(data)

    @app.post("/api/decision")
    async def decision(payload: dict[str, Any] = Body(default_factory=dict)) -> JSONResponse:
        scenario = str(payload.get("scenario") or "normal")
        data = build_bootstrap(scenario)
        action = str(payload.get("action") or "approve")
        if action == "reject":
            data["decision"]["state"] = "rejected"
            data["trace"].append({"id": "rejected", "label": "Owner rejected the reply", "tone": "error", "timestamp_label": "now"})
        elif action == "clarify":
            data["decision"]["state"] = "ready"
            data["trace"].append({"id": "clarify", "label": "Owner asked for clarification", "tone": "warning", "timestamp_label": "now"})
        else:
            data["decision"]["state"] = "sent"
            data["trace"].append({"id": "sent", "label": "Reply marked sent via simulator", "tone": "success", "timestamp_label": "now"})
        return JSONResponse(data)

    @app.post("/api/extract-booking")
    async def extract_booking(payload: dict[str, Any] = Body(default_factory=dict)) -> JSONResponse:
        scenario = str(payload.get("scenario") or "normal")
        message = str(payload.get("message") or SAMPLE_USER_MESSAGE)
        trace_id = str(payload.get("trace_id") or "space-venue-sample-001")
        context = build_bootstrap(scenario)
        result = await run_in_threadpool(
            call_booking_extractor,
            message=message,
            venue_context=_model_context(context),
            trace_id=trace_id,
        )
        return JSONResponse(result, status_code=200 if result.get("ok") else 502)

    @app.post("/api/player-message")
    async def player_message(payload: dict[str, Any] = Body(default_factory=dict)) -> JSONResponse:
        trace_id = str(payload.get("trace_id") or "space-venue-flow-sample-001")
        return JSONResponse(
            {
                "ok": False,
                "trace_id": trace_id,
                "error": "endpoint_retired",
                "replacement": "/api/whatsapp/simulated-message",
                "message": "The legacy /api/player-message spike endpoint is retired. Use the deterministic conversation API.",
            },
            status_code=410,
        )

    @app.post("/api/booking-decision")
    async def booking_decision(payload: dict[str, Any] = Body(default_factory=dict)) -> JSONResponse:
        flow = payload.get("flow") if isinstance(payload.get("flow"), dict) else {}
        decision = str(payload.get("decision") or "approve")
        return JSONResponse(approve_booking_flow(flow, decision=decision))

    @app.post("/api/whatsapp/simulated-message")
    async def whatsapp_simulated_message(payload: dict[str, Any] = Body(default_factory=dict)) -> JSONResponse:
        scenario = str(payload.get("scenario") or "normal")
        context = _model_context(build_bootstrap(scenario))
        session = process_simulated_message(
            payload=payload,
            venue_context=context,
            store=CONVERSATION_STORE,
        )
        return JSONResponse({"ok": session["terminal_state"] != "failed_model", "conversation": session})

    @app.post("/api/whatsapp/simulated-model-message")
    async def whatsapp_simulated_model_message(payload: dict[str, Any] = Body(default_factory=dict)) -> JSONResponse:
        scenario = str(payload.get("scenario") or "normal")
        context = _model_context(build_bootstrap(scenario))
        session = await run_in_threadpool(
            process_simulated_model_message,
            payload=payload,
            venue_context=context,
            store=CONVERSATION_STORE,
            extraction_provider=call_booking_extractor,
        )
        ok = session["terminal_state"] != "failed_model"
        return JSONResponse(
            {
                "ok": ok,
                "conversation": session,
                "proof_boundary": {
                    "adapter": "simulator",
                    "extraction_mode": "modal",
                    "live_whatsapp_inbound_proven": False,
                    "live_outbound_proven": False,
                },
            },
            status_code=200 if ok else 502,
        )

    @app.post("/api/whatsapp/baileys-message")
    async def whatsapp_baileys_message(
        payload: dict[str, Any] = Body(default_factory=dict),
        adapter_token: str | None = Header(default=None, alias="X-Floodlight-Adapter-Token"),
    ) -> JSONResponse:
        if not _adapter_token_valid(adapter_token):
            return JSONResponse({"ok": False, "error": "adapter_token_missing_or_invalid", "conversation": None}, status_code=401)

        try:
            envelope = normalize_baileys_envelope(payload)
        except ValueError as exc:
            return JSONResponse({"ok": False, "error": str(exc), "conversation": None}, status_code=400)

        if not _sender_allowed(envelope.get("sender_phone")):
            return JSONResponse({"ok": False, "error": "sender_not_allowed", "conversation": None}, status_code=403)

        scenario = str(payload.get("scenario") or "normal")
        context = _model_context(build_bootstrap(scenario))
        mode = _live_adapter_mode()
        try:
            if mode == "modal":
                session = await run_in_threadpool(
                    process_baileys_message,
                    payload=payload,
                    venue_context=context,
                    store=CONVERSATION_STORE,
                    extraction_mode=mode,
                    extraction_provider=call_booking_extractor,
                )
            else:
                session = process_baileys_message(
                    payload=payload,
                    venue_context=context,
                    store=CONVERSATION_STORE,
                    extraction_mode=mode,
                    extraction_provider=call_booking_extractor,
                )
        except ValueError as exc:
            return JSONResponse({"ok": False, "error": str(exc), "conversation": None}, status_code=400)

        ok = session["terminal_state"] != "failed_model"
        status_code = 200
        if not ok and mode == "modal":
            status_code = 502
        return JSONResponse(
            {
                "ok": ok,
                "conversation": session,
                "proof_boundary": {
                    "adapter": "baileys",
                    "extraction_mode": mode,
                    "live_whatsapp_inbound_proven": False,
                    "live_outbound_proven": False,
                },
            },
            status_code=status_code,
        )

    @app.post("/api/conversations/{session_id}/owner-review")
    async def conversation_owner_review(session_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> JSONResponse:
        session = CONVERSATION_STORE.get_mutable(session_id)
        if session is None:
            return JSONResponse({"ok": False, "error": "conversation_not_found", "session_id": session_id}, status_code=404)
        scenario = str(payload.get("scenario") or "normal")
        context = _model_context(build_bootstrap(scenario))
        reviewed = apply_owner_review(session=session, payload=payload, venue_context=context)
        saved = CONVERSATION_STORE.save(reviewed)
        return JSONResponse({"ok": True, "conversation": saved})

    @app.get("/api/conversations/{session_id}")
    async def conversation_get(session_id: str) -> JSONResponse:
        session = CONVERSATION_STORE.get(session_id)
        if session is None:
            return JSONResponse({"ok": False, "error": "conversation_not_found", "session_id": session_id}, status_code=404)
        return JSONResponse({"ok": True, "conversation": session})

    @app.get("/api/conversations/{session_id}/trace")
    async def conversation_trace(session_id: str) -> JSONResponse:
        session = CONVERSATION_STORE.get(session_id)
        if session is None:
            return JSONResponse({"ok": False, "error": "conversation_not_found", "session_id": session_id}, status_code=404)
        trace = {
            "session_id": session_id,
            "trace_id": session.get("trace_id"),
            "raw_message": ((session.get("turns") or [{}])[-1].get("raw_message", "")),
            "inbound_turns": session.get("turns", []),
            "adapter_envelope": (session.get("turns") or [{}])[-1].get("adapter_envelope", {}),
            "model_extraction": session.get("model_extraction"),
            "model_validation": session.get("model_validation"),
            "truth_check_initial": session.get("truth_check_initial"),
            "owner_review_action": session.get("owner_review_action"),
            "owner_correction_diff": session.get("owner_correction_diff"),
            "approved_extraction": session.get("approved_extraction"),
            "truth_check_final": session.get("truth_check_final"),
            "backend_action": session.get("status"),
            "outbound_message": session.get("outbound_message"),
            "send_adapter": session.get("send_adapter"),
            "terminal_state": session.get("terminal_state"),
            "runtime_axes": _conversation_runtime_axes(session),
            "failure_reason": _failure_reason(session),
            "agent_trace": session.get("agent_trace", []),
        }
        return JSONResponse({"ok": True, "trace": trace})

    @app.api(
        name="get-floodlight-fixture",
        description="Return the static Floodlight venue-ops fixture with explicit proof boundaries.",
        queue=False,
        api_visibility="public",
    )
    def get_floodlight_fixture(scenario: str = "normal") -> dict[str, Any]:
        return build_bootstrap(scenario)

    @app.api(
        name="extract-venue-booking-sample",
        description="Send one booking message to the Modal Nemotron Cascade extractor and return schema-checked JSON.",
        queue=False,
        api_visibility="public",
    )
    def extract_venue_booking_sample(message: str = SAMPLE_USER_MESSAGE) -> dict[str, Any]:
        context = build_bootstrap("normal")
        return call_booking_extractor(
            message=message,
            venue_context=_model_context(context),
            trace_id="gradio-api-venue-sample-001",
        )

    return app


def _model_context(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "slots": context["slots"],
        "venues": context["venues"],
        "bookings": context.get("bookings", []),
        "registered_teams": context.get("registered_teams", []),
        "players": context.get("players", []),
        "decision": context["decision"],
    }


def _runtime_axes(extraction: dict[str, Any]) -> dict[str, Any]:
    return {
        "lifecycle_stage": "testing",
        "app_host": "hf_space" if os.environ.get("SPACE_ID") else "local",
        "model_runtime": "modal",
        "model_backend": extraction.get("backend", "modal_http"),
        "inference_engine": extraction.get("inference_engine", "unknown"),
        "model_artifact_format": extraction.get("model_artifact_format", "unknown"),
        "quantization": extraction.get("quantization", "unknown"),
        "model_id": extraction.get("model_id", get_modal_status()["model_id"]),
        "fallback_used": extraction.get("fallback_used", False),
    }


def _conversation_runtime_axes(session: dict[str, Any]) -> dict[str, Any]:
    extraction = session.get("model_extraction") if isinstance(session.get("model_extraction"), dict) else {}
    is_modal = extraction.get("backend") == "modal_http"
    return {
        "lifecycle_stage": "testing",
        "app_host": "hf_space" if os.environ.get("SPACE_ID") else "local",
        "model_runtime": "modal" if is_modal else "fixture_model_shaped_input",
        "model_backend": extraction.get("backend", "fixture_extractor"),
        "model_id": extraction.get("model_id", get_modal_status()["model_id"] if is_modal else "fixture-model-shaped-json"),
        "fallback_used": extraction.get("fallback_used", False),
        "send_adapter": "simulator",
        "live_whatsapp_inbound": False,
        "live_whatsapp_outbound": False,
    }


def _failure_reason(session: dict[str, Any]) -> str | None:
    if session.get("terminal_state") == "failed_model":
        extraction = session.get("model_extraction") if isinstance(session.get("model_extraction"), dict) else {}
        return str(extraction.get("blocker") or "failed_model")
    send_adapter = session.get("send_adapter") if isinstance(session.get("send_adapter"), dict) else {}
    if send_adapter.get("delivery_state") == "not_sent" and send_adapter.get("reason"):
        return str(send_adapter.get("reason"))
    return None


def _adapter_token_valid(adapter_token: str | None) -> bool:
    expected = os.environ.get("FLOODLIGHT_ADAPTER_TOKEN", "")
    return bool(expected) and adapter_token == expected


def _sender_allowed(sender_phone: Any) -> bool:
    allowed = {
        normalize_phone(item)
        for item in os.environ.get("FLOODLIGHT_ALLOWED_PHONES", "").split(",")
        if normalize_phone(item)
    }
    if not allowed:
        return True
    return normalize_phone(sender_phone) in allowed


def _live_adapter_mode() -> str:
    mode = os.environ.get("FLOODLIGHT_LIVE_ADAPTER_MODE", "fixture_dry_run")
    if mode not in {"fixture_dry_run", "modal"}:
        return "fixture_dry_run"
    return mode


app = build_server()


if __name__ == "__main__":
    app.launch(
        server_name=os.environ.get("HOST", "0.0.0.0"),
        server_port=int(os.environ.get("PORT", "7860")),
        footer_links=[],
        show_error=True,
    )
