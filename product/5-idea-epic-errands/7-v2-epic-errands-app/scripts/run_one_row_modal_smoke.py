"""Run one Epic Errands V2 model-backed row through the existing Modal functions.

This is a bounded paid smoke for V2 proof only: one goal, one theme, one text
model call, one image, and one audio clip. It records fresh V2 evidence and
does not claim hosted Space or judge-ready proof.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

from huggingface_hub import get_hf_file_metadata, hf_hub_url


APP_ROOT = Path(__file__).resolve().parents[1]
IDEA_ROOT = APP_ROOT.parent
REPO_ROOT = APP_ROOT.parents[2]
V1_ROOT = APP_ROOT.parent / "5-v1-epic-errands-app"
V1_SPACE_ROOT = V1_ROOT / "space"
V1_MODAL_ROOT = V1_ROOT / "modal"
OUT_ROOT = APP_ROOT / "evidence" / "live-model-smoke-2026-06-15"
RAW_ROOT = OUT_ROOT / "raw_modal_responses"
REQUEST_ROOT = OUT_ROOT / "modal_requests"
ASSET_ROOT = OUT_ROOT / "assets"
PREFLIGHT_PATH = OUT_ROOT / "model_access_preflight.json"
SUMMARY_PATH = OUT_ROOT / "summary.json"

sys.path.insert(0, str(V1_SPACE_ROOT))

from epic_errands_space.quest_generation import (  # noqa: E402
    MODEL_ID,
    VOXCPM2_MODEL_ID,
    _audio_prompt_for_card,
    _image_prompt_for_card,
    _spoken_text_for_card,
    _text_prompt_for_goal,
)


TEXT_MODEL_IDS = {
    "nemotron3": "nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF",
    "minicpm": "openbmb/MiniCPM4.1-8B",
}

REQUIRED_MODEL_FILES = [
    {
        "repo_id": "black-forest-labs/FLUX.2-klein-9B",
        "required_file": "model_index.json",
        "runtime": "Diffusers safetensors bf16 image generation",
    },
    {
        "repo_id": "nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF",
        "required_file": "NVIDIA-Nemotron3-Nano-4B-Q4_K_M.gguf",
        "runtime": "llama.cpp GGUF Q4_K_M text generation",
    },
    {
        "repo_id": "openbmb/VoxCPM2",
        "required_file": "config.json",
        "runtime": "voxcpm safetensors bf16 audio generation",
    },
]


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def configure_env() -> dict[str, str]:
    values = load_env_file(REPO_ROOT / ".env")
    values.update(load_env_file(IDEA_ROOT / ".env.modal.local"))
    for key, value in values.items():
        if key.startswith(("HF", "MODAL_", "APP_MODAL_")) and value:
            os.environ.setdefault(key, value)
    return values


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_preflight() -> dict[str, Any]:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HF_TOKEN_2") or os.environ.get("HF_TOKEN_1")
    if not token:
        raise SystemExit("Missing HF token env value for no-GPU model file access preflight.")

    results: list[dict[str, Any]] = []
    for item in REQUIRED_MODEL_FILES:
        repo_id = item["repo_id"]
        filename = item["required_file"]
        try:
            metadata = get_hf_file_metadata(hf_hub_url(repo_id, filename), token=token)
            results.append(
                {
                    **item,
                    "status": "ok",
                    "size": metadata.size,
                    "etag_present": bool(metadata.etag),
                }
            )
        except Exception as exc:  # noqa: BLE001 - record exact preflight blocker.
            results.append(
                {
                    **item,
                    "status": "blocked",
                    "exception_class": exc.__class__.__name__,
                    "error": str(exc),
                }
            )

    payload = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Fresh token-backed no-GPU required-file access check before approved Modal GPU smoke.",
        "proof_boundary": "File access only; no model load, inference, Modal GPU, or fallback proof claimed.",
        "token_source": "HF_TOKEN/HF_TOKEN_2/HF_TOKEN_1 from repo environment; value not printed",
        "results": results,
        "paid_run_allowed_now": all(result.get("status") == "ok" for result in results),
    }
    write_json(PREFLIGHT_PATH, payload)
    if not payload["paid_run_allowed_now"]:
        raise SystemExit(f"Preflight blocked; see {PREFLIGHT_PATH}")
    return payload


def save_asset(kind: str, goal_id: str, suffix: str, data_b64: str) -> str:
    digest = hashlib.sha1(data_b64.encode("ascii")).hexdigest()[:10]
    asset_dir = ASSET_ROOT / kind
    asset_dir.mkdir(parents=True, exist_ok=True)
    path = asset_dir / f"{goal_id}-{digest}.{suffix}"
    path.write_bytes(base64.b64decode(data_b64))
    return str(path.relative_to(OUT_ROOT))


def modal_run(
    app_path: Path,
    payload: dict[str, Any],
    output_name: str,
    env: dict[str, str],
    *,
    model: str | None = None,
) -> dict[str, Any]:
    REQUEST_ROOT.mkdir(parents=True, exist_ok=True)
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    payload_path = REQUEST_ROOT / f"{output_name}.request.json"
    output_path = RAW_ROOT / f"{output_name}.json"
    log_path = RAW_ROOT / f"{output_name}.log"
    write_json(payload_path, payload)

    command = [
        str(REPO_ROOT / ".venv" / "bin" / "modal"),
        "run",
        str(app_path),
        f"--payload-file={payload_path}",
        f"--output-file={output_path}",
    ]
    if model:
        command.append(f"--model={model}")

    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        timeout=20 * 60,
    )
    log_path.write_text(result.stdout, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"modal run failed for {output_name}; see {log_path}")

    body = json.loads(output_path.read_text(encoding="utf-8"))
    body["_client_latency_ms"] = round((time.monotonic() - started) * 1000)
    write_json(output_path, body)
    return body


def validate_text_response(body: dict[str, Any], goal_id: str) -> dict[str, Any]:
    outputs = body.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        raise RuntimeError("Text response missing outputs.")
    output = next((item for item in outputs if item.get("goal_id") == goal_id), outputs[0])
    if body.get("fallback_used") is not False:
        raise RuntimeError("Text response reported fallback_used=true.")
    if not output.get("schema_valid") or not isinstance(output.get("card_text"), dict):
        raise RuntimeError(f"Text schema invalid: {output.get('validation_error') or 'unknown error'}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--goal-id", default="read-20-comic")
    parser.add_argument("--goal", default="Read for 20 minutes")
    parser.add_argument("--theme", default="comic")
    parser.add_argument("--text-model", default="nemotron3", choices=["nemotron3", "minicpm"])
    parser.add_argument("--skip-audio", action="store_true")
    parser.add_argument("--skip-image", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()

    env = configure_env()
    if not env.get("APP_MODAL_AUTH_TOKEN") and not os.environ.get("APP_MODAL_AUTH_TOKEN"):
        raise SystemExit("Missing APP_MODAL_AUTH_TOKEN in .env.modal.local or environment.")

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    preflight = run_preflight()
    if args.preflight_only:
        print(f"Wrote {PREFLIGHT_PATH}")
        return 0

    started = time.monotonic()
    generated_at = datetime.now(timezone.utc).isoformat()
    goal = {"id": args.goal_id, "text": args.goal, "theme": args.theme}

    command_env = os.environ.copy()
    command_env.update({key: value for key, value in env.items() if value})

    text_payload = {
        "model": args.text_model,
        "max_new_tokens": 220,
        "items": [
            {
                "goal_id": args.goal_id,
                "ordinary_goal": args.goal,
                "theme": args.theme,
                "text_prompt": _text_prompt_for_goal(goal),
            }
        ],
    }
    text_body = modal_run(
        V1_MODAL_ROOT / "modal_epic_errands_text.py",
        text_payload,
        "text",
        command_env,
        model=args.text_model,
    )
    text_output = validate_text_response(text_body, args.goal_id)
    card_text = text_output["card_text"]

    image_body: dict[str, Any] = {}
    image_output: dict[str, Any] = {}
    if not args.skip_image:
        image_payload = {
            "height": 768,
            "width": 768,
            "steps": 4,
            "guidance": 1.0,
            "items": [
                {
                    "goal_id": args.goal_id,
                    "ordinary_goal": args.goal,
                    "theme": args.theme,
                    "card_text": card_text,
                    "prompt": _image_prompt_for_card(goal, "cozy", card_text),
                    "seed": 26002,
                }
            ],
        }
        image_body = modal_run(V1_MODAL_ROOT / "modal_epic_errands_image.py", image_payload, "image", command_env)
        image_outputs = image_body.get("outputs") or []
        image_output = image_outputs[0] if image_outputs else {}
        if image_output.get("image_png_base64"):
            image_output["image_asset_path"] = save_asset("images", args.goal_id, "png", image_output["image_png_base64"])
            image_output.pop("image_png_base64", None)
            write_json(RAW_ROOT / "image.json", image_body)

    audio_body: dict[str, Any] = {}
    audio_output: dict[str, Any] = {}
    if not args.skip_audio:
        audio_payload = {
            "cfg_value": 2.0,
            "inference_timesteps": 10,
            "items": [
                {
                    "goal_id": args.goal_id,
                    "ordinary_goal": args.goal,
                    "theme": args.theme,
                    "card_text": card_text,
                    "audio_prompt": _audio_prompt_for_card(goal, card_text),
                    "narration": _spoken_text_for_card(goal, card_text),
                }
            ],
        }
        audio_body = modal_run(V1_MODAL_ROOT / "modal_epic_errands_voxcpm2.py", audio_payload, "audio", command_env)
        audio_outputs = audio_body.get("outputs") or []
        audio_output = audio_outputs[0] if audio_outputs else {}
        if audio_output.get("audio_wav_base64"):
            audio_output["audio_asset_path"] = save_asset("audio", args.goal_id, "wav", audio_output["audio_wav_base64"])
            audio_output.pop("audio_wav_base64", None)
            write_json(RAW_ROOT / "audio.json", audio_body)

    image_fallback = args.skip_image or image_body.get("fallback_used") is not False or not image_output.get("image_asset_path")
    audio_fallback = args.skip_audio or audio_body.get("fallback_used") is not False or not audio_output.get("audio_asset_path")
    fallback_used = image_fallback or audio_fallback
    summary = {
        "generated_at": generated_at,
        "duration_ms": round((time.monotonic() - started) * 1000),
        "approved_budget_usd": 20,
        "max_runtime_minutes": 20,
        "stop_condition": "one schema-valid V2 row, first blocker, 20 wall-clock minutes, or $20 spend",
        "run_label": "Local App With Modal",
        "scope": "one V2 goal-theme row via direct Modal Functions; no hosted Space or judge-ready claim",
        "goal_id": args.goal_id,
        "plain_goal": args.goal,
        "theme": args.theme,
        "card_text": card_text,
        "text": {
            "model_id": TEXT_MODEL_IDS[args.text_model],
            "runtime_axes": {
                "lifecycle_stage": "testing",
                "app_host": "local",
                "model_runtime": "modal",
                "model_backend": "modal_function",
                "inference_engine": text_body.get("inference_engine"),
                "model_artifact_format": text_body.get("model_artifact_format"),
                "quantization": text_body.get("quantization"),
                "fallback_used": text_body.get("fallback_used"),
            },
            "schema_valid": text_output.get("schema_valid"),
            "latency_ms": text_body.get("latency_ms"),
            "client_latency_ms": text_body.get("_client_latency_ms"),
        },
        "image": {
            "model_id": MODEL_ID,
            "asset_path": image_output.get("image_asset_path", ""),
            "runtime_axes": {
                "lifecycle_stage": "testing",
                "app_host": "local",
                "model_runtime": "modal",
                "model_backend": "modal_http",
                "inference_engine": image_body.get("inference_engine"),
                "model_artifact_format": image_body.get("model_artifact_format"),
                "quantization": image_body.get("quantization"),
                "fallback_used": image_fallback,
            },
            "latency_ms": image_body.get("latency_ms"),
            "client_latency_ms": image_body.get("_client_latency_ms"),
        },
        "audio": {
            "model_id": VOXCPM2_MODEL_ID,
            "asset_path": audio_output.get("audio_asset_path", ""),
            "runtime_axes": {
                "lifecycle_stage": "testing",
                "app_host": "local",
                "model_runtime": "modal",
                "model_backend": "modal_function",
                "inference_engine": audio_body.get("inference_engine"),
                "model_artifact_format": audio_body.get("model_artifact_format"),
                "quantization": audio_body.get("quantization"),
                "fallback_used": audio_fallback,
            },
            "latency_ms": audio_body.get("latency_ms"),
            "client_latency_ms": audio_body.get("_client_latency_ms"),
        },
        "fallback_used": fallback_used,
        "model_proof_claimed": not fallback_used,
        "preflight_path": str(PREFLIGHT_PATH.relative_to(APP_ROOT)),
        "preflight": preflight,
        "evidence_files": {
            "summary": str(SUMMARY_PATH.relative_to(APP_ROOT)),
            "raw_responses": str(RAW_ROOT.relative_to(APP_ROOT)),
            "requests": str(REQUEST_ROOT.relative_to(APP_ROOT)),
            "assets": str(ASSET_ROOT.relative_to(APP_ROOT)),
        },
    }
    write_json(SUMMARY_PATH, summary)
    print(f"Wrote {SUMMARY_PATH}")
    print(f"fallback_used={fallback_used}")
    return 0 if not fallback_used else 2


if __name__ == "__main__":
    raise SystemExit(main())
