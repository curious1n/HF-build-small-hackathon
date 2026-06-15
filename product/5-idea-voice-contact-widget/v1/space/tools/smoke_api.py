from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import wave


SPACE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_BASE_URL = "https://build-small-hackathon-voice-reach.hf.space"


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("'\"")
    values.update(os.environ)
    return values


def request_json(base_url: str, path: str, token: str | None, payload: dict | None = None, timeout: float = 30) -> dict:
    data = None
    headers = {}
    method = "GET"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        method = "POST"
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(f"{base_url.rstrip('/')}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {"ok": True, "status": response.status, "body": json.loads(body)}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"raw": body[:1000]}
        return {"ok": False, "status": exc.code, "body": parsed}


def wav_duration_ms(path: Path) -> int | None:
    if path.suffix.lower() != ".wav":
        return None
    with wave.open(str(path), "rb") as handle:
        rate = handle.getframerate()
        if not rate:
            return None
        return round((handle.getnframes() / rate) * 1000)


def process_payload(audio_file: Path, speech_mode: str, duration_ms: int | None) -> dict:
    audio_bytes = audio_file.read_bytes()
    mime = mimetypes.guess_type(audio_file.name)[0] or "application/octet-stream"
    return {
        "speech_mode": speech_mode,
        "visitor_notice_shown": True,
        "audio_duration_ms": duration_ms or wav_duration_ms(audio_file) or 0,
        "audio_size_bytes": len(audio_bytes),
        "audio_mime": mime,
        "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
    }


def text_smoke_payload(transcript: str, speech_mode: str) -> dict:
    return {
        "speech_mode": speech_mode,
        "visitor_notice_shown": True,
        "transcript": transcript,
    }


def summarize_trace(trace: dict) -> dict:
    return {
        "trace_id": trace.get("trace_id"),
        "created_at": trace.get("created_at"),
        "speech_mode": trace.get("speech_mode"),
        "asr_language_hint": trace.get("asr_language_hint"),
        "fallback_used": trace.get("fallback_used"),
        "fallback_reason": trace.get("fallback_reason"),
        "blocker": trace.get("blocker"),
        "text_only_smoke": trace.get("text_only_smoke"),
        "transcript": (trace.get("asr") or {}).get("transcript"),
        "message_en": ((trace.get("text") or {}).get("output") or {}).get("message_en"),
        "needs_edit": ((trace.get("text") or {}).get("output") or {}).get("needs_edit"),
        "guardrail_flags": ((trace.get("text") or {}).get("output") or {}).get("guardrail_flags"),
        "timings_ms": trace.get("timings_ms"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke Voice Reach V1 API.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--token-env", default="HF_TOKEN_2")
    parser.add_argument("--timeout", default=30.0, type=float)
    parser.add_argument("--include-traces", action="store_true", help="Read /api/traces and summarize recent failures.")
    parser.add_argument("--process-audio", type=Path, help="Optional real audio file for /api/process.")
    parser.add_argument("--text-transcript", help="Optional supplied transcript for a tiny-aya-only /api/text-smoke request.")
    parser.add_argument("--speech-mode", default="hinglish", choices=["hindi", "hinglish"])
    parser.add_argument("--audio-duration-ms", type=int)
    parser.add_argument(
        "--allow-model-request",
        action="store_true",
        help="Required with --process-audio so status checks do not accidentally spend model time.",
    )
    args = parser.parse_args()

    env = load_env()
    token = env.get(args.token_env) or env.get("HF_TOKEN")
    started = time.time()
    report: dict[str, object] = {
        "base_url": args.base_url,
        "token_env": args.token_env if token else None,
        "checks": {},
    }

    for path in ("/health", "/api/packet"):
        report["checks"][path] = request_json(args.base_url, path, token, timeout=args.timeout)

    if args.include_traces:
        traces = request_json(args.base_url, "/api/traces", token, timeout=args.timeout)
        if traces["ok"]:
            items = traces["body"].get("items", [])
            traces["body"] = {"items": [summarize_trace(item) for item in items[:10]]}
        report["checks"]["/api/traces"] = traces

    if args.process_audio:
        if not args.allow_model_request:
            raise SystemExit("--process-audio requires --allow-model-request")
        payload = process_payload(args.process_audio, args.speech_mode, args.audio_duration_ms)
        process = request_json(args.base_url, "/api/process", token, payload=payload, timeout=args.timeout)
        body = process.get("body") or {}
        if isinstance(body, dict) and "trace" in body:
            body = {**body, "trace": summarize_trace(body["trace"])}
            process["body"] = body
        report["checks"]["/api/process"] = process

    if args.text_transcript:
        if not args.allow_model_request:
            raise SystemExit("--text-transcript requires --allow-model-request")
        payload = text_smoke_payload(args.text_transcript, args.speech_mode)
        text_smoke = request_json(args.base_url, "/api/text-smoke", token, payload=payload, timeout=args.timeout)
        body = text_smoke.get("body") or {}
        if isinstance(body, dict) and "trace" in body:
            body = {**body, "trace": summarize_trace(body["trace"])}
            text_smoke["body"] = body
        report["checks"]["/api/text-smoke"] = text_smoke

    report["elapsed_ms"] = round((time.time() - started) * 1000)
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    failed = [path for path, result in report["checks"].items() if not result.get("ok")]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
