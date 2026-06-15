"""Modal endpoint for Venue Manager Agent booking extraction.

The endpoint loads Nemotron Cascade 2 on Modal and returns schema-checked JSON.
It intentionally has no deterministic extraction fallback: when the model or
JSON validation fails, the response records the blocker and leaves `booking`
empty.
"""

from __future__ import annotations

import json
import os
import re
import time
from inspect import signature
from typing import Any

import modal
from fastapi import Header, HTTPException


APP_NAME = "venue-manager-agent-cascade"
AUTH_SECRET_NAME = "hf-build-small-modal-auth"
HF_SECRET_NAME = "hf-build-small-hf-token-2"
CACHE_VOLUME_NAME = "venue-manager-cascade-cache"
MODEL_ID = "nvidia/Nemotron-Cascade-2-30B-A3B"

GPU_CONFIG = os.environ.get("VENUE_MODAL_GPU", "H100:2")
TENSOR_PARALLEL_SIZE = int(os.environ.get("VENUE_CASCADE_TENSOR_PARALLEL", "2"))
MAX_MODEL_LEN = int(os.environ.get("VENUE_CASCADE_MAX_MODEL_LEN", "4096"))
MAX_TOKENS = int(os.environ.get("VENUE_CASCADE_MAX_TOKENS", "1200"))
FUNCTION_TIMEOUT = int(os.environ.get("VENUE_MODAL_FUNCTION_TIMEOUT", "1800"))
STARTUP_TIMEOUT = int(os.environ.get("VENUE_MODAL_STARTUP_TIMEOUT", str(FUNCTION_TIMEOUT)))
MIN_CONTAINERS = int(os.environ.get("VENUE_MODAL_MIN_CONTAINERS", "0"))
BUFFER_CONTAINERS = int(os.environ.get("VENUE_MODAL_BUFFER_CONTAINERS", "0"))
SCALEDOWN_WINDOW = int(
    os.environ.get("VENUE_MODAL_SCALEDOWN_WINDOW", "900" if MIN_CONTAINERS else "60")
)

app = modal.App(APP_NAME)
cache_volume = modal.Volume.from_name(CACHE_VOLUME_NAME, create_if_missing=True)

image = (
    modal.Image.from_registry(
        "vllm/vllm-openai:latest",
        setup_dockerfile_commands=[
            "RUN if ! command -v python >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then ln -s $(command -v python3) /usr/local/bin/python; fi",
            "ENTRYPOINT []",
        ],
    )
    .uv_pip_install("fastapi[standard]==0.115.4")
    .env(
        {
            "HF_HOME": "/cache/huggingface",
            "HF_HUB_ENABLE_HF_TRANSFER": "1",
            "HF_XET_HIGH_PERFORMANCE": "1",
            "VLLM_WORKER_MULTIPROC_METHOD": "spawn",
        }
    )
)

_LLM: Any | None = None


BOOKING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "intent",
        "customer",
        "sport",
        "date_text",
        "time_window",
        "venue_preference",
        "surface_preference",
        "players",
        "budget",
        "booking_status",
        "missing_fields",
        "confidence",
        "owner_next_action",
        "reply_draft",
    ],
    "properties": {
        "intent": {"type": "string"},
        "customer": {
            "type": "object",
            "required": ["name", "phone"],
            "properties": {
                "name": {"type": ["string", "null"]},
                "phone": {"type": ["string", "null"]},
            },
        },
        "sport": {"type": ["string", "null"]},
        "date_text": {"type": ["string", "null"]},
        "time_window": {"type": ["string", "null"]},
        "venue_preference": {"type": ["string", "null"]},
        "surface_preference": {"type": ["string", "null"]},
        "players": {"type": ["integer", "null"]},
        "budget": {
            "type": "object",
            "required": ["amount", "currency"],
            "properties": {
                "amount": {"type": ["integer", "null"]},
                "currency": {"type": "string"},
            },
        },
        "booking_status": {"type": "string"},
        "missing_fields": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
        "owner_next_action": {"type": "string"},
        "reply_draft": {"type": "string"},
    },
}

