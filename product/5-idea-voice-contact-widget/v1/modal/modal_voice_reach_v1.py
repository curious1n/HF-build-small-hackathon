"""Modal sidecar for Voice Reach V1.

This endpoint keeps the HF Space on CPU Basic while running the model path on
Modal. It intentionally uses the proven optimized ONNX ASR + GGUF text runtime
shape from V0, while preserving the V1 response contract at the Space layer.
"""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import time
from typing import Any

import modal
from fastapi import Header, HTTPException


APP_NAME = "voice-reach-v1-modal"
AUTH_SECRET_NAME = "hf-build-small-modal-auth"
HF_SECRET_NAME = "voice-reach-v1-hf"
CACHE_VOLUME_NAME = "voice-reach-v1-model-cache"

DEFAULT_ASR_MODEL_ID = "onnx-community/nemotron-3.5-asr-streaming-0.6b-onnx-int4"
TINY_AYA_TEXT_MODEL_ID = "CohereLabs/tiny-aya-fire-GGUF"

TEXT_MODEL_ARTIFACTS = {
    TINY_AYA_TEXT_MODEL_ID: {
        "filename": "tiny-aya-fire-q4_k_m.gguf",
        "label": "CohereLabs/tiny-aya-fire-GGUF:Q4_K_M",
        "inference_engine": "llama.cpp",
        "model_artifact_format": "gguf",
        "quantization": "q4_k_m",
    }
}

app = modal.App(APP_NAME)
cache_volume = modal.Volume.from_name(CACHE_VOLUME_NAME, create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("build-essential", "cmake", "ffmpeg")
    .uv_pip_install(
        "fastapi[standard]==0.115.4",
        "huggingface_hub[hf_transfer]>=0.36,<1",
        "llama-cpp-python>=0.3.16,<0.4",
        "numpy>=2.0,<3",
        "onnxruntime-genai>=0.14,<0.15",
    )
    .env(
        {
            "HF_HOME": "/cache/huggingface",
            "HF_HUB_ENABLE_HF_TRANSFER": "1",
        }
    )
)

_LLM: Any | None = None
_LLM_MODEL_ID: str | None = None
_ASR_MODEL: Any | None = None
_ASR_TOKENIZER: Any | None = None
_ASR_MODEL_PATH: str | None = None

ASR_LANG_TO_ID = {
    "auto": 101,
    "hi": 6,
    "hi-IN": 6,
    "en": 0,
    "en-US": 0,
}


def _duration_ms(started: float) -> int:
    return round((time.time() - started) * 1000)


def _download_asr_model(model_id: str) -> str:
    from huggingface_hub import snapshot_download

    return snapshot_download(
        repo_id=model_id,
        cache_dir="/cache/huggingface",
        allow_patterns=[
            "audio_processor_config.json",
            "decoder.onnx",
            "decoder.onnx.data",
            "encoder.onnx",
            "encoder.onnx.data",
            "genai_config.json",
            "joint.onnx",
            "joint.onnx.data",
            "model_config.json",
            "silero_vad.onnx",
            "tokenizer.json",
            "tokenizer_config.json",
            "vocab.txt",
        ],
    )


def _load_asr(model_id: str) -> tuple[Any, Any, str]:
    global _ASR_MODEL, _ASR_TOKENIZER, _ASR_MODEL_PATH
    if _ASR_MODEL is not None and _ASR_MODEL_PATH:
        return _ASR_MODEL, _ASR_TOKENIZER, _ASR_MODEL_PATH
    if model_id != DEFAULT_ASR_MODEL_ID:
        raise ValueError(f"Unsupported ASR model: {model_id}")

    import onnxruntime_genai as og

    model_path = _download_asr_model(model_id)
    _ASR_MODEL = og.Model(model_path)
    _ASR_TOKENIZER = og.Tokenizer(_ASR_MODEL)
    _ASR_MODEL_PATH = model_path
    return _ASR_MODEL, _ASR_TOKENIZER, model_path


