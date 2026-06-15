#!/usr/bin/env python3
"""Send one sample user message through the Venue Manager extraction endpoint."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import urllib.error
import urllib.request


SAMPLE_USER_MESSAGE = (
    "Hi, this is Aman Sharma. Need a cricket ground tomorrow morning "
    "8 AM to 12 PM for 12 players. Natural grass preferred, North Field if "
    "available. Budget is around Rs 6000. My number is +91 98765 43210."
)


def post_json(url: str, payload: dict) -> dict:
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("HF_TOKEN_FOR_SPACE")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {body}") from exc


def app_url_from_space(space: str) -> str:
    if space.startswith("https://") and ".hf.space" in space:
        return space.rstrip("/")
    if space.startswith("https://huggingface.co/spaces/"):
        parts = space.rstrip("/").split("/spaces/", 1)[1].split("/")
        return f"https://{parts[0]}-{parts[1]}.hf.space"
    if "/" in space:
        owner, name = space.split("/", 1)
        return f"https://{owner}-{name}.hf.space"
    return space.rstrip("/")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", help="App base URL, e.g. http://127.0.0.1:7860")
    parser.add_argument("--space", help="HF Space id or URL.")
    parser.add_argument("--message", default=SAMPLE_USER_MESSAGE)
    parser.add_argument("--trace-id", default="hosted-venue-sample-001")
    parser.add_argument("--hf-token-env", help="Optional env key for private Space auth, e.g. HF_TOKEN_2.")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(__file__).resolve().parents[4] / ".env",
        help="Env file used only to read --hf-token-env without printing it.",
    )
    args = parser.parse_args()

    if args.hf_token_env:
        token = os.environ.get(args.hf_token_env) or _load_env(args.env_file).get(args.hf_token_env)
        if not token:
            raise SystemExit(f"Missing {args.hf_token_env} in environment or {args.env_file}.")
        os.environ["HF_TOKEN_FOR_SPACE"] = token

    if args.space:
        base_url = app_url_from_space(args.space)
    else:
        base_url = (args.base_url or "http://127.0.0.1:7860").rstrip("/")
    result = post_json(
        f"{base_url}/api/extract-booking",
        {"message": args.message, "trace_id": args.trace_id, "scenario": "normal"},
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") and result.get("fallback_used") is False else 1


def _load_env(path: Path) -> dict[str, str]:
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


if __name__ == "__main__":
    raise SystemExit(main())
