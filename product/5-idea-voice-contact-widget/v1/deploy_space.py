#!/usr/bin/env python3
"""Deploy and guard the Voice Reach V1 Hugging Face Space.

This helper keeps the target Space, token slot, and paid hardware controls
explicit. It never prints secret values.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APP_ROOT = Path(__file__).resolve().parent
IDEA_ROOT = APP_ROOT.parent
REPO_ROOT = APP_ROOT.parents[2]
ENV_PATH = REPO_ROOT / ".env"
LOCAL_MODAL_ENV = IDEA_ROOT / ".env.modal.local"
SPACE_ROOT = APP_ROOT / "space"
DEFAULT_SPACE_NAME = "voice-reach"
DEFAULT_HARDWARE = "t4-medium"
CPU_HARDWARE = "cpu-basic"
T4_MEDIUM_USD_PER_HOUR = 0.60
DEFAULT_MODAL_BASE_URL = "https://curious1n--voice-reach-v1-modal-process.modal.run"
DEFAULT_MODAL_ASR_MODEL_ID = "onnx-community/nemotron-3.5-asr-streaming-0.6b-onnx-int4"
DEFAULT_MODAL_TEXT_MODEL_ID = "CohereLabs/tiny-aya-fire-GGUF"
DEFAULT_HF_PERSONAL_BASE_URL = "https://curieous-voice-reach.hf.space"
TARGET_PROFILES = {
    "modal-test": {
        "description": "HF hackathon Space on CPU Basic calling Modal for model testing. Not for submission.",
        "namespace_env": "HF_HACKATHON",
        "token_env": "HF_TOKEN_2",
        "space_name": "voice-reach",
        "model_runtime": "modal",
        "hardware": CPU_HARDWARE,
        "sleep_time": 172800,
        "modal": True,
        "allow_runtime_switch": True,
    },
    "hf2-t4-test": {
        "description": "HF_2-owned Space on t4-medium for testing the Space-local HF GPU path.",
        "namespace_env": "HF_2",
        "token_env": "HF_TOKEN_2",
        "space_name": "voice-reach",
        "model_runtime": "hf_space",
        "hardware": DEFAULT_HARDWARE,
        "sleep_time": 900,
        "modal": False,
        "allow_runtime_switch": True,
    },
    "hackathon-t4-submit": {
        "description": "Official hackathon-org Space on t4-medium with Modal disabled.",
        "namespace_env": "HF_HACKATHON",
        "token_env": "HF_TOKEN_2",
        "space_name": "voice-reach",
        "model_runtime": "hf_space",
        "hardware": DEFAULT_HARDWARE,
        "sleep_time": -1,
        "modal": False,
        "allow_runtime_switch": False,
    },
}
UPLOAD_IGNORE_PATTERNS = [
    "__pycache__/**",
    "**/__pycache__/**",
    "*.pyc",
    "**/*.pyc",
    ".env",
    "**/.env",
    ".venv/**",
    "venv/**",
    "node_modules/**",
    ".DS_Store",
    "**/.DS_Store",
    "demo-ledger.jsonl",
]
MODEL_FILES = [
    ("nvidia/nemotron-3.5-asr-streaming-0.6b", "nemotron-3.5-asr-streaming-0.6b.nemo"),
    ("CohereLabs/tiny-aya-fire-GGUF", "tiny-aya-fire-q8_0.gguf"),
]


def load_env(path: Path) -> dict[str, str]:
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


def merged_env() -> dict[str, str]:
    values = load_env(ENV_PATH)
    values.update(load_env(LOCAL_MODAL_ENV))
    for key, value in os.environ.items():
        if (
            key.startswith("HF")
            or key.startswith("APP_MODAL")
            or key.startswith("APP_HF_PERSONAL")
            or key.startswith("VCW_MODEL")
            or key.startswith("VCW_ALLOW_RUNTIME_SWITCH")
        ):
            values[key] = value
    return values


def target_profile(name: str) -> dict[str, Any]:
    try:
        return TARGET_PROFILES[name]
    except KeyError as exc:
        raise SystemExit(f"Unknown target {name!r}; choose one of {', '.join(sorted(TARGET_PROFILES))}.") from exc


def resolve_space_config(values: dict[str, str], profile: dict[str, Any], space_name: str | None) -> tuple[str, str, str, str]:
    namespace_env = str(profile["namespace_env"])
    token_env = str(profile["token_env"])
    resolved_space_name = space_name or str(profile["space_name"])
    namespace = values.get(namespace_env, "").strip()
    if not namespace:
        raise SystemExit(f"Missing {namespace_env} in repo .env or environment.")
    token_source = token_env
    token = values.get(token_source, "").strip()
    if not token:
        raise SystemExit(f"Missing {token_env} in repo .env or environment.")
    return f"{namespace}/{resolved_space_name}", namespace, token, token_source


def runtime_summary(runtime: Any) -> dict[str, Any]:
    return {
        "stage": getattr(getattr(runtime, "stage", None), "value", getattr(runtime, "stage", None)),
        "hardware": getattr(runtime, "hardware", None),
        "requested_hardware": getattr(runtime, "requested_hardware", None),
        "sleep_time": getattr(runtime, "sleep_time", None),
        "raw_error": getattr(runtime, "raw_error", None),
    }


def print_json(label: str, payload: dict[str, Any]) -> None:
    print(label)
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def preflight_model_files(token: str) -> list[dict[str, Any]]:
    from huggingface_hub import hf_hub_download

    results: list[dict[str, Any]] = []
    for repo_id, filename in MODEL_FILES:
        info = hf_hub_download(repo_id=repo_id, filename=filename, repo_type="model", token=token, dry_run=True)
        results.append(
            {
                "repo_id": repo_id,
                "filename": filename,
                "size": getattr(info, "size", None),
                "will_download": getattr(info, "will_download", None),
                "is_cached": getattr(info, "is_cached", None),
                "access": "pass",
            }
        )
    return results


def upload_space(repo_id: str, token: str, commit_message: str, *, create: bool) -> dict[str, Any]:
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    if create:
        api.create_repo(repo_id=repo_id, repo_type="space", space_sdk="docker", exist_ok=True, private=True)
    info = api.repo_info(repo_id=repo_id, repo_type="space")
    if getattr(info, "private", None) is not True:
        raise SystemExit(f"Refusing to upload: Space {repo_id} is not private.")
    commit = api.upload_folder(
        repo_id=repo_id,
        repo_type="space",
        folder_path=str(SPACE_ROOT),
        path_in_repo=".",
        commit_message=commit_message,
        ignore_patterns=UPLOAD_IGNORE_PATTERNS,
        delete_patterns=["*"],
    )
    return {"commit_oid": getattr(commit, "oid", None), "commit_url": getattr(commit, "commit_url", None)}


def configure_runtime_token(repo_id: str, token: str, token_source: str) -> dict[str, Any]:
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    api.add_space_secret(repo_id=repo_id, key="HF_TOKEN", value=token)
    api.add_space_secret(repo_id=repo_id, key=token_source, value=token)
    api.add_space_variable(repo_id=repo_id, key="VCW_MODEL_MODE", value="real")
    return {
        "secrets": ["HF_TOKEN", token_source],
        "variables": {"VCW_MODEL_MODE": "real"},
    }


def ignore_missing_hf_delete(func: Any, *, repo_id: str, key: str) -> None:
    try:
        func(repo_id=repo_id, key=key)
    except Exception:
        pass


def configure_target_runtime(
    repo_id: str,
    token: str,
    values: dict[str, str],
    profile: dict[str, Any],
    modal_base_url: str,
) -> dict[str, Any]:
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    variables = {
        "VCW_MODEL_MODE": "real",
        "VCW_MODEL_RUNTIME": str(profile["model_runtime"]),
    }
    secrets: list[str] = []
    removed: list[str] = []
    allow_runtime_switch = bool(profile.get("allow_runtime_switch"))
    if allow_runtime_switch:
        variables["VCW_ALLOW_RUNTIME_SWITCH"] = "1"
        variables["APP_HF_PERSONAL_BASE_URL"] = values.get("APP_HF_PERSONAL_BASE_URL", DEFAULT_HF_PERSONAL_BASE_URL)
        api.add_space_secret(repo_id=repo_id, key="APP_HF_PERSONAL_TOKEN", value=token)
        secrets.append("APP_HF_PERSONAL_TOKEN")
    else:
        for key in ("VCW_ALLOW_RUNTIME_SWITCH", "APP_HF_PERSONAL_BASE_URL"):
            ignore_missing_hf_delete(api.delete_space_variable, repo_id=repo_id, key=key)
            removed.append(key)
        ignore_missing_hf_delete(api.delete_space_secret, repo_id=repo_id, key="APP_HF_PERSONAL_TOKEN")
        removed.append("APP_HF_PERSONAL_TOKEN")

    if profile.get("modal") or allow_runtime_switch:
        auth_token = values.get("APP_MODAL_AUTH_TOKEN", "").strip()
        if not auth_token:
            raise SystemExit(f"Missing APP_MODAL_AUTH_TOKEN in {LOCAL_MODAL_ENV} or environment.")
        variables.update(
            {
                "APP_MODAL_BASE_URL": modal_base_url,
                "APP_MODAL_TIMEOUT_SECONDS": values.get("APP_MODAL_TIMEOUT_SECONDS", "180"),
                "APP_MODAL_MODEL_ID": DEFAULT_MODAL_TEXT_MODEL_ID,
                "APP_MODAL_ASR_MODEL_ID": DEFAULT_MODAL_ASR_MODEL_ID,
            }
        )
        api.add_space_secret(repo_id=repo_id, key="APP_MODAL_AUTH_TOKEN", value=auth_token)
        secrets.append("APP_MODAL_AUTH_TOKEN")
    else:
        for key in ("APP_MODAL_BASE_URL", "APP_MODAL_TIMEOUT_SECONDS", "APP_MODAL_MODEL_ID", "APP_MODAL_ASR_MODEL_ID"):
            ignore_missing_hf_delete(api.delete_space_variable, repo_id=repo_id, key=key)
            removed.append(key)
        ignore_missing_hf_delete(api.delete_space_secret, repo_id=repo_id, key="APP_MODAL_AUTH_TOKEN")
        removed.append("APP_MODAL_AUTH_TOKEN")

    for key, value in variables.items():
        api.add_space_variable(repo_id=repo_id, key=key, value=value)
    return {
        "variables": {key: "<set>" for key in sorted(variables)},
        "secrets": secrets,
        "removed_runtime_keys": removed,
    }


def validate_paid_request(hardware: str, sleep_time: int, max_paid_usd: float) -> None:
    if hardware != DEFAULT_HARDWARE:
        raise SystemExit(f"V1 paid proof is restricted to {DEFAULT_HARDWARE}; got {hardware}.")
    if sleep_time == -1:
        return
    max_seconds = int(max_paid_usd / T4_MEDIUM_USD_PER_HOUR * 3600)
    if sleep_time > max_seconds:
        raise SystemExit(
            f"sleep_time={sleep_time}s can exceed ${max_paid_usd:.2f} on {hardware}; use <= {max_seconds}s."
        )


def request_hardware(repo_id: str, token: str, hardware: str, sleep_time: int, max_paid_usd: float) -> dict[str, Any]:
    from huggingface_hub import HfApi

    validate_paid_request(hardware, sleep_time, max_paid_usd)
    api = HfApi(token=token)
    runtime = api.request_space_hardware(repo_id=repo_id, hardware=hardware, sleep_time=sleep_time)
    return runtime_summary(runtime)


def request_cpu(repo_id: str, token: str) -> dict[str, Any]:
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    runtime = api.request_space_hardware(repo_id=repo_id, hardware=CPU_HARDWARE)
    return runtime_summary(runtime)


def pause_space(repo_id: str, token: str) -> dict[str, Any]:
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    runtime = api.pause_space(repo_id=repo_id)
    return runtime_summary(runtime)


def restart_space(repo_id: str, token: str) -> dict[str, Any]:
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    runtime = api.restart_space(repo_id=repo_id)
    return runtime_summary(runtime)


def wait_running(repo_id: str, token: str, timeout_seconds: int, poll_seconds: int) -> dict[str, Any]:
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    deadline = time.monotonic() + timeout_seconds
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        runtime = api.get_space_runtime(repo_id=repo_id)
        last = runtime_summary(runtime)
        print_json("Runtime:", last)
        stage = str(last.get("stage") or "").upper()
        if stage == "RUNNING":
            return last
        if stage in {"BUILD_ERROR", "RUNTIME_ERROR"}:
            raise SystemExit(f"Space entered terminal stage: {stage}")
        time.sleep(poll_seconds)
    raise SystemExit(f"Timed out waiting for {repo_id} to reach RUNNING; last={last}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=sorted(TARGET_PROFILES), default="modal-test")
    parser.add_argument("--space-name", help="Override the profile's Space slug.")
    parser.add_argument("--preflight-model-files", action="store_true")
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--configure-runtime-token", action="store_true")
    parser.add_argument("--configure-target-runtime", action="store_true")
    parser.add_argument("--configure-modal-runtime", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--request-hardware", action="store_true")
    parser.add_argument("--request-t4", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--wait-running", action="store_true")
    parser.add_argument("--pause", action="store_true")
    parser.add_argument("--cpu-basic", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--sleep-time", type=int)
    parser.add_argument("--max-paid-usd", type=float, default=10.0)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--poll-seconds", type=int, default=30)
    parser.add_argument("--commit-message", default="Deploy Voice Reach V1 Space")
    parser.add_argument("--modal-base-url", default=DEFAULT_MODAL_BASE_URL)
    args = parser.parse_args()

    values = merged_env()
    profile = target_profile(args.target)
    repo_id, namespace, token, token_source = resolve_space_config(values, profile, args.space_name)
    hardware = str(profile["hardware"])
    sleep_time = int(args.sleep_time if args.sleep_time is not None else profile["sleep_time"])
    print(f"Voice Reach V1 Space repo: {repo_id}")
    print(f"Target profile: {args.target}")
    print(f"Target profile description: {profile['description']}")
    print(f"Target namespace source: {profile['namespace_env']}=<set>")
    print(f"Auth source: {token_source}=<set>")
    print(f"Package root: {SPACE_ROOT}")
    print(f"Runtime profile: VCW_MODEL_RUNTIME={profile['model_runtime']}")
    print(f"Hardware profile: hardware={hardware}, sleep_time={sleep_time}s")
    print(f"Budget guard: max_paid_usd=${args.max_paid_usd:.2f}")

    if args.preflight_model_files:
        print_json("Model file preflight:", {"files": preflight_model_files(token)})
    if args.upload:
        print_json("Upload:", upload_space(repo_id, token, args.commit_message, create=args.create))
    if args.configure_runtime_token:
        print_json("Runtime token config:", configure_runtime_token(repo_id, token, token_source))
    if args.configure_target_runtime or args.configure_modal_runtime:
        print_json("Target runtime config:", configure_target_runtime(repo_id, token, values, profile, args.modal_base_url))
    if args.request_hardware or args.request_t4:
        if hardware == CPU_HARDWARE:
            print_json("Requested CPU hardware:", request_cpu(repo_id, token))
        else:
            print_json("Requested paid hardware:", request_hardware(repo_id, token, hardware, sleep_time, args.max_paid_usd))
    if args.restart:
        print_json("Restarted:", restart_space(repo_id, token))
    if args.wait_running:
        wait_running(repo_id, token, args.timeout_seconds, args.poll_seconds)
    if args.status:
        from huggingface_hub import HfApi

        print_json("Status:", runtime_summary(HfApi(token=token).get_space_runtime(repo_id=repo_id)))
    if args.pause:
        print_json("Paused:", pause_space(repo_id, token))
    if args.cpu_basic:
        print_json("Requested CPU hardware:", request_cpu(repo_id, token))

    if not any(
        [
            args.preflight_model_files,
            args.upload,
            args.configure_runtime_token,
            args.configure_target_runtime,
            args.configure_modal_runtime,
            args.request_hardware,
            args.request_t4,
            args.restart,
            args.wait_running,
            args.status,
            args.pause,
            args.cpu_basic,
        ]
    ):
        print(
            "Dry run only. Add --upload, --configure-runtime-token, --configure-target-runtime, "
            "--preflight-model-files, --request-hardware, --restart, --wait-running, --status, "
            "--pause, or --cpu-basic."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
