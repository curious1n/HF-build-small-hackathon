#!/usr/bin/env python3
"""Voice Reach V1 Space app.

The default local mode is deterministic so package checks stay fast. On a
Hugging Face Space, set VCW_MODEL_MODE=real for the model-backed proof path.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import gradio as gr
from huggingface_hub import hf_hub_download
from pydantic import BaseModel


APP_VERSION = "v1-space-local-model-2026-06-15"
SPACE_DIR = Path(__file__).resolve().parent
V1_DIR = SPACE_DIR.parent if (SPACE_DIR.parent / "onboarding").exists() else SPACE_DIR
IDEA_DIR = V1_DIR.parent if V1_DIR != SPACE_DIR else SPACE_DIR
REPO_ROOT = V1_DIR.parents[2] if len(V1_DIR.parents) > 2 else V1_DIR


def load_local_env_files(paths: tuple[Path, ...]) -> list[str]:
    loaded: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().removeprefix("export ").strip()
            if key and key not in os.environ:
                os.environ[key] = value.strip().strip("'\"")
        loaded.append(str(path))
    return loaded


LOCAL_ENV_FILES = (
    IDEA_DIR / ".env.modal.local",
)
LOADED_LOCAL_ENV_FILES = load_local_env_files(LOCAL_ENV_FILES) if not os.environ.get("SPACE_ID") else []

PACKET_CANDIDATES = (
    V1_DIR / "onboarding" / "metime-to.json",
    SPACE_DIR / "onboarding" / "metime-to.json",
)
PACKET_PATH = next((path for path in PACKET_CANDIDATES if path.exists()), PACKET_CANDIDATES[0])
LEDGER_PATH = Path(os.environ.get("VCW_LEDGER_PATH", SPACE_DIR / "demo-ledger.jsonl"))
TRACE_PATH = Path(os.environ.get("VCW_TRACE_PATH", "/tmp/vcw-v1-traces.jsonl"))
STATIC_DIR = SPACE_DIR / "static"

ASR_MODEL_ID = "nvidia/nemotron-3.5-asr-streaming-0.6b"
ASR_MODEL_FILE = "nemotron-3.5-asr-streaming-0.6b.nemo"
TEXT_MODEL_ID = "CohereLabs/tiny-aya-fire-GGUF"
TEXT_MODEL_FILE = "tiny-aya-fire-q8_0.gguf"
TEXT_MODEL_LABEL = "CohereLabs/tiny-aya-fire-GGUF:Q8_0"
MODAL_ASR_MODEL_ID = ASR_MODEL_ID
MODAL_TEXT_MODEL_ID = TEXT_MODEL_ID
MODAL_TEXT_MODEL_LABEL = TEXT_MODEL_LABEL
DEFAULT_HF_PERSONAL_BASE_URL = "https://curieous-voice-reach.hf.space"
MAX_AUDIO_BYTES = int(os.environ.get("VCW_MAX_AUDIO_BYTES", str(16 * 1024 * 1024)))
MAX_AUDIO_SECONDS = int(os.environ.get("VCW_MAX_AUDIO_SECONDS", "45"))

SUPPORT_FIELD_CUES = {
    "order": {
        "message": ("order id", "order number", "order"),
        "source": ("order", "order id", "\u0911\u0930\u094d\u0921\u0930"),
    },
    "delivery": {
        "message": ("delivery status", "delivery address", "delivered", "delivery"),
        "source": ("delivery", "delivered", "\u0921\u093f\u0932\u093f\u0935\u0930\u0940"),
    },
    "address": {
        "message": ("delivery address", "address"),
        "source": ("address", "\u092a\u0924\u093e"),
    },
    "payment": {
        "message": ("payment", "paid", "transaction"),
        "source": ("payment", "paid", "transaction", "\u092d\u0941\u0917\u0924\u093e\u0928", "\u092a\u0947\u092e\u0947\u0902\u091f"),
    },
    "refund": {
        "message": ("refund", "refunded"),
        "source": ("refund", "refunded", "\u0930\u093f\u092b\u0902\u0921"),
    },
    "phone": {
        "message": ("phone number", "mobile number", "call me at", "contact me at"),
        "source": ("phone number", "mobile number", "\u092b\u094b\u0928", "\u092e\u094b\u092c\u093e\u0907\u0932"),
    },
    "email": {
        "message": ("email address", "email id"),
        "source": ("email address", "email id", "email", "\u0908\u092e\u0947\u0932"),
    },
    "account": {
        "message": ("account id", "account number", "account"),
        "source": ("account", "\u0905\u0915\u093e\u0909\u0902\u091f"),
    },
    "booking": {
        "message": ("booking id", "booking number", "booking", "book ", "appointment"),
        "source": ("booking", "book ", "appointment", "\u092c\u0941\u0915\u093f\u0902\u0917"),
    },
}

PRESERVATION_CUES = {
    "antique": {
        "source": ("antique", "\u090f\u0902\u091f\u0940\u0915"),
        "message": ("antique",),
    },
    "pricing": {
        "source": ("pricing", "price", "\u092a\u094d\u0930\u093e\u0907\u0938"),
        "message": ("pricing", "price"),
    },
    "availability": {
        "source": ("availability", "available"),
        "message": ("availability", "available"),
    },
}

REQUIRED_PACKET_FIELDS = {
    "schema_version",
    "site_id",
    "brand_name",
    "contact_email",
    "locale_defaults",
    "audio_eval_consent",
    "audio_eval_notice",
    "retention",
    "design_tokens",
    "copy",
}

REQUIRED_TOKEN_FIELDS = {
    "font_family",
    "color_background",
    "color_surface",
    "color_surface_subtle",
    "color_text",
    "color_text_muted",
    "color_primary",
    "color_primary_hover",
    "color_accent",
    "color_accent_soft",
    "color_border",
    "color_danger",
    "shadow_soft",
    "radius_container",
    "radius_control",
    "radius_button",
}

RUN_LEDGER: list[dict[str, Any]] = []
PIPELINE_LOCK = threading.Lock()
PROCESS_LOCK = threading.Lock()
PIPELINE: "ModelPipeline | None" = None
TEXT_ADAPTER_LOCK = threading.Lock()
TEXT_ADAPTER: "TinyAyaAdapter | None" = None


class PacketError(ValueError):
    """Raised when the onboarding packet does not match the V1 contract."""


class SendPayload(BaseModel):
    site_id: str
    contact_email: str
    model_message_en: str
    final_message_en: str
    trace_id: str
    simulate: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def detect_app_host() -> str:
    return "hf_space" if os.environ.get("SPACE_ID") or os.environ.get("SPACE_HOST") else "local"


def lifecycle_stage() -> str:
    return "staging" if detect_app_host() == "hf_space" else "testing"


def model_mode() -> str:
    forced = os.environ.get("VCW_MODEL_MODE", "").strip().lower()
    if forced in {"real", "deterministic"}:
        return forced
    if os.environ.get("VCW_FORCE_DETERMINISTIC", "").strip().lower() in {"1", "true", "yes"}:
        return "deterministic"
    return "real" if detect_app_host() == "hf_space" else "deterministic"


def runtime_switch_allowed() -> bool:
    return os.environ.get("VCW_ALLOW_RUNTIME_SWITCH", "").strip().lower() in {"1", "true", "yes", "on"}


def selected_model_runtime(override: Any = None) -> str:
    requested = str(override or "").strip().lower()
    aliases = {
        "hf_hackathon_space": "hf_space",
        "hf_personal": "hf_personal_space",
        "deterministic": "none",
    }
    requested = aliases.get(requested, requested)
    if requested:
        if requested == "hf_space":
            return "hf_space"
        if requested in {"hf_personal_space", "modal"} and runtime_switch_allowed():
            return requested
        if requested in {"hf_personal_space", "modal"}:
            raise HTTPException(status_code=403, detail="Model runtime switch is disabled")
        raise HTTPException(status_code=400, detail="Unsupported model runtime")

    runtime = os.environ.get("VCW_MODEL_RUNTIME", "").strip().lower()
    runtime = aliases.get(runtime, runtime)
    if runtime in {"modal", "hf_personal_space", "hf_space", "none"}:
        return runtime
    if model_mode() == "deterministic":
        return "none"
    return "hf_space"


def runtime_axes(runtime: str) -> dict[str, Any]:
    if runtime == "modal":
        return {
            "model_backend": "modal_http",
            "inference_engine": "nemo+llama.cpp",
            "model_artifact_format": "nemo_archive+gguf",
            "quantization": "unquantized+q8_0",
            "asr_model_id": os.environ.get("APP_MODAL_ASR_MODEL_ID", MODAL_ASR_MODEL_ID),
            "text_model_id": os.environ.get("APP_MODAL_MODEL_ID", MODAL_TEXT_MODEL_LABEL),
            "fallback_used": False,
        }
    if runtime == "hf_personal_space":
        return {
            "model_backend": "hf_space_proxy",
            "inference_engine": "remote_space_api",
            "model_artifact_format": "remote_space",
            "quantization": "remote",
            "asr_model_id": ASR_MODEL_ID,
            "text_model_id": TEXT_MODEL_LABEL,
            "fallback_used": False,
        }
    if runtime == "hf_space":
        return {
            "model_backend": "nemo+llama.cpp",
            "inference_engine": "nemo+llama.cpp",
            "model_artifact_format": "nemo_archive+gguf",
            "quantization": "unknown+q8_0",
            "asr_model_id": ASR_MODEL_ID,
            "text_model_id": TEXT_MODEL_LABEL,
            "fallback_used": False,
        }
    return {
        "model_backend": "template",
        "inference_engine": "none",
        "model_artifact_format": "none",
        "quantization": "none",
        "asr_model_id": ASR_MODEL_ID,
        "text_model_id": TEXT_MODEL_LABEL,
        "fallback_used": True,
    }


def runtime_availability(runtime: str) -> dict[str, Any]:
    if runtime == "none":
        return {"available": True, "reason": None}
    if runtime == "hf_space":
        if model_mode() == "deterministic":
            return {
                "available": False,
                "reason": "HF hackathon space is not available in local deterministic mode. Set VCW_MODEL_MODE=real on model-backed hardware.",
            }
        return {"available": True, "reason": None}
    if runtime == "hf_personal_space":
        if not runtime_switch_allowed():
            return {"available": False, "reason": "Runtime switching is disabled for this Space."}
        if not hf_personal_base_url():
            return {"available": False, "reason": "HF personal space URL is not configured."}
        return {"available": True, "reason": None}
    if runtime == "modal":
        if not runtime_switch_allowed():
            return {"available": False, "reason": "Runtime switching is disabled for this Space."}
        if not modal_base_url():
            return {"available": False, "reason": "Modal endpoint is not configured."}
        if not modal_auth_token():
            return {"available": False, "reason": "Modal auth token is not configured."}
        return {"available": True, "reason": None}
    return {"available": False, "reason": "Unsupported model runtime."}


def runtime_controls(default_runtime: str) -> dict[str, Any]:
    allow_switch = runtime_switch_allowed()
    selected = default_runtime if default_runtime in {"hf_space", "hf_personal_space", "modal"} else "hf_space"
    hf_space_availability = runtime_availability("hf_space")
    hf_personal_availability = runtime_availability("hf_personal_space")
    modal_availability = runtime_availability("modal")
    return {
        "label": "Model Runtime",
        "allow_switch": allow_switch,
        "selected": selected,
        "options": [
            {
                "value": "hf_space",
                "label": "HF hackathon space",
                "note": "credit issue",
                "enabled": True,
                "available": hf_space_availability["available"],
                "disabled_reason": hf_space_availability["reason"],
            },
            {
                "value": "hf_personal_space",
                "label": "HF personal space",
                "note": "test runtime",
                "enabled": allow_switch,
                "available": allow_switch and hf_personal_availability["available"],
                "disabled_reason": hf_personal_availability["reason"] if allow_switch else "Enable VCW_ALLOW_RUNTIME_SWITCH=1 to test this runtime.",
            },
            {
                "value": "modal",
                "label": "Modal",
                "note": "warm GPU" if modal_availability["available"] else "test runtime",
                "enabled": allow_switch,
                "available": allow_switch and modal_availability["available"],
                "disabled_reason": modal_availability["reason"] if allow_switch else "Enable VCW_ALLOW_RUNTIME_SWITCH=1 to test this runtime.",
            },
        ],
    }


def hf_token() -> str | None:
    token = (
        os.environ.get("HF_TOKEN")
        or os.environ.get("HF_TOKEN_2")
        or os.environ.get("HF_TOKEN_1")
        or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    )
    if token and not os.environ.get("HF_TOKEN"):
        os.environ["HF_TOKEN"] = token
    return token


def load_packet() -> dict[str, Any]:
    packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    validate_packet(packet)
    return packet


def validate_packet(packet: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_PACKET_FIELDS - packet.keys())
    if missing:
        raise PacketError(f"Packet missing required fields: {', '.join(missing)}")

    defaults = packet.get("locale_defaults", {})
    modes = defaults.get("speech_modes")
    if modes != ["hindi", "hinglish"]:
        raise PacketError("Packet speech modes must be exactly ['hindi', 'hinglish']")
    if defaults.get("default_speech_mode") not in modes:
        raise PacketError("Packet default speech mode must be one of the speech modes")
    if defaults.get("target_output_language") != "en":
        raise PacketError("Packet target output language must be 'en'")
    if packet.get("site_id") != "metime-to":
        raise PacketError("V1 expects site_id='metime-to'")
    if packet.get("contact_email") != "founders@metime.to":
        raise PacketError("V1 expects contact_email='founders@metime.to'")

    tokens = packet.get("design_tokens", {})
    missing_tokens = sorted(REQUIRED_TOKEN_FIELDS - tokens.keys())
    if missing_tokens:
        raise PacketError(f"Packet missing design tokens: {', '.join(missing_tokens)}")

    copy = packet.get("copy", {})
    for key in ("heading", "subheading", "record_cta", "stop_cta", "send_cta", "success"):
        if not copy.get(key):
            raise PacketError(f"Packet copy missing '{key}'")


def asr_hint_for_mode(speech_mode: str) -> str:
    return "hi-IN" if speech_mode in {"hindi", "hinglish"} else "hi-IN"


def public_packet(packet: dict[str, Any]) -> dict[str, Any]:
    mode = model_mode()
    runtime = selected_model_runtime()
    axes = runtime_axes(runtime)
    return {
        **packet,
        "runtime_controls": runtime_controls(runtime),
        "provenance": {
            "packet_path": "product/5-idea-voice-contact-widget/v1/onboarding/metime-to.json",
            "app_version": APP_VERSION,
            "lifecycle_stage": lifecycle_stage(),
            "app_host": detect_app_host(),
            "model_runtime": runtime,
            "model_backend": axes["model_backend"],
            "inference_engine": axes["inference_engine"],
            "model_artifact_format": axes["model_artifact_format"],
            "quantization": axes["quantization"],
            "mock_mode": "deterministic" if mode == "deterministic" else "off",
            "fallback_used": axes["fallback_used"],
            "asr_model_id": axes["asr_model_id"],
            "text_model_id": axes["text_model_id"],
            "concurrency": 1,
        },
    }


def deterministic_transcript(speech_mode: str) -> str:
    if speech_mode == "hindi":
        return "Namaste, mujhe metime.to ke baare mein founders se baat karni hai. Kripya mujhe onboarding aur pricing details bhej dijiye."
    return "Hi, main metime.to ke baare mein founders se connect karna chahta hoon. Please onboarding aur pricing details share kar dijiye."


def deterministic_message(speech_mode: str, transcript: str) -> str:
    if speech_mode == "hindi":
        body = "I would like to connect with the founders to learn more about metime.to, including onboarding and pricing details."
    else:
        body = "I would like to connect with the founders and learn more about metime.to, especially onboarding and pricing details."
    return f"Hello metime.to team,\n\n{body}\n\nOriginal voice note summary: {transcript}\n\nThank you."


def deterministic_model_json(speech_mode: str, transcript: str) -> dict[str, Any]:
    return {
        "message_en": deterministic_message(speech_mode, transcript),
        "confidence": 0.72,
        "needs_edit": False,
        "notes": [],
        "guardrail_flags": [],
    }


def unsupported_support_fields(transcript: str, message: str) -> list[str]:
    transcript_lower = transcript.lower()
    message_lower = message.lower()
    unsupported: list[str] = []
    for field, cues in SUPPORT_FIELD_CUES.items():
        message_mentions = any(cue in message_lower for cue in cues["message"])
        if field == "phone" and re.search(r"\b\d{7,}\b", message_lower):
            message_mentions = True
        source_mentions = any(cue in transcript_lower for cue in cues["source"])
        if message_mentions and not source_mentions:
            unsupported.append(field)
    return unsupported


def missing_preservation_cues(transcript: str, message: str) -> list[str]:
    transcript_lower = transcript.lower()
    message_lower = message.lower()
    missing: list[str] = []
    for cue, patterns in PRESERVATION_CUES.items():
        source_mentions = any(pattern in transcript_lower for pattern in patterns["source"])
        message_mentions = any(pattern in message_lower for pattern in patterns["message"])
        if source_mentions and not message_mentions:
            missing.append(cue)
    return missing


def normalize_text_output(data: dict[str, Any], transcript: str) -> dict[str, Any]:
    message = str(data.get("message_en") or "").strip()
    if not message:
        raise ValueError("tiny_aya_empty_message")

    confidence_raw = data.get("confidence", 0.5)
    try:
        confidence = max(0.0, min(1.0, float(confidence_raw)))
    except (TypeError, ValueError):
        confidence = 0.5

    notes_raw = data.get("notes") or []
    if isinstance(notes_raw, str):
        notes = [notes_raw]
    else:
        notes = [str(note).strip() for note in list(notes_raw) if str(note).strip()]

    guardrail_flags = [str(flag).strip() for flag in list(data.get("guardrail_flags") or []) if str(flag).strip()]
    unsupported = unsupported_support_fields(transcript, message)
    if unsupported:
        guardrail_flags.append("unsupported_support_fields:" + ",".join(unsupported))
        notes.append("draft_mentions_support_fields_not_present_in_transcript")
    missing_cues = missing_preservation_cues(transcript, message)
    if missing_cues:
        guardrail_flags.append("missing_preservation_cues:" + ",".join(missing_cues))
        notes.append("draft_may_not_preserve_source_topic")

    needs_edit = bool(data.get("needs_edit"))
    if unsupported or missing_cues or confidence < 0.55:
        needs_edit = True

    return {
        "message_en": message,
        "confidence": confidence,
        "needs_edit": needs_edit,
        "notes": sorted(set(notes)),
        "guardrail_flags": sorted(set(guardrail_flags)),
    }


def tiny_aya_messages(packet: dict[str, Any], transcript: str, speech_mode: str, target_lang: str) -> list[dict[str, str]]:
    payload = {
        "site_id": packet["site_id"],
        "brand_name": packet["brand_name"],
        "asr_transcript": transcript,
        "speech_mode": speech_mode,
        "asr_language_hint": target_lang,
        "target_output_language": "en",
        "task": "Rewrite or translate only the user's transcript into a concise English contact-form message.",
        "output_schema": {
            "message_en": "English draft preserving only the transcript's meaning",
            "confidence": "number from 0.0 to 1.0",
            "needs_edit": "boolean",
            "notes": "short array of review notes; empty when clean",
        },
    }
    system = (
        "You are a literal Hindi/Hinglish to English rewriting assistant for a website contact widget. "
        "Preserve the user's meaning. Do not act as customer support. Do not invent facts, fields, "
        "names, phone numbers, emails, order IDs, payment status, delivery outcomes, addresses, links, "
        "bookings, or account details. If the transcript is unrelated, unclear, or not a request, "
        "write a faithful English version and set needs_edit=true. Return only strict JSON."
    )
    user = (
        "Create the JSON response for this input. Use only information present in asr_transcript.\n"
        f"{json.dumps(payload, ensure_ascii=True, sort_keys=True)}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def tiny_aya_raw_prompt(messages: list[dict[str, str]]) -> str:
    return (
        f"System:\n{messages[0]['content']}\n\n"
        f"User:\n{messages[1]['content']}\n\n"
        "JSON:"
    )


def append_trace(record: dict[str, Any]) -> None:
    redacted = json.loads(json.dumps(record, ensure_ascii=True))
    RUN_LEDGER.insert(0, redacted)
    del RUN_LEDGER[50:]
    try:
        TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with TRACE_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(redacted, ensure_ascii=True) + "\n")
    except OSError:
        pass


def build_trace_base(packet: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    retention = packet.get("retention", {})
    speech_mode = str(payload.get("speech_mode") or packet["locale_defaults"]["default_speech_mode"])
    return {
        "trace_id": f"vcw_{uuid.uuid4().hex[:12]}",
        "created_at": utc_now(),
        "site_id": packet["site_id"],
        "speech_mode": speech_mode,
        "asr_language_hint": asr_hint_for_mode(speech_mode),
        "audio_eval_consent": bool(packet["audio_eval_consent"]),
        "visitor_notice_shown": bool(payload.get("visitor_notice_shown")),
        "raw_audio_retained": bool(retention.get("retain_raw_audio_for_eval")),
        "retain_transcript_for_eval": bool(retention.get("retain_transcript_for_eval")),
        "retain_generated_message_for_eval": bool(retention.get("retain_generated_message_for_eval")),
        "asr_model_id": ASR_MODEL_ID,
        "text_model_id": TEXT_MODEL_LABEL,
        "lifecycle_stage": lifecycle_stage(),
        "app_host": detect_app_host(),
    }


def strip_data_url(value: str) -> str:
    if "," in value and value[:64].lower().startswith("data:"):
        return value.split(",", 1)[1]
    return value


def suffix_for_mime(mime: str) -> str:
    mime = (mime or "").split(";", 1)[0].strip().lower()
    return {
        "audio/wav": ".wav",
        "audio/wave": ".wav",
        "audio/x-wav": ".wav",
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/webm": ".webm",
        "audio/ogg": ".ogg",
        "audio/mp4": ".m4a",
    }.get(mime, ".wav")


def decode_audio_payload(payload: dict[str, Any]) -> tuple[Path | None, int]:
    audio_b64 = str(payload.get("audio_base64") or "").strip()
    if not audio_b64:
        return None, 0
    raw = base64.b64decode(strip_data_url(audio_b64), validate=False)
    if len(raw) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio payload too large")
    mime = str(payload.get("audio_mime") or "audio/wav")
    suffix = suffix_for_mime(mime)
    source = Path(tempfile.gettempdir()) / f"vcw-audio-{uuid.uuid4().hex}{suffix}"
    source.write_bytes(raw)
    if suffix == ".wav":
        return source, len(raw)
    wav_path = source.with_suffix(".wav")
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(wav_path),
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    except Exception as exc:
        raise RuntimeError(f"ffmpeg_audio_convert_failed:{type(exc).__name__}") from exc
    return wav_path, len(raw)


def extract_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list) and value:
        return extract_text(value[0])
    if isinstance(value, tuple) and value:
        return extract_text(value[0])
    if hasattr(value, "text"):
        return str(value.text).strip()
    return str(value).strip()


class NemoAsrAdapter:
    def __init__(self) -> None:
        started = time.time()
        hf_token()
        import torch
        import nemo.collections.asr as nemo_asr
        from nemo.collections.asr.parts.utils.streaming_utils import CacheAwareStreamingAudioBuffer

        self.torch = torch
        self.StreamingAudioBuffer = CacheAwareStreamingAudioBuffer
        self.model = nemo_asr.models.ASRModel.from_pretrained(model_name=ASR_MODEL_ID)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if hasattr(torch, "set_float32_matmul_precision"):
            torch.set_float32_matmul_precision("high")
        self.model = self.model.to(device=self.device, dtype=torch.float32)
        self.model.eval()
        self._configure_streaming_context()
        self.load_ms = round((time.time() - started) * 1000)

    def _configure_streaming_context(self) -> None:
        raw = os.environ.get("VCW_NEMO_ATT_CONTEXT_SIZE", "56,13")
        try:
            att_context_size = [int(part.strip()) for part in raw.replace("[", "").replace("]", "").split(",") if part.strip()]
        except ValueError:
            att_context_size = []
        if len(att_context_size) == 2 and hasattr(self.model.encoder, "set_default_att_context_size"):
            self.model.encoder.set_default_att_context_size(att_context_size=att_context_size)

    def transcribe(self, audio_path: Path, target_lang: str) -> tuple[str, int]:
        started = time.time()
        if hasattr(self.model, "set_inference_prompt"):
            self.model.set_inference_prompt(target_lang)
            decoding = getattr(self.model, "decoding", None)
            if decoding is not None and hasattr(decoding, "set_strip_lang_tags"):
                decoding.set_strip_lang_tags(True, lang_tag_pattern=r"<[a-z]{2,3}-[A-Z]{2}>")
        streaming_buffer = self.StreamingAudioBuffer(
            model=self.model,
            online_normalization=False,
            pad_and_drop_preencoded=False,
        )
        streaming_buffer.append_audio_file(str(audio_path), stream_id=-1)
        text = extract_text(self._perform_streaming(streaming_buffer))
        if not text:
            raise RuntimeError("nemo_streaming_returned_empty_transcript")
        return text, round((time.time() - started) * 1000)

    def _perform_streaming(self, streaming_buffer: Any) -> Any:
        batch_size = len(streaming_buffer.streams_length)
        cache_last_channel, cache_last_time, cache_last_channel_len = self.model.encoder.get_initial_cache_state(
            batch_size=batch_size
        )
        previous_hypotheses = None
        pred_out_stream = None
        transcribed_texts: Any = []
        with self.torch.inference_mode():
            for step_num, (chunk_audio, chunk_lengths) in enumerate(streaming_buffer):
                chunk_audio = chunk_audio.to(self.torch.float32)
                drop_extra = 0
                if step_num != 0:
                    drop_extra = self.model.encoder.streaming_cfg.drop_extra_pre_encoded
                (
                    pred_out_stream,
                    transcribed_texts,
                    cache_last_channel,
                    cache_last_time,
                    cache_last_channel_len,
                    previous_hypotheses,
                ) = self.model.conformer_stream_step(
                    processed_signal=chunk_audio,
                    processed_signal_length=chunk_lengths,
                    cache_last_channel=cache_last_channel,
                    cache_last_time=cache_last_time,
                    cache_last_channel_len=cache_last_channel_len,
                    keep_all_outputs=streaming_buffer.is_buffer_empty(),
                    previous_hypotheses=previous_hypotheses,
                    previous_pred_out=pred_out_stream,
                    drop_extra_pre_encoded=drop_extra,
                    return_transcription=True,
                )
        return transcribed_texts



class TinyAyaAdapter:
    def __init__(self) -> None:
        started = time.time()
        from llama_cpp import Llama

        model_path = hf_hub_download(
            repo_id=TEXT_MODEL_ID,
            filename=TEXT_MODEL_FILE,
            repo_type="model",
            token=hf_token(),
            cache_dir=os.environ.get("HF_HOME") or os.environ.get("HF_MODEL_CACHE_DIR"),
        )
        n_gpu_layers = int(os.environ.get("VCW_LLAMA_N_GPU_LAYERS", "0"))
        self.llm = Llama(
            model_path=model_path,
            n_ctx=int(os.environ.get("VCW_LLAMA_N_CTX", "2048")),
            n_threads=int(os.environ.get("VCW_LLAMA_THREADS", "4")),
            n_gpu_layers=n_gpu_layers,
            verbose=os.environ.get("VCW_LLAMA_VERBOSE", "0") in {"1", "true", "yes"},
        )
        self.load_ms = round((time.time() - started) * 1000)

    def generate(self, packet: dict[str, Any], transcript: str, speech_mode: str, target_lang: str) -> tuple[dict[str, Any], int, str]:
        started = time.time()
        messages = tiny_aya_messages(packet, transcript, speech_mode, target_lang)
        max_tokens = int(os.environ.get("VCW_LLAMA_MAX_TOKENS", "220"))
        temperature = float(os.environ.get("VCW_LLAMA_TEMPERATURE", "0.1"))
        top_p = float(os.environ.get("VCW_LLAMA_TOP_P", "0.95"))
        use_chat_completion = os.environ.get("VCW_TINY_AYA_CHAT_COMPLETION", "1").strip().lower() in {"1", "true", "yes"}
        raw = ""
        try:
            if not use_chat_completion:
                raise RuntimeError("chat_completion_disabled")
            result = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            raw = str(result["choices"][0]["message"]["content"]).strip()
        except Exception:
            result = self.llm(
                tiny_aya_raw_prompt(messages),
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=["\n\nUser:", "\n\nSystem:", "</s>"],
            )
            raw = str(result["choices"][0]["text"]).strip()
        try:
            parsed = parse_model_json(raw, transcript)
        except Exception as exc:
            raise ValueError(f"{exc}; raw_prefix={raw[:500]!r}") from exc
        return parsed, round((time.time() - started) * 1000), raw


def parse_model_json(raw: str, transcript: str = "") -> dict[str, Any]:
    text = raw.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("tiny_aya_output_not_json")
        data = json.loads(match.group(0))
    for wrapper_key in ("output", "response", "result"):
        if isinstance(data.get(wrapper_key), dict):
            data = data[wrapper_key]
            break
    if isinstance(data.get("output_schema"), dict):
        nested = data["output_schema"]
        required = {"message_en", "confidence", "needs_edit"}
        if required <= set(nested):
            data = nested
    if isinstance(data.get("message"), dict) and isinstance(data["message"].get("content"), str):
        return parse_model_json(data["message"]["content"], transcript)
    if isinstance(data.get("content"), str):
        return parse_model_json(data["content"], transcript)
    required = {"message_en", "confidence", "needs_edit"}
    missing = required - set(data)
    if missing:
        raise ValueError(f"tiny_aya_json_missing:{','.join(sorted(missing))}")
    return normalize_text_output(data, transcript)


class ModelPipeline:
    def __init__(self) -> None:
        self.asr = NemoAsrAdapter()
        self.text = TinyAyaAdapter()

    def run(self, packet: dict[str, Any], payload: dict[str, Any], audio_path: Path) -> dict[str, Any]:
        trace = build_trace_base(packet, payload)
        speech_mode = trace["speech_mode"]
        target_lang = trace["asr_language_hint"]
        total_started = time.time()
        transcript, asr_ms = self.asr.transcribe(audio_path, target_lang)
        if not transcript:
            raise RuntimeError("nemo_empty_transcript")
        text_json, text_ms, raw_text = self.text.generate(packet, transcript, speech_mode, target_lang)
        trace.update(
            {
                "model_runtime": "hf_space",
                "model_backend": "nemo+llama.cpp",
                "inference_engine": "nemo+llama.cpp",
                "model_artifact_format": "nemo_archive+gguf",
                "quantization": "unknown+q8_0",
                "model_id": f"{ASR_MODEL_ID}+{TEXT_MODEL_LABEL}",
                "fallback_used": False,
                "fallback_reason": None,
                "timings_ms": {
                    "asr_load": self.asr.load_ms,
                    "text_load": self.text.load_ms,
                    "asr": asr_ms,
                    "text": text_ms,
                    "total": round((time.time() - total_started) * 1000),
                },
                "asr": {
                    "model_id": ASR_MODEL_ID,
                    "backend": "nemo",
                    "inference_engine": "nemo",
                    "model_artifact_format": "nemo_archive",
                    "quantization": "unknown",
                    "target_lang": target_lang,
                    "fallback_used": False,
                    "transcript": transcript,
                },
                "text": {
                    "model_id": TEXT_MODEL_LABEL,
                    "backend": "llama.cpp",
                    "inference_engine": "llama.cpp",
                    "model_artifact_format": "gguf",
                    "quantization": "q8_0",
                    "fallback_used": False,
                    "raw_output": raw_text[:2000],
                    "output": text_json,
                },
            }
        )
        return {
            "transcript": transcript,
            "model_message_en": text_json["message_en"],
            "text": text_json,
            "trace": trace,
        }


def get_pipeline() -> ModelPipeline:
    global PIPELINE
    if PIPELINE is None:
        with PIPELINE_LOCK:
            if PIPELINE is None:
                PIPELINE = ModelPipeline()
    return PIPELINE


def get_text_adapter() -> TinyAyaAdapter:
    global TEXT_ADAPTER
    if PIPELINE is not None:
        return PIPELINE.text
    if TEXT_ADAPTER is None:
        with TEXT_ADAPTER_LOCK:
            if TEXT_ADAPTER is None:
                TEXT_ADAPTER = TinyAyaAdapter()
    return TEXT_ADAPTER


def modal_timeout_seconds() -> float:
    return float(os.environ.get("APP_MODAL_TIMEOUT_SECONDS", "180"))


def modal_base_url() -> str:
    return os.environ.get("APP_MODAL_BASE_URL", "").strip().rstrip("/")


def modal_auth_token() -> str:
    return os.environ.get("APP_MODAL_AUTH_TOKEN", "").strip()


def modal_payload(packet: dict[str, Any], payload: dict[str, Any], trace: dict[str, Any], *, transcript: str = "") -> dict[str, Any]:
    audio_b64 = str(payload.get("audio_base64") or "").strip()
    return {
        "trace_id": trace["trace_id"],
        "site_id": packet["site_id"],
        "speech_mode": trace["speech_mode"],
        "language_hint": trace["asr_language_hint"],
        "asr_model_id": os.environ.get("APP_MODAL_ASR_MODEL_ID", MODAL_ASR_MODEL_ID),
        "text_model_id": os.environ.get("APP_MODAL_MODEL_ID", MODAL_TEXT_MODEL_ID),
        "transcript": transcript,
        "audio": {
            "size_bytes": int(payload.get("audio_size_bytes") or 0),
            "duration_ms": int(payload.get("duration_ms") or payload.get("audio_duration_ms") or 0),
            "content_type": str(payload.get("audio_mime") or "audio/wav"),
            "b64": strip_data_url(audio_b64),
        },
    }


def call_modal(payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
    base_url = modal_base_url()
    token = modal_auth_token()
    if not base_url:
        raise RuntimeError("APP_MODAL_BASE_URL is not set")
    if not token:
        raise RuntimeError("APP_MODAL_AUTH_TOKEN is not set")
    started = time.time()
    request = urllib.request.Request(
        base_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=modal_timeout_seconds()) as response:
            body = response.read().decode("utf-8", errors="replace")
            parsed = json.loads(body)
            if not isinstance(parsed, dict):
                raise RuntimeError("modal_response_not_json_object")
            return parsed, round((time.time() - started) * 1000)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"modal_http_{exc.code}:{body}") from exc


def hf_personal_base_url() -> str:
    return os.environ.get("APP_HF_PERSONAL_BASE_URL", DEFAULT_HF_PERSONAL_BASE_URL).strip().rstrip("/")


def hf_personal_auth_token() -> str:
    return (
        os.environ.get("APP_HF_PERSONAL_TOKEN", "").strip()
        or os.environ.get("HF_TOKEN_2", "").strip()
        or os.environ.get("HF_TOKEN", "").strip()
    )


def call_hf_personal(path: str, payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
    base_url = hf_personal_base_url()
    if not base_url:
        raise RuntimeError("APP_HF_PERSONAL_BASE_URL is not set")
    token = hf_personal_auth_token()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    proxied_payload = dict(payload)
    proxied_payload.pop("model_runtime", None)
    started = time.time()
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=json.dumps(proxied_payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=modal_timeout_seconds()) as response:
            body = response.read().decode("utf-8", errors="replace")
            parsed = json.loads(body)
            if not isinstance(parsed, dict):
                raise RuntimeError("hf_personal_response_not_json_object")
            return parsed, round((time.time() - started) * 1000)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"hf_personal_http_{exc.code}:{body}") from exc


def hf_personal_result_to_response(
    local_trace: dict[str, Any],
    result: dict[str, Any],
    latency_ms: int,
    *,
    text_only: bool,
) -> dict[str, Any]:
    remote_trace = result.get("trace") if isinstance(result.get("trace"), dict) else {}
    transcript = str(result.get("transcript") or remote_trace.get("transcript") or "").strip()
    text_json = result.get("text") if isinstance(result.get("text"), dict) else {}
    if not text_json:
        text_json = ((remote_trace.get("text") or {}).get("output") or {}) if isinstance(remote_trace.get("text"), dict) else {}
    text_json = normalize_text_output(text_json, transcript)
    local_trace.update(
        {
            "text_only_smoke": text_only,
            "model_runtime": "hf_personal_space",
            "model_backend": "hf_space_proxy",
            "inference_engine": "remote_space_api",
            "model_artifact_format": "remote_space",
            "quantization": "remote",
            "model_id": f"{hf_personal_base_url()}:{'text-smoke' if text_only else 'process'}",
            "fallback_used": bool(remote_trace.get("fallback_used")),
            "fallback_reason": remote_trace.get("fallback_reason"),
            "blocker": remote_trace.get("blocker"),
            "timings_ms": {
                "hf_personal_http": latency_ms,
                "remote_total": (remote_trace.get("timings_ms") or {}).get("total"),
            },
            "remote_trace_id": remote_trace.get("trace_id"),
            "asr": remote_trace.get("asr")
            or {
                "model_id": "supplied-transcript" if text_only else ASR_MODEL_ID,
                "backend": "hf_space_proxy",
                "inference_engine": "remote_space_api",
                "model_artifact_format": "remote_space",
                "quantization": "remote",
                "target_lang": local_trace["asr_language_hint"],
                "fallback_used": False,
                "transcript": transcript,
            },
            "text": remote_trace.get("text")
            or {
                "model_id": TEXT_MODEL_LABEL,
                "backend": "hf_space_proxy",
                "inference_engine": "remote_space_api",
                "model_artifact_format": "remote_space",
                "quantization": "remote",
                "fallback_used": bool(remote_trace.get("fallback_used")),
                "output": text_json,
            },
        }
    )
    return {
        "transcript": transcript,
        "model_message_en": text_json["message_en"],
        "text": text_json,
        "trace": local_trace,
    }


def modal_result_to_response(
    packet: dict[str, Any],
    payload: dict[str, Any],
    trace: dict[str, Any],
    modal_result: dict[str, Any],
    modal_ms: int,
    *,
    text_only: bool,
) -> dict[str, Any]:
    asr = modal_result.get("asr") if isinstance(modal_result.get("asr"), dict) else {}
    text = modal_result.get("text") if isinstance(modal_result.get("text"), dict) else {}
    raw_output = str(text.get("raw_output") or "")
    transcript = str(modal_result.get("transcript") or (asr.get("output") or {}).get("transcript") or "").strip()
    text_output = text.get("output") if isinstance(text.get("output"), dict) else {}
    text_json = normalize_text_output(text_output, transcript)
    fallback_used = bool(modal_result.get("fallback_used")) or bool(asr.get("fallback_used")) or bool(text.get("fallback_used"))
    trace.update(
        {
            "text_only_smoke": text_only,
            "model_runtime": "modal",
            "model_backend": "modal_http",
            "inference_engine": modal_result.get("inference_engine") or "nemo+llama.cpp",
            "model_artifact_format": modal_result.get("model_artifact_format") or "nemo_archive+gguf",
            "quantization": modal_result.get("quantization") or "unquantized+q8_0",
            "model_id": modal_result.get("model_id") or f"{MODAL_ASR_MODEL_ID}+{MODAL_TEXT_MODEL_LABEL}",
            "fallback_used": fallback_used,
            "fallback_reason": modal_result.get("fallback_reason"),
            "blocker": modal_result.get("error"),
            "timings_ms": {
                "modal_http": modal_ms,
                "modal_total": modal_result.get("latency_ms"),
                "asr": asr.get("latency_ms"),
                "text": text.get("latency_ms"),
            },
            "asr": {
                "model_id": asr.get("model_id") or ("supplied-transcript" if text_only else MODAL_ASR_MODEL_ID),
                "backend": asr.get("backend") or ("none" if text_only else "modal_http"),
                "inference_engine": asr.get("inference_engine") or ("none" if text_only else "nemo"),
                "model_artifact_format": asr.get("model_artifact_format") or ("none" if text_only else "nemo_archive"),
                "quantization": asr.get("quantization") or ("none" if text_only else "unquantized"),
                "target_lang": trace["asr_language_hint"],
                "fallback_used": bool(asr.get("fallback_used")),
                "transcript": transcript,
            },
            "text": {
                "model_id": text.get("model_id") or MODAL_TEXT_MODEL_LABEL,
                "backend": text.get("backend") or "modal_http",
                "inference_engine": text.get("inference_engine") or "llama.cpp",
                "model_artifact_format": text.get("model_artifact_format") or "gguf",
                "quantization": text.get("quantization") or "q8_0",
                "fallback_used": bool(text.get("fallback_used")),
                "raw_output": raw_output[:2000],
                "output": text_json,
            },
        }
    )
    if fallback_used:
        trace["fallback_reason"] = trace["fallback_reason"] or "modal_partial_or_failed"
    return {
        "transcript": transcript,
        "model_message_en": text_json["message_en"],
        "text": text_json,
        "trace": trace,
    }


def deterministic_process(packet: dict[str, Any], payload: dict[str, Any], reason: str) -> dict[str, Any]:
    trace = build_trace_base(packet, payload)
    speech_mode = trace["speech_mode"]
    transcript = str(payload.get("transcript") or deterministic_transcript(speech_mode)).strip()
    text_json = deterministic_model_json(speech_mode, transcript)
    trace.update(
        {
            "model_runtime": "none",
            "model_backend": "template",
            "inference_engine": "none",
            "model_artifact_format": "none",
            "quantization": "none",
            "model_id": "deterministic-v1-template",
            "mock_mode": "deterministic",
            "fallback_used": True,
            "fallback_reason": reason,
            "timings_ms": {"prepare": 10, "mock_asr": 1, "mock_text": 1, "total": 12},
            "asr": {
                "model_id": ASR_MODEL_ID,
                "backend": "template",
                "inference_engine": "none",
                "model_artifact_format": "none",
                "quantization": "none",
                "target_lang": trace["asr_language_hint"],
                "fallback_used": True,
                "transcript": transcript,
            },
            "text": {
                "model_id": TEXT_MODEL_LABEL,
                "backend": "template",
                "inference_engine": "none",
                "model_artifact_format": "none",
                "quantization": "none",
                "fallback_used": True,
                "output": text_json,
            },
        }
    )
    return {"transcript": transcript, "model_message_en": text_json["message_en"], "text": text_json, "trace": trace}


def runtime_unavailable_response(packet: dict[str, Any], payload: dict[str, Any], runtime: str, *, text_only: bool) -> JSONResponse:
    availability = runtime_availability(runtime)
    reason = availability["reason"] or "Selected model runtime is not available."
    trace = build_trace_base(packet, payload)
    axes = runtime_axes(runtime)
    trace.update(
        {
            "text_only_smoke": text_only,
            "model_runtime": runtime,
            "model_backend": axes["model_backend"],
            "inference_engine": axes["inference_engine"],
            "model_artifact_format": axes["model_artifact_format"],
            "quantization": axes["quantization"],
            "model_id": f"{axes['asr_model_id']}+{axes['text_model_id']}",
            "fallback_used": False,
            "fallback_reason": None,
            "blocker": reason,
            "timings_ms": {"total": 0},
        }
    )
    append_trace(trace)
    return JSONResponse(
        {
            "error": "Selected model runtime is not available; deterministic output was not substituted.",
            "blocker": reason,
            "trace": trace,
        },
        status_code=424,
    )


app = FastAPI(title="Voice Reach V1", version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(SPACE_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, Any]:
    mode = model_mode()
    runtime = selected_model_runtime()
    axes = runtime_axes(runtime)
    availability = runtime_availability(runtime)
    return {
        "ok": True,
        "app": "voice-reach-v1",
        "version": APP_VERSION,
        "lifecycle_stage": lifecycle_stage(),
        "app_host": detect_app_host(),
        "model_runtime": runtime,
        "model_backend": axes["model_backend"],
        "inference_engine": axes["inference_engine"],
        "model_artifact_format": axes["model_artifact_format"],
        "quantization": axes["quantization"],
        "model_mode": mode,
        "runtime_available": availability["available"],
        "runtime_unavailable_reason": availability["reason"],
        "fallback_used": axes["fallback_used"],
        "asr_model_id": axes["asr_model_id"],
        "text_model_id": axes["text_model_id"],
        "modal_configured": bool(modal_base_url()) if runtime == "modal" else None,
        "hf_personal_configured": bool(hf_personal_base_url()) if runtime == "hf_personal_space" else None,
        "runtime_switch_allowed": runtime_switch_allowed(),
        "local_env_files_loaded": [Path(path).name for path in LOADED_LOCAL_ENV_FILES],
        "concurrency": 1,
        "gradio_status_path": "/gradio",
        "trace_path": str(TRACE_PATH),
    }


@app.get("/api/packet")
def api_packet() -> dict[str, Any]:
    return public_packet(load_packet())


@app.get("/api/traces")
def api_traces() -> dict[str, Any]:
    return {"items": RUN_LEDGER[:20]}


@app.post("/api/process")
async def api_process(request: Request) -> JSONResponse:
    packet = load_packet()
    payload = await request.json()
    speech_mode = payload.get("speech_mode", packet["locale_defaults"]["default_speech_mode"])
    if speech_mode not in {"hindi", "hinglish"}:
        raise HTTPException(status_code=400, detail="Unsupported speech mode")
    runtime = selected_model_runtime(payload.get("model_runtime"))
    duration_ms = int(payload.get("duration_ms") or payload.get("audio_duration_ms") or 0)
    if duration_ms > MAX_AUDIO_SECONDS * 1000:
        raise HTTPException(status_code=400, detail=f"Audio exceeds {MAX_AUDIO_SECONDS} second V1 smoke limit")

    if payload.get("simulate") == "asr_failure":
        raise HTTPException(status_code=422, detail="ASR failed in deterministic test mode")
    if payload.get("simulate") == "text_failure":
        raise HTTPException(status_code=424, detail="Text generation failed in deterministic test mode")

    with PROCESS_LOCK:
        if model_mode() == "deterministic" and runtime == "none":
            result = deterministic_process(packet, payload, "deterministic_mode")
            append_trace(result["trace"])
            return JSONResponse(result)
        if not runtime_availability(runtime)["available"]:
            return runtime_unavailable_response(packet, payload, runtime, text_only=False)

        try:
            if runtime == "modal":
                trace = build_trace_base(packet, payload)
                modal_result, modal_ms = call_modal(modal_payload(packet, payload, trace))
                result = modal_result_to_response(packet, payload, trace, modal_result, modal_ms, text_only=False)
                result["trace"]["audio_size_bytes"] = int(payload.get("audio_size_bytes") or 0)
                result["trace"]["audio_duration_ms"] = duration_ms
            elif runtime == "hf_personal_space":
                trace = build_trace_base(packet, payload)
                remote_result, remote_ms = call_hf_personal("/api/process", payload)
                result = hf_personal_result_to_response(trace, remote_result, remote_ms, text_only=False)
                result["trace"]["audio_size_bytes"] = int(payload.get("audio_size_bytes") or 0)
                result["trace"]["audio_duration_ms"] = duration_ms
            elif runtime == "hf_space":
                audio_path, audio_size = decode_audio_payload(payload)
                if audio_path is None or audio_size <= 0:
                    raise ValueError("real_model_mode_requires_audio_base64")
                result = get_pipeline().run(packet, payload, audio_path)
                result["trace"]["audio_size_bytes"] = audio_size
                result["trace"]["audio_duration_ms"] = duration_ms
            else:
                return runtime_unavailable_response(packet, payload, runtime, text_only=False)
            append_trace(result["trace"])
            return JSONResponse(result)
        except Exception as exc:
            trace = build_trace_base(packet, payload)
            axes = runtime_axes(runtime)
            trace.update(
                {
                    "model_runtime": runtime,
                    "model_backend": axes["model_backend"],
                    "inference_engine": axes["inference_engine"],
                    "model_artifact_format": axes["model_artifact_format"],
                    "quantization": axes["quantization"],
                    "model_id": f"{axes['asr_model_id']}+{axes['text_model_id']}",
                    "fallback_used": True,
                    "fallback_reason": f"real_model_error:{type(exc).__name__}",
                    "blocker": str(exc),
                    "timings_ms": {},
                }
            )
            append_trace(trace)
            return JSONResponse(
                {
                    "error": "Real model path failed; deterministic output was not substituted.",
                    "blocker": str(exc),
                    "trace": trace,
                },
                status_code=424,
            )


@app.post("/api/text-smoke")
async def api_text_smoke(request: Request) -> JSONResponse:
    packet = load_packet()
    payload = await request.json()
    speech_mode = payload.get("speech_mode", packet["locale_defaults"]["default_speech_mode"])
    if speech_mode not in {"hindi", "hinglish"}:
        raise HTTPException(status_code=400, detail="Unsupported speech mode")
    runtime = selected_model_runtime(payload.get("model_runtime"))

    transcript = str(payload.get("transcript") or "").strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="transcript is required")

    trace = build_trace_base(packet, payload)
    target_lang = trace["asr_language_hint"]
    if model_mode() == "deterministic" and runtime == "none":
        text_json = deterministic_model_json(speech_mode, transcript)
        trace.update(
            {
                "text_only_smoke": True,
                "model_runtime": "none",
                "model_backend": "template",
                "inference_engine": "none",
                "model_artifact_format": "none",
                "quantization": "none",
                "model_id": "deterministic-v1-template",
                "fallback_used": True,
                "fallback_reason": "deterministic_mode",
                "timings_ms": {"mock_text": 1, "total": 1},
                "asr": {
                    "model_id": "supplied-transcript",
                    "backend": "none",
                    "inference_engine": "none",
                    "model_artifact_format": "none",
                    "quantization": "none",
                    "target_lang": target_lang,
                    "fallback_used": False,
                    "transcript": transcript,
                },
                "text": {
                    "model_id": TEXT_MODEL_LABEL,
                    "backend": "template",
                    "inference_engine": "none",
                    "model_artifact_format": "none",
                    "quantization": "none",
                    "fallback_used": True,
                    "output": text_json,
                },
            }
        )
        append_trace(trace)
        return JSONResponse({"transcript": transcript, "model_message_en": text_json["message_en"], "text": text_json, "trace": trace})
    if not runtime_availability(runtime)["available"]:
        return runtime_unavailable_response(packet, payload, runtime, text_only=True)

    started = time.time()
    try:
        if runtime == "modal":
            modal_result, modal_ms = call_modal(modal_payload(packet, payload, trace, transcript=transcript))
            result = modal_result_to_response(packet, payload, trace, modal_result, modal_ms, text_only=True)
            append_trace(result["trace"])
            return JSONResponse(result)
        if runtime == "hf_personal_space":
            remote_result, remote_ms = call_hf_personal("/api/text-smoke", payload)
            result = hf_personal_result_to_response(trace, remote_result, remote_ms, text_only=True)
            append_trace(result["trace"])
            return JSONResponse(result)
        text_json, text_ms, raw_text = get_text_adapter().generate(packet, transcript, speech_mode, target_lang)
        trace.update(
            {
                "text_only_smoke": True,
                "model_runtime": "hf_space",
                "model_backend": "llama.cpp",
                "inference_engine": "llama.cpp",
                "model_artifact_format": "gguf",
                "quantization": "q8_0",
                "model_id": TEXT_MODEL_LABEL,
                "fallback_used": False,
                "fallback_reason": None,
                "timings_ms": {
                    "text_load": get_text_adapter().load_ms,
                    "text": text_ms,
                    "total": round((time.time() - started) * 1000),
                },
                "asr": {
                    "model_id": "supplied-transcript",
                    "backend": "none",
                    "inference_engine": "none",
                    "model_artifact_format": "none",
                    "quantization": "none",
                    "target_lang": target_lang,
                    "fallback_used": False,
                    "transcript": transcript,
                },
                "text": {
                    "model_id": TEXT_MODEL_LABEL,
                    "backend": "llama.cpp",
                    "inference_engine": "llama.cpp",
                    "model_artifact_format": "gguf",
                    "quantization": "q8_0",
                    "fallback_used": False,
                    "raw_output": raw_text[:2000],
                    "output": text_json,
                },
            }
        )
        append_trace(trace)
        return JSONResponse({"transcript": transcript, "model_message_en": text_json["message_en"], "text": text_json, "trace": trace})
    except Exception as exc:
        axes = runtime_axes(runtime)
        trace.update(
            {
                "text_only_smoke": True,
                "model_runtime": runtime,
                "model_backend": axes["model_backend"],
                "inference_engine": axes["inference_engine"],
                "model_artifact_format": axes["model_artifact_format"],
                "quantization": axes["quantization"],
                "model_id": axes["text_model_id"],
                "fallback_used": True,
                "fallback_reason": f"real_text_model_error:{type(exc).__name__}",
                "blocker": str(exc),
                "timings_ms": {"total": round((time.time() - started) * 1000)},
            }
        )
        append_trace(trace)
        return JSONResponse(
            {
                "error": "Real text model path failed; deterministic output was not substituted.",
                "blocker": str(exc),
                "trace": trace,
            },
            status_code=424,
        )


@app.post("/api/send")
def api_send(payload: SendPayload) -> dict[str, Any]:
    if payload.simulate == "send_failure":
        raise HTTPException(status_code=502, detail="Send failed in deterministic test mode")
    final_message = payload.final_message_en.strip()
    model_message = payload.model_message_en.strip()
    if not final_message or not payload.trace_id:
        raise HTTPException(status_code=400, detail="final_message_en and trace_id are required")
    record = {
        "created_at": utc_now(),
        "site_id": payload.site_id,
        "contact_email": payload.contact_email,
        "model_message_en": model_message,
        "final_message_en": final_message,
        "user_edited": final_message != model_message,
        "trace_id": payload.trace_id,
        "delivery": "demo_ledger",
        "email_sent": False,
        "email_provider": "ledger",
        "fallback_used": selected_model_runtime() == "none",
        "model_runtime": selected_model_runtime(),
    }
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as ledger:
        ledger.write(json.dumps(record, sort_keys=True) + "\n")
    return {
        "status": "saved",
        "visitor_copy": "Message saved for the demo.",
        "ledger_path": "product/5-idea-voice-contact-widget/v1/space/demo-ledger.jsonl",
        "email_sent": False,
        "email_provider": "ledger",
        "fallback_used": record["fallback_used"],
        "model_runtime": record["model_runtime"],
    }


def gradio_status() -> dict[str, Any]:
    return {"health": health(), "packet": public_packet(load_packet())["provenance"], "recent_traces": RUN_LEDGER[:5]}


def build_gradio_demo() -> gr.Blocks:
    with gr.Blocks(title="Voice Reach V1") as demo:
        gr.Markdown(
            """
            # Voice Reach V1

            The custom visitor widget is served at `/`. This status panel exists
            to keep the HF Space visibly Gradio-backed and to expose runtime
            provenance for smoke evidence.
            """
        )
        status = gr.JSON(value=gradio_status(), label="Runtime status")
        refresh = gr.Button("Refresh status", variant="primary")
        refresh.click(fn=gradio_status, inputs=None, outputs=status, concurrency_limit=1)
    return demo.queue(default_concurrency_limit=1)


gradio_demo = build_gradio_demo()
app = gr.mount_gradio_app(app, gradio_demo, path="/gradio")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Voice Reach V1 Space app.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=int(os.environ.get("PORT", "7860")), type=int)
    parser.add_argument("--check", action="store_true", help="Validate packet and exit without loading models.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    packet = load_packet()
    if args.check:
        print(
            json.dumps(
                {
                    "ok": True,
                    "site_id": packet["site_id"],
                    "brand_name": packet["brand_name"],
                    "contact_email": packet["contact_email"],
                    "speech_modes": packet["locale_defaults"]["speech_modes"],
                    "audio_eval_consent": packet["audio_eval_consent"],
                    "app_host": detect_app_host(),
                    "model_mode": model_mode(),
                    "model_runtime": selected_model_runtime(),
                    "runtime_switch_allowed": runtime_switch_allowed(),
                    "fallback_used": selected_model_runtime() == "none",
                    "concurrency": 1,
                },
                indent=2,
            )
        )
        return 0
    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