SAMPLE_MESSAGE = (
    "Hi, this is Aman Sharma. Need a cricket ground tomorrow morning "
    "8 AM to 12 PM for 12 players. Natural grass preferred, North Field if "
    "available. Budget is around Rs 6000. My number is +91 98765 43210."
)


def _duration_ms(started: float) -> int:
    return round((time.time() - started) * 1000)


def _mark_timing(timing: dict[str, int], name: str, started: float) -> None:
    timing[name] = _duration_ms(started)


def _load_llm() -> Any:
    global _LLM
    if _LLM is not None:
        return _LLM

    from vllm import LLM

    _LLM = LLM(
        model=MODEL_ID,
        trust_remote_code=True,
        tensor_parallel_size=TENSOR_PARALLEL_SIZE,
        max_model_len=MAX_MODEL_LEN,
        gpu_memory_utilization=float(os.environ.get("VENUE_CASCADE_GPU_MEMORY_UTILIZATION", "0.92")),
        dtype=os.environ.get("VENUE_CASCADE_DTYPE", "bfloat16"),
    )
    return _LLM


def _check_authorization(authorization: str | None) -> None:
    expected = os.environ.get("APP_MODAL_AUTH_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=500, detail="APP_MODAL_AUTH_TOKEN is not set")
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized")


def _prompt(payload: dict[str, Any]) -> str:
    message = str(payload.get("message") or SAMPLE_MESSAGE)
    venue_context = payload.get("venue_context") or {}
    schema_json = json.dumps(BOOKING_SCHEMA, ensure_ascii=True)
    return (
        "You are a JSON extraction endpoint for Venue Manager Agent.\n"
        "Return ONLY one valid JSON object. The first character must be { and the last character must be }.\n"
        "Do not write reasoning, analysis, markdown, code fences, comments, labels, or extra text.\n"
        "Do not include inline examples or additional JSON objects before or after the answer.\n"
        "Do not invent details. Use null for unknown scalar values and list unknown details in missing_fields.\n"
        "The JSON object must use double-quoted property names and exactly these top-level keys:\n"
        "- intent: one of book_slot, ask_availability, change_booking, cancel_booking, unknown\n"
        "- customer: {name, phone}\n"
        "- sport\n"
        "- date_text\n"
        "- time_window\n"
        "- venue_preference\n"
        "- surface_preference\n"
        "- players\n"
        "- budget: {amount, currency}\n"
        "- booking_status: one of ready_for_owner_review, needs_clarification, conflict_possible, unknown\n"
        "- missing_fields: array of strings\n"
        "- confidence: number from 0 to 1\n"
        "- owner_next_action: short instruction for the venue owner\n"
        "- reply_draft: concise WhatsApp-style reply to the customer\n\n"
        f"JSON schema:\n{schema_json}\n\n"
        f"Venue inventory context JSON:\n{json.dumps(venue_context, ensure_ascii=True)[:6000]}\n\n"
        f"User message:\n{message}\n\n"
        "Return the JSON object now:"
    )


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    return stripped


def _iter_balanced_objects(text: str) -> list[str]:
    candidates: list[str] = []
    stripped = _strip_code_fence(text)
    for start, char in enumerate(stripped):
        if char != "{":
            continue
        depth = 0
        in_string = False
        escaped = False
        for index, current in enumerate(stripped[start:], start=start):
            if in_string:
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == '"':
                    in_string = False
                continue
            if current == '"':
                in_string = True
            elif current == "{":
                depth += 1
            elif current == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(stripped[start : index + 1])
                    break
    return candidates


def _looks_like_booking_object(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    present_keys = set(value.keys())
    required_keys = set(BOOKING_SCHEMA["required"])
    schema_key_count = len(present_keys & required_keys)
    return schema_key_count >= 4 and ("intent" in value or "booking_status" in value)


def _extract_json_object(text: str) -> str:
    stripped = _strip_code_fence(text)
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            parsed = json.loads(stripped)
            if _looks_like_booking_object(parsed):
                return stripped
        except json.JSONDecodeError:
            pass
    for candidate in _iter_balanced_objects(stripped):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if _looks_like_booking_object(parsed):
            return candidate
    raise ValueError("model_output_did_not_contain_valid_booking_json_object")


def _validate_booking(value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["top_level_not_object"]
    for key in BOOKING_SCHEMA["required"]:
        if key not in value:
            errors.append(f"missing_key:{key}")
    customer = value.get("customer")
    if not isinstance(customer, dict):
        errors.append("customer_not_object")
    else:
        for key in ("name", "phone"):
            if key not in customer:
                errors.append(f"missing_customer_key:{key}")
    budget = value.get("budget")
    if not isinstance(budget, dict):
        errors.append("budget_not_object")
    else:
        for key in ("amount", "currency"):
            if key not in budget:
                errors.append(f"missing_budget_key:{key}")
    if not isinstance(value.get("missing_fields"), list):
        errors.append("missing_fields_not_array")
    confidence = value.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        errors.append("confidence_not_0_to_1")
    return errors


def _runtime_config() -> dict[str, Any]:
    return {
        "warm_pool": {
            "min_containers": MIN_CONTAINERS,
            "buffer_containers": BUFFER_CONTAINERS,
            "scaledown_window_seconds": SCALEDOWN_WINDOW,
        },
        "timeout_seconds": FUNCTION_TIMEOUT,
        "startup_timeout_seconds": STARTUP_TIMEOUT,
    }


def _run_model(payload: dict[str, Any]) -> dict[str, Any]:
    from vllm import SamplingParams

    started = time.time()
    timing_ms: dict[str, int] = {}
    _mark_timing(timing_ms, "request_received", started)
    raw_text = ""

    try:
        _mark_timing(timing_ms, "load_llm_start", started)
        llm = _load_llm()
        _mark_timing(timing_ms, "load_llm_end", started)
        _mark_timing(timing_ms, "prompt_build_start", started)
        prompt = _prompt(payload)
        sampling = _sampling_params(SamplingParams)
        _mark_timing(timing_ms, "prompt_build_end", started)
        _mark_timing(timing_ms, "generation_start", started)
        output = llm.generate([prompt], sampling)[0]
        _mark_timing(timing_ms, "generation_end", started)
        raw_text = output.outputs[0].text.strip()
        _mark_timing(timing_ms, "parse_validation_start", started)
        parsed = json.loads(_extract_json_object(raw_text))
        validation_errors = _validate_booking(parsed)
        _mark_timing(timing_ms, "parse_validation_end", started)
    except Exception as exc:
        parsed = None
        _mark_timing(timing_ms, "blocked_at", started)
        validation_errors = [f"modal_or_json_error:{type(exc).__name__}:{str(exc)[:240]}"]

    return {
        "ok": parsed is not None and not validation_errors,
        "trace_id": payload.get("trace_id"),
        "model_id": MODEL_ID,
        "model_family": "Nemotron Cascade 2 30B-A3B",
        "backend": "modal_http",
        "inference_engine": "vllm",
        "model_artifact_format": "safetensors",
        "quantization": "bf16",
        "gpu": GPU_CONFIG,
        "tensor_parallel_size": TENSOR_PARALLEL_SIZE,
        "runtime_config": _runtime_config(),
        "fallback_used": False,
        "latency_ms": _duration_ms(started),
        "timing_ms": timing_ms,
        "validation": {
            "valid": parsed is not None and not validation_errors,
            "errors": validation_errors,
        },
        "booking": parsed,
        "raw_text": raw_text[:4000],
        "blocker": "" if parsed is not None and not validation_errors else "model_output_failed_booking_json_validation",
    }


def _run_model_batch(payload: dict[str, Any]) -> dict[str, Any]:
    from vllm import SamplingParams

    started = time.time()
    timing_ms: dict[str, int] = {}
    _mark_timing(timing_ms, "request_received", started)
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        return {
            "ok": False,
            "model_id": MODEL_ID,
            "backend": "modal_http",
            "fallback_used": False,
            "results": [],
            "blocker": "batch_items_required",
            "validation": {"valid": False, "errors": ["batch_items_required"]},
        }
    if len(items) > 12:
        return {
            "ok": False,
            "model_id": MODEL_ID,
            "backend": "modal_http",
            "fallback_used": False,
            "results": [],
            "blocker": "batch_item_limit_exceeded",
            "validation": {"valid": False, "errors": ["batch_item_limit_exceeded"]},
        }

    try:
        _mark_timing(timing_ms, "load_llm_start", started)
        llm = _load_llm()
        _mark_timing(timing_ms, "load_llm_end", started)
        _mark_timing(timing_ms, "prompt_build_start", started)
        prompts = [_prompt(item if isinstance(item, dict) else {}) for item in items]
        sampling = _sampling_params(SamplingParams)
        _mark_timing(timing_ms, "prompt_build_end", started)
        _mark_timing(timing_ms, "generation_start", started)
        outputs = llm.generate(prompts, sampling)
        _mark_timing(timing_ms, "generation_end", started)
    except Exception as exc:
        _mark_timing(timing_ms, "blocked_at", started)
        return {
            "ok": False,
            "model_id": MODEL_ID,
            "model_family": "Nemotron Cascade 2 30B-A3B",
            "backend": "modal_http",
            "inference_engine": "vllm",
            "model_artifact_format": "safetensors",
            "quantization": "bf16",
            "gpu": GPU_CONFIG,
            "tensor_parallel_size": TENSOR_PARALLEL_SIZE,
            "runtime_config": _runtime_config(),
            "fallback_used": False,
            "latency_ms": _duration_ms(started),
            "timing_ms": timing_ms,
            "results": [],
            "validation": {"valid": False, "errors": ["modal_batch_exception"]},
            "blocker": f"{type(exc).__name__}: {str(exc)[:1000]}",
        }

    results: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        item_payload = item if isinstance(item, dict) else {}
        raw_text = outputs[index].outputs[0].text.strip() if index < len(outputs) else ""
        try:
            parsed = json.loads(_extract_json_object(raw_text))
            validation_errors = _validate_booking(parsed)
        except Exception as exc:
            parsed = None
            validation_errors = [f"modal_or_json_error:{type(exc).__name__}:{str(exc)[:240]}"]
        results.append(
            {
                "ok": parsed is not None and not validation_errors,
                "trace_id": item_payload.get("trace_id"),
                "case_id": item_payload.get("case_id"),
                "model_id": MODEL_ID,
                "model_family": "Nemotron Cascade 2 30B-A3B",
                "backend": "modal_http",
                "inference_engine": "vllm",
                "model_artifact_format": "safetensors",
                "quantization": "bf16",
                "gpu": GPU_CONFIG,
                "tensor_parallel_size": TENSOR_PARALLEL_SIZE,
                "runtime_config": _runtime_config(),
                "fallback_used": False,
                "latency_ms": _duration_ms(started),
                "timing_ms": timing_ms,
                "validation": {
                    "valid": parsed is not None and not validation_errors,
                    "errors": validation_errors,
                },
                "booking": parsed,
                "raw_text": raw_text[:4000],
                "blocker": "" if parsed is not None and not validation_errors else "model_output_failed_booking_json_validation",
            }
        )

    return {
        "ok": all(result.get("ok") for result in results),
        "model_id": MODEL_ID,
        "model_family": "Nemotron Cascade 2 30B-A3B",
        "backend": "modal_http",
        "inference_engine": "vllm",
        "model_artifact_format": "safetensors",
        "quantization": "bf16",
        "gpu": GPU_CONFIG,
        "tensor_parallel_size": TENSOR_PARALLEL_SIZE,
        "runtime_config": _runtime_config(),
        "fallback_used": False,
        "latency_ms": _duration_ms(started),
        "timing_ms": timing_ms,
        "results": results,
        "validation": {
            "valid": all(result.get("ok") for result in results),
            "errors": [result.get("blocker") for result in results if result.get("blocker")],
        },
        "blocker": "" if all(result.get("ok") for result in results) else "one_or_more_batch_items_failed",
    }


def _sampling_params(sampling_params_type: Any) -> Any:
    kwargs: dict[str, Any] = {
        "temperature": float(os.environ.get("VENUE_CASCADE_TEMPERATURE", "0")),
        "max_tokens": MAX_TOKENS,
        "stop": ["\n\nUser message:", "\n\nVenue inventory", "```"],
    }
    supported = set(signature(sampling_params_type).parameters)
    if "guided_json" in supported:
        kwargs["guided_json"] = BOOKING_SCHEMA
    elif "guided_decoding" in supported:
        guided = _guided_decoding_params()
        if guided is not None:
            kwargs["guided_decoding"] = guided
    elif "structured_outputs" in supported:
        structured = _structured_outputs_params()
        if structured is not None:
            kwargs["structured_outputs"] = structured
    return sampling_params_type(**kwargs)


def _guided_decoding_params() -> Any | None:
    try:
        from vllm.sampling_params import GuidedDecodingParams
    except Exception:
        return None
    return GuidedDecodingParams(json=BOOKING_SCHEMA)


def _structured_outputs_params() -> Any | None:
    try:
        from vllm.sampling_params import StructuredOutputsParams
    except Exception:
        return None
    return StructuredOutputsParams(json=BOOKING_SCHEMA)


@app.cls(
    image=image,
    env={
        "VENUE_MODAL_MIN_CONTAINERS": str(MIN_CONTAINERS),
        "VENUE_MODAL_BUFFER_CONTAINERS": str(BUFFER_CONTAINERS),
        "VENUE_MODAL_SCALEDOWN_WINDOW": str(SCALEDOWN_WINDOW),
    },
    gpu=GPU_CONFIG,
    timeout=FUNCTION_TIMEOUT,
    startup_timeout=STARTUP_TIMEOUT,
    min_containers=MIN_CONTAINERS or None,
    buffer_containers=BUFFER_CONTAINERS or None,
    scaledown_window=SCALEDOWN_WINDOW,
    volumes={"/cache": cache_volume},
    secrets=[
        modal.Secret.from_name(AUTH_SECRET_NAME),
        modal.Secret.from_name(HF_SECRET_NAME),
    ],
)
class VenueManagerCascade:
    @modal.enter()
    def preload(self) -> None:
        _load_llm()

    @modal.method()
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            if isinstance(payload.get("items"), list):
                return _run_model_batch(payload)
            return _run_model(payload)
        except Exception as exc:
            return {
                "ok": False,
                "trace_id": payload.get("trace_id"),
                "model_id": MODEL_ID,
                "model_family": "Nemotron Cascade 2 30B-A3B",
                "backend": "modal_http",
                "inference_engine": "vllm",
                "model_artifact_format": "safetensors",
                "quantization": "bf16",
                "gpu": GPU_CONFIG,
                "tensor_parallel_size": TENSOR_PARALLEL_SIZE,
                "runtime_config": _runtime_config(),
                "fallback_used": False,
                "latency_ms": 0,
                "timing_ms": {},
                "validation": {"valid": False, "errors": ["modal_model_exception"]},
                "booking": None,
                "raw_text": "",
                "blocker": f"{type(exc).__name__}: {str(exc)[:1000]}",
            }


@app.function(
    image=image,
    timeout=FUNCTION_TIMEOUT,
    secrets=[modal.Secret.from_name(AUTH_SECRET_NAME)],
)
@modal.fastapi_endpoint(method="POST", label="extract-booking")
def extract_booking(
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _check_authorization(authorization)
    return VenueManagerCascade().run.remote(payload)


@app.local_entrypoint()
def main(message: str = SAMPLE_MESSAGE) -> None:
    payload = {
        "trace_id": "modal-local-venue-sample-001",
        "message": message,
        "venue_context": {
            "venues": ["North Field", "South Field"],
            "slots": ["8 AM - 12 PM", "2 PM - 6 PM"],
        },
    }
    token = os.environ.get("APP_MODAL_AUTH_TOKEN", "local-entrypoint")
    result = extract_booking.remote(
        payload,
        authorization=f"Bearer {token}",
    )
    print(json.dumps(result, indent=2))
