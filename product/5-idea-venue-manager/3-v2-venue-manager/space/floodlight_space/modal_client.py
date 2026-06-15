from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from floodlight_space.extraction_adapter import validate_candidate_booking


SAMPLE_USER_MESSAGE = (
    "Hi, this is Aman Sharma. Need a cricket ground tomorrow morning "
    "8 AM to 12 PM for 12 players. Natural grass preferred, North Field if "
    "available. Budget is around Rs 6000. My number is +91 98765 43210."
)


def modal_status() -> dict[str, Any]:
    return {
        "configured": bool(os.environ.get("APP_MODAL_BASE_URL") and os.environ.get("APP_MODAL_AUTH_TOKEN")),
        "base_url_configured": bool(os.environ.get("APP_MODAL_BASE_URL")),
        "auth_configured": bool(os.environ.get("APP_MODAL_AUTH_TOKEN")),
        "model_id": os.environ.get("APP_MODAL_MODEL_ID", "nvidia/Nemotron-Cascade-2-30B-A3B"),
        "timeout_seconds": float(os.environ.get("APP_MODAL_TIMEOUT_SECONDS", "90")),
    }


def call_booking_extractor(
    *,
    message: str = SAMPLE_USER_MESSAGE,
    venue_context: dict[str, Any] | None = None,
    trace_id: str = "space-venue-sample-001",
) -> dict[str, Any]:
    status = modal_status()
    if not status["configured"]:
        return {
            "ok": False,
            "trace_id": trace_id,
            "model_id": status["model_id"],
            "backend": "modal_http",
            "fallback_used": False,
            "booking": None,
            "blocker": "APP_MODAL_BASE_URL and APP_MODAL_AUTH_TOKEN must be configured on the Space.",
            "validation": {"valid": False, "errors": ["modal_config_missing"]},
        }

    payload = json.dumps(
        {
            "trace_id": trace_id,
            "message": message,
            "venue_context": venue_context or {},
        }
    ).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['APP_MODAL_AUTH_TOKEN']}",
    }
    started = time.time()
    request = urllib.request.Request(
        os.environ["APP_MODAL_BASE_URL"],
        data=payload,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=status["timeout_seconds"]) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        return _blocked(trace_id, status["model_id"], f"Modal HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        return _blocked(trace_id, status["model_id"], f"Modal request failed: {exc}")
    except TimeoutError as exc:
        return _blocked(trace_id, status["model_id"], f"Modal request timed out: {exc}")
    except json.JSONDecodeError as exc:
        return _blocked(trace_id, status["model_id"], f"Modal returned non-JSON response: {exc}")

    result.setdefault("client_latency_ms", round((time.time() - started) * 1000))
    result.setdefault("fallback_used", False)
    result.setdefault("backend", "modal_http")
    result.setdefault("model_id", status["model_id"])
    if result.get("ok"):
        validation = validate_candidate_booking(result.get("booking") if isinstance(result.get("booking"), dict) else {})
        result["validation"] = validation
        if not validation["valid"]:
            return {
                "ok": False,
                "trace_id": result.get("trace_id", trace_id),
                "model_id": result.get("model_id", status["model_id"]),
                "backend": result.get("backend", "modal_http"),
                "inference_engine": result.get("inference_engine"),
                "model_artifact_format": result.get("model_artifact_format"),
                "quantization": result.get("quantization"),
                "fallback_used": result.get("fallback_used", False),
                "latency_ms": result.get("latency_ms"),
                "client_latency_ms": result.get("client_latency_ms"),
                "timing_ms": result.get("timing_ms", {}),
                "raw_text": result.get("raw_text", ""),
                "booking": None,
                "blocker": "Modal returned ok=true but booking schema was invalid.",
                "validation": validation,
            }
    return result


def _blocked(trace_id: str, model_id: str, blocker: str) -> dict[str, Any]:
    return {
        "ok": False,
        "trace_id": trace_id,
        "model_id": model_id,
        "backend": "modal_http",
        "fallback_used": False,
        "booking": None,
        "blocker": blocker,
        "validation": {"valid": False, "errors": ["modal_request_blocked"]},
    }