def _decode_audio_bytes(audio_b64: str) -> Any:
    if not audio_b64:
        raise ValueError("No audio bytes for ASR")

    import numpy as np

    raw_audio = base64.b64decode(audio_b64)
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        "pipe:0",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "f32le",
        "pipe:1",
    ]
    proc = subprocess.run(
        command,
        input=raw_audio,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout:
        detail = proc.stderr.decode("utf-8", errors="replace").strip()[:300]
        raise ValueError(f"ffmpeg audio decode failed: {detail}")
    return np.frombuffer(proc.stdout, dtype=np.float32)


def _read_asr_config(model_path: str) -> tuple[int, int]:
    config_path = os.path.join(model_path, "genai_config.json")
    with open(config_path, "r", encoding="utf-8") as handle:
        config = json.load(handle)
    return int(config["model"]["sample_rate"]), int(config["model"]["chunk_samples"])


def _decode_available_tokens(generator: Any, tokenizer_stream: Any) -> str:
    text = ""
    while not generator.is_done():
        generator.generate_next_token()
        tokens = generator.get_next_tokens()
        for token in tokens:
            token_text = tokenizer_stream.decode(token)
            if token_text:
                text += token_text
    return text


def _supplied_transcript_asr(transcript: str, language_hint: str) -> dict[str, Any]:
    return {
        "model_id": "supplied-transcript",
        "backend": "none",
        "inference_engine": "none",
        "model_artifact_format": "none",
        "quantization": "none",
        "latency_ms": 0,
        "fallback_used": False,
        "fallback_reason": None,
        "error": None,
        "output": {
            "source_language": language_hint,
            "transcript": transcript,
            "confidence": 1.0,
            "segments": [],
        },
    }


def _asr_onnx(payload: dict[str, Any]) -> dict[str, Any]:
    started = time.time()
    audio = payload.get("audio") or {}
    asr_model_id = str(payload.get("asr_model_id") or DEFAULT_ASR_MODEL_ID)
    language_hint = str(payload.get("language_hint") or "hi")
    try:
        import onnxruntime_genai as og

        model, tokenizer, model_path = _load_asr(asr_model_id)
        processor = og.StreamingProcessor(model)
        processor.set_option("use_vad", "false")
        _, chunk_samples = _read_asr_config(model_path)
        pcm = _decode_audio_bytes(str(audio.get("b64") or ""))
        if len(pcm) == 0:
            raise ValueError("Decoded audio was empty")

        tokenizer_stream = tokenizer.create_stream()
        params = og.GeneratorParams(model)
        generator = og.Generator(model, params)
        lang_id = ASR_LANG_TO_ID.get(language_hint, ASR_LANG_TO_ID["hi"])
        generator.set_runtime_option("lang_id", str(lang_id))

        transcript = ""
        chunks_processed = 0
        chunks_skipped = 0
        for start_idx in range(0, len(pcm), chunk_samples):
            chunk = pcm[start_idx : start_idx + chunk_samples].astype("float32")
            inputs = processor.process(chunk)
            if inputs is None:
                chunks_skipped += 1
                continue
            chunks_processed += 1
            generator.set_inputs(inputs)
            transcript += _decode_available_tokens(generator, tokenizer_stream)

        inputs = processor.flush()
        if inputs is not None:
            generator.set_inputs(inputs)
            transcript += _decode_available_tokens(generator, tokenizer_stream)

        transcript = " ".join(transcript.split()).strip()
        if not transcript:
            raise ValueError("ASR returned empty transcript")
        return {
            "model_id": asr_model_id,
            "backend": "modal_http",
            "inference_engine": "onnxruntime",
            "model_artifact_format": "onnx",
            "quantization": "int4",
            "latency_ms": _duration_ms(started),
            "fallback_used": False,
            "fallback_reason": None,
            "error": None,
            "output": {
                "source_language": "hi-Latn" if lang_id == 6 else language_hint,
                "transcript": transcript,
                "confidence": 0.7,
                "segments": [],
            },
            "debug": {
                "pcm_samples": int(len(pcm)),
                "chunk_samples": int(chunk_samples),
                "chunks_processed": chunks_processed,
                "chunks_skipped": chunks_skipped,
                "lang_id": lang_id,
            },
        }
    except Exception as exc:
        return {
            "model_id": asr_model_id,
            "backend": "modal_asr_error",
            "inference_engine": "onnxruntime",
            "model_artifact_format": "onnx",
            "quantization": "int4",
            "latency_ms": _duration_ms(started),
            "fallback_used": True,
            "fallback_reason": f"modal_asr_error:{type(exc).__name__}",
            "error": str(exc),
            "output": {
                "source_language": language_hint,
                "transcript": "",
                "confidence": 0.0,
                "segments": [],
            },
        }


def _load_llm(model_id: str) -> Any:
    global _LLM, _LLM_MODEL_ID
    if _LLM is not None and _LLM_MODEL_ID == model_id:
        return _LLM
    if model_id not in TEXT_MODEL_ARTIFACTS:
        raise ValueError(f"Unsupported text model: {model_id}")

    from huggingface_hub import hf_hub_download
    from llama_cpp import Llama

    artifact = TEXT_MODEL_ARTIFACTS[model_id]
    model_path = hf_hub_download(
        repo_id=model_id,
        filename=artifact["filename"],
        cache_dir="/cache/huggingface",
    )
    _LLM = Llama(
        model_path=model_path,
        n_ctx=int(os.environ.get("VCW_LLAMA_N_CTX", "2048")),
        n_threads=int(os.environ.get("VCW_LLAMA_N_THREADS", "4")),
        n_gpu_layers=int(os.environ.get("VCW_LLAMA_N_GPU_LAYERS", "0")),
        verbose=False,
    )
    _LLM_MODEL_ID = model_id
    return _LLM


def _build_messages(transcript: str, language_hint: str) -> list[dict[str, str]]:
    schema = {
        "message_en": "short faithful English message for metime.to",
        "confidence": 0.0,
        "needs_edit": True,
        "notes": [],
    }
    return [
        {
            "role": "system",
            "content": (
                "You are a literal Hindi/Hinglish to English rewriting assistant "
                "for a website contact widget. Preserve the user's meaning. Do "
                "not act as customer support. Do not invent facts, fields, names, "
                "phone numbers, emails, order IDs, payment status, delivery "
                "outcomes, addresses, links, bookings, or account details. Return "
                "only strict JSON."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "language_hint": language_hint,
                    "asr_transcript": transcript,
                    "output_schema": schema,
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
        },
    ]


def _extract_json(raw_text: str) -> dict[str, Any]:
    stripped = raw_text.strip()
    candidates = [stripped]
    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if match:
        candidates.insert(0, match.group(0))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    raise ValueError("Text model response was not parseable JSON")


def _confidence(value: Any, default: float = 0.55) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return default
    if confidence > 1.0 and confidence <= 10.0:
        confidence = confidence / 10.0
    return max(0.0, min(1.0, confidence))


def _normalize_model_output(parsed: dict[str, Any]) -> dict[str, Any]:
    if isinstance(parsed.get("output_schema"), dict):
        parsed = parsed["output_schema"]
    return {
        "message_en": str(parsed.get("message_en") or "").strip(),
        "confidence": _confidence(parsed.get("confidence")),
        "needs_edit": bool(parsed.get("needs_edit", False)),
        "notes": parsed.get("notes") if isinstance(parsed.get("notes"), list) else [],
    }


def _text_gguf(payload: dict[str, Any], transcript: str) -> dict[str, Any]:
    started = time.time()
    text_model_id = str(payload.get("text_model_id") or TINY_AYA_TEXT_MODEL_ID)
    artifact = TEXT_MODEL_ARTIFACTS.get(text_model_id)
    if artifact is None:
        return {
            "model_id": text_model_id,
            "backend": "modal_text_unsupported",
            "inference_engine": "none",
            "model_artifact_format": "none",
            "quantization": "none",
            "latency_ms": _duration_ms(started),
            "fallback_used": True,
            "fallback_reason": "modal_text_model_not_implemented",
            "error": f"Only {TINY_AYA_TEXT_MODEL_ID} is implemented.",
            "output": {
                "message_en": "",
                "confidence": 0.0,
                "needs_edit": True,
                "notes": ["modal_text_model_not_implemented"],
            },
        }

    try:
        llm = _load_llm(text_model_id)
        raw = llm.create_chat_completion(
            messages=_build_messages(transcript, str(payload.get("language_hint") or "hi")),
            max_tokens=int(os.environ.get("VCW_LLAMA_MAX_TOKENS", "220")),
            temperature=float(os.environ.get("VCW_LLAMA_TEMPERATURE", "0.1")),
            top_p=float(os.environ.get("VCW_LLAMA_TOP_P", "0.95")),
        )
        raw_text = str(raw["choices"][0]["message"]["content"]).strip()
        output = _normalize_model_output(_extract_json(raw_text))
        if not output["message_en"]:
            raise ValueError("Text model JSON did not contain message_en")
        return {
            "model_id": artifact["label"],
            "backend": "modal_http",
            "inference_engine": artifact["inference_engine"],
            "model_artifact_format": artifact["model_artifact_format"],
            "quantization": artifact["quantization"],
            "latency_ms": _duration_ms(started),
            "fallback_used": False,
            "fallback_reason": None,
            "error": None,
            "raw_output": raw_text[:2000],
            "output": output,
        }
    except Exception as exc:
        return {
            "model_id": text_model_id,
            "backend": "modal_text_error",
            "inference_engine": artifact["inference_engine"],
            "model_artifact_format": artifact["model_artifact_format"],
            "quantization": artifact["quantization"],
            "latency_ms": _duration_ms(started),
            "fallback_used": True,
            "fallback_reason": f"modal_text_error:{type(exc).__name__}",
            "error": str(exc),
            "output": {
                "message_en": "",
                "confidence": 0.0,
                "needs_edit": True,
                "notes": ["modal_text_error"],
            },
        }


def _process(payload: dict[str, Any]) -> dict[str, Any]:
    started = time.time()
    supplied_transcript = str(payload.get("transcript") or "").strip()
    language_hint = str(payload.get("language_hint") or "hi")
    asr = _supplied_transcript_asr(supplied_transcript, language_hint) if supplied_transcript else _asr_onnx(payload)
    transcript = str((asr.get("output") or {}).get("transcript") or "")
    text = _text_gguf(payload, transcript) if transcript else {
        "model_id": "none",
        "backend": "blocked_by_asr",
        "inference_engine": "none",
        "model_artifact_format": "none",
        "quantization": "none",
        "latency_ms": 0,
        "fallback_used": True,
        "fallback_reason": "asr_blocked",
        "error": asr.get("error") or "ASR did not produce a transcript.",
        "output": {
            "message_en": "",
            "confidence": 0.0,
            "needs_edit": True,
            "notes": ["asr_blocked"],
        },
    }
    fallback_used = bool(asr.get("fallback_used")) or bool(text.get("fallback_used"))
    return {
        "model_id": f"{asr.get('model_id')}+{text.get('model_id')}",
        "backend": "modal_http",
        "inference_engine": "onnxruntime+llama.cpp",
        "model_artifact_format": "onnx+gguf",
        "quantization": "int4+q4_k_m",
        "latency_ms": _duration_ms(started),
        "fallback_used": fallback_used,
        "fallback_reason": asr.get("fallback_reason") if asr.get("fallback_used") else text.get("fallback_reason"),
        "error": asr.get("error") or text.get("error"),
        "transcript": transcript,
        "message_en": (text.get("output") or {}).get("message_en"),
        "asr": asr,
        "text": text,
    }


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name(AUTH_SECRET_NAME),
        modal.Secret.from_name(HF_SECRET_NAME),
    ],
    volumes={"/cache": cache_volume},
    timeout=180,
    startup_timeout=180,
    scaledown_window=2,
    cpu=4,
    memory=8192,
)
def process_internal(payload: dict[str, Any]) -> dict[str, Any]:
    return _process(payload)


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name(AUTH_SECRET_NAME),
        modal.Secret.from_name(HF_SECRET_NAME),
    ],
    volumes={"/cache": cache_volume},
    timeout=180,
    startup_timeout=180,
    scaledown_window=2,
    cpu=4,
    memory=8192,
)
@modal.fastapi_endpoint(method="POST")
def process(
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    expected = os.environ.get("APP_MODAL_AUTH_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=500, detail="APP_MODAL_AUTH_TOKEN is not set")
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return _process(payload)


@app.local_entrypoint()
def main() -> None:
    payload = {
        "trace_id": "modal-v1-text-smoke",
        "asr_model_id": DEFAULT_ASR_MODEL_ID,
        "text_model_id": TINY_AYA_TEXT_MODEL_ID,
        "language_hint": "hi-IN",
        "transcript": "Hi, mujhe metime.to ke pricing aur availability ke baare mein baat karni hai.",
    }
    print(json.dumps(process_internal.remote(payload), indent=2, sort_keys=True))
