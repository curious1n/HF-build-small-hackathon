#!/usr/bin/env python3
"""Resolve and upload the Venue Manager v2 Hugging Face Space package.

This deploys to the hackathon namespace using account slot 2:

- `HF_HACKATHON`: target namespace, e.g. build-small-hackathon.
- `HF_2`: upload actor label.
- `HF_TOKEN_2`: upload actor token.

Secret values are never printed.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent
IDEA_ROOT = APP_ROOT.parent
REPO_ROOT = APP_ROOT.parents[2]
ENV_PATH = REPO_ROOT / ".env"
LOCAL_MODAL_ENV = IDEA_ROOT / ".env.modal.local"
SPACE_ROOT = APP_ROOT / "space"
DEFAULT_SPACE_NAME = "venue-manager-agent"
DEFAULT_MODEL_ID = "nvidia/Nemotron-Cascade-2-30B-A3B"
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
]


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text().splitlines():
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
        if key.startswith("HF") or key.startswith("APP_MODAL"):
            values[key] = value
    return values


def resolve_space_config(values: dict[str, str]) -> tuple[str, str, str]:
    namespace = values.get("HF_HACKATHON", "").strip()
    if not namespace:
        raise SystemExit("Missing HF_HACKATHON in repo .env or environment.")
    if not values.get("HF_2", "").strip():
        raise SystemExit("Missing HF_2 in repo .env or environment for the upload actor label.")
    token_source = "HF_TOKEN_2"
    token = values.get(token_source, "").strip()
    if not token:
        raise SystemExit("Missing HF_TOKEN_2 in repo .env or environment.")
    return f"{namespace}/{DEFAULT_SPACE_NAME}", token, token_source


def upload_space(repo_id: str, token: str, commit_message: str, *, create: bool) -> None:
    os.environ.setdefault("HF_HOME", str(REPO_ROOT / ".hf-cache"))
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    if create:
        api.create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="gradio",
            exist_ok=True,
            private=True,
        )
    api.upload_folder(
        repo_id=repo_id,
        repo_type="space",
        folder_path=str(SPACE_ROOT),
        commit_message=commit_message,
        ignore_patterns=UPLOAD_IGNORE_PATTERNS,
    )


def set_modal_config(repo_id: str, token: str, values: dict[str, str], *, dry_run: bool) -> None:
    required = ["APP_MODAL_BASE_URL", "APP_MODAL_AUTH_TOKEN"]
    missing = [key for key in required if not values.get(key)]
    if missing:
        raise SystemExit(f"Missing Modal config: {', '.join(missing)}")

    variables = {
        "APP_MODAL_BASE_URL": values["APP_MODAL_BASE_URL"],
        "APP_MODAL_TIMEOUT_SECONDS": values.get("APP_MODAL_TIMEOUT_SECONDS", "120"),
        "APP_MODAL_MODEL_ID": values.get("APP_MODAL_MODEL_ID", DEFAULT_MODEL_ID),
    }
    secrets = {"APP_MODAL_AUTH_TOKEN": values["APP_MODAL_AUTH_TOKEN"]}

    if dry_run:
        for key in sorted(variables):
            print(f"{repo_id}: would set variable {key}=<set>")
        for key in sorted(secrets):
            print(f"{repo_id}: would set secret {key}=<set>")
        return

    os.environ.setdefault("HF_HOME", str(REPO_ROOT / ".hf-cache"))
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    for key, value in variables.items():
        api.add_space_variable(repo_id=repo_id, key=key, value=value)
        print(f"{repo_id}: variable {key}=<set>")
    for key, value in secrets.items():
        api.add_space_secret(repo_id=repo_id, key=key, value=value)
        print(f"{repo_id}: secret {key}=<set>")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upload", action="store_true", help="Upload the Space package.")
    parser.add_argument("--create", action="store_true", help="Create the private Gradio Space if needed.")
    parser.add_argument("--set-modal-config", action="store_true", help="Set APP_MODAL_* variables/secrets.")
    parser.add_argument("--config-dry-run", action="store_true", help="Show redacted Modal config writes.")
    parser.add_argument(
        "--commit-message",
        default="Deploy Venue Manager v2 Space",
        help="Commit message for --upload.",
    )
    args = parser.parse_args()

    values = merged_env()
    repo_id, token, token_source = resolve_space_config(values)
    print(f"Venue Manager v2 Space repo: {repo_id}")
    print("Target namespace source: HF_HACKATHON=<set>")
    print("Upload actor source: HF_2=<set>")
    print(f"Auth source: {token_source}=<set>")
    print(f"Package root: {SPACE_ROOT}")

    if args.upload:
        upload_space(repo_id, token, args.commit_message, create=args.create)
        print("Upload complete.")
    if args.set_modal_config:
        set_modal_config(repo_id, token, values, dry_run=args.config_dry_run)
    if not args.upload and not args.set_modal_config:
        print("Dry run only. Add --upload and/or --set-modal-config to mutate HF state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
