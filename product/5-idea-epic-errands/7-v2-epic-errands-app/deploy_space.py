#!/usr/bin/env python3
"""Resolve and upload the Epic Errands V2 Hugging Face Space package.

Epic Errands V2 uses the same private hackathon Space target as V1:

- `HF_HACKATHON`: Hugging Face org/namespace target, e.g. build-small-hackathon.
- `HF_2`: Hugging Face username for upload actor 2.
- `HF_TOKEN_2`: token for upload actor 2.

Secret values are never printed.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent
REPO_ROOT = APP_ROOT.parents[2]
ENV_PATH = REPO_ROOT / ".env"
SPACE_ROOT = APP_ROOT / "space"
DEFAULT_SPACE_NAME = "epic-errands"
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
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def merged_env() -> dict[str, str]:
    values = load_env(ENV_PATH)
    for key, value in os.environ.items():
        if key.startswith("HF"):
            values[key] = value
    return values


def resolve_space_config(values: dict[str, str]) -> tuple[str, str, str]:
    namespace = values.get("HF_HACKATHON", "").strip()
    if not namespace:
        raise SystemExit(
            "Missing HF_HACKATHON in repo .env or environment. "
            "Epic Errands V2 deploys to HF_HACKATHON/epic-errands."
        )
    if not values.get("HF_2", "").strip():
        raise SystemExit("Missing HF_2 in repo .env or environment for the upload actor label.")
    repo_id = f"{namespace}/{DEFAULT_SPACE_NAME}"

    token_source = "HF_TOKEN_2"
    token = values.get(token_source, "").strip()
    if not token:
        raise SystemExit("Missing HF_TOKEN_2 in repo .env or environment.")

    return repo_id, token, token_source


def upload_space(repo_id: str, token: str, commit_message: str, *, create: bool) -> None:
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
        delete_patterns=["*"],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload the local space/ folder to the resolved HF Space repo.",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create the target private Gradio Space first if it does not exist.",
    )
    parser.add_argument(
        "--commit-message",
        default="Deploy Epic Errands V2 Space",
        help="Commit message for --upload.",
    )
    args = parser.parse_args()

    values = merged_env()
    repo_id, token, token_source = resolve_space_config(values)
    print(f"Epic Errands V2 Space repo: {repo_id}")
    print("Target namespace source: HF_HACKATHON=<set>")
    print("Upload actor source: HF_2=<set>")
    print(f"Auth source: {token_source}=<set>")
    print(f"Package root: {SPACE_ROOT}")

    if args.upload:
        upload_space(repo_id, token, args.commit_message, create=args.create)
        print("Upload complete.")
    else:
        print("Dry run only. Add --upload to push the Space package.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
