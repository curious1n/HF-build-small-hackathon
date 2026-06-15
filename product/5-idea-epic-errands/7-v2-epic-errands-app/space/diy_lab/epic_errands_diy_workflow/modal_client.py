from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from .contracts import (
    AudioRequest,
    AudioResult,
    ImageRequest,
    ImageResult,
    PlainGoalInput,
    RuntimeMetadata,
    TextResult,
)


Transport = Callable[[str, dict[str, Any], dict[str, str], float], dict[str, Any]]


def _default_transport(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


@dataclass(frozen=True)
class ModalClientConfig:
    dry_run: bool = True
    base_url: str = ""
    text_url: str = ""
    image_url: str = ""
    audio_url: str = ""
    auth_token: str = ""
    timeout_seconds: float = 45
    model_id: str = ""

    @classmethod
    def from_env(cls) -> "ModalClientConfig":
        dry_value = os.environ.get("APP_DRY_RUN", "true").strip().lower()
        live_value = os.environ.get("EPIC_ENABLE_LIVE_GENERATION", "").strip().lower()
        dry_run = dry_value not in {"0", "false", "no"}
        if live_value in {"1", "true", "yes"}:
            dry_run = False
        return cls(
            dry_run=dry_run,
            base_url=os.environ.get("APP_MODAL_BASE_URL", "") or os.environ.get("EPIC_MODAL_BASE_URL", ""),
            text_url=os.environ.get("APP_MODAL_TEXT_URL", "") or os.environ.get("EPIC_MODAL_TEXT_URL", ""),
            image_url=os.environ.get("APP_MODAL_IMAGE_URL", "") or os.environ.get("EPIC_MODAL_IMAGE_URL", ""),
            audio_url=(
                os.environ.get("APP_MODAL_AUDIO_URL", "")
                or os.environ.get("EPIC_MODAL_AUDIO_URL", "")
                or os.environ.get("EPIC_MODAL_VOXCPM2_URL", "")
            ),
            auth_token=os.environ.get("APP_MODAL_AUTH_TOKEN", ""),
            timeout_seconds=float(os.environ.get("APP_MODAL_TIMEOUT_SECONDS", "45") or 45),
            model_id=os.environ.get("APP_MODAL_MODEL_ID", ""),
        )


class ModalClient:
    def __init__(
        self,
        config: ModalClientConfig | None = None,
        transport: Transport | None = None,
    ):
        self.config = config or ModalClientConfig.from_env()
        self._transport = transport or _default_transport

    def generate_text(self, goal: PlainGoalInput) -> TextResult:
        if self.config.dry_run:
            return self._dry_text(goal)
        payload = {
            "items": [
                {
                    "goal_id": goal.goal_id,
                    "ordinary_goal": goal.ordinary_goal,
                    "theme": goal.theme,
                }
            ],
            "model": self.config.model_id,
        }
        result = self._post(self._url("text"), payload)
        output = result["outputs"][0]
        card = output.get("card_text") or {}
        return TextResult(
            goal_id=goal.goal_id,
            ordinary_goal=goal.ordinary_goal,
            theme=goal.theme,
            title=str(card.get("title") or ""),
            narration=str(card.get("narration") or ""),
            reward_label=str(card.get("reward_label") or ""),
            steps=_steps_for(goal.ordinary_goal),
            text_prompt=str(output.get("text_prompt") or ""),
            runtime_metadata=_metadata_from_modal(result),
        )

    def generate_image(self, request: ImageRequest) -> ImageResult:
        if self.config.dry_run:
            return self._dry_image(request)
        payload = {
            "items": [
                {
                    "goal_id": request.goal_id,
                    "ordinary_goal": request.ordinary_goal,
                    "theme": request.theme,
                    "card_text": request.card_text,
                    "prompt": request.prompt,
                    "seed": request.seed,
                }
            ],
            "height": request.height,
            "width": request.width,
        }
        result = self._post(self._url("image"), payload)
        output = result["outputs"][0]
        return ImageResult(
            goal_id=request.goal_id,
            request=request,
            asset_kind="modal_png_base64",
            artifact_uri="data:image/png;base64," + str(output.get("image_png_base64") or ""),
            placeholder_label="",
            prompt_summary=str(output.get("prompt_summary") or request.prompt),
            runtime_metadata=_metadata_from_modal(result),
        )

    def generate_audio(self, request: AudioRequest) -> AudioResult:
        if self.config.dry_run:
            return self._dry_audio(request)
        payload = {
            "items": [
                {
                    "goal_id": request.goal_id,
                    "ordinary_goal": request.ordinary_goal,
                    "theme": request.theme,
                    "card_text": request.card_text,
                    "audio_prompt": request.audio_prompt,
                    "narration": request.spoken_text,
                }
            ]
        }
        result = self._post(self._url("audio"), payload)
        output = result["outputs"][0]
        return AudioResult(
            goal_id=request.goal_id,
            request=request,
            asset_kind="modal_wav_base64",
            artifact_uri="data:audio/wav;base64," + str(output.get("audio_wav_base64") or ""),
            placeholder_label="",
            transcript_hint=str(output.get("spoken_text") or request.spoken_text),
            runtime_metadata=_metadata_from_modal(result),
        )

    def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not url:
            raise RuntimeError("Modal URL is required when APP_DRY_RUN=false.")
        if not self.config.auth_token:
            raise RuntimeError("APP_MODAL_AUTH_TOKEN is required when APP_DRY_RUN=false.")
        headers = {
            "Authorization": f"Bearer {self.config.auth_token}",
            "Content-Type": "application/json",
        }
        return self._transport(url, payload, headers, self.config.timeout_seconds)

    def _url(self, kind: str) -> str:
        if kind == "text":
            return self.config.text_url or self.config.base_url
        if kind == "image":
            return self.config.image_url or self.config.base_url
        if kind == "audio":
            return self.config.audio_url or self.config.base_url
        raise ValueError(kind)

    def _dry_text(self, goal: PlainGoalInput) -> TextResult:
        started = time.time()
        title = _title_for(goal.ordinary_goal, goal.theme)
        return TextResult(
            goal_id=goal.goal_id,
            ordinary_goal=goal.ordinary_goal,
            theme=goal.theme,
            title=title,
            narration=(
                f"Today, your real-world quest is to {goal.ordinary_goal}. "
                "Take it one small step at a time and show the finished mission."
            ),
            reward_label=_reward_for(goal.theme),
            steps=_steps_for(goal.ordinary_goal),
            text_prompt=(
                "Dry-run text placeholder for Epic Errands. "
                "No model, Modal endpoint, or network call was used."
            ),
            runtime_metadata=RuntimeMetadata(latency_ms=round((time.time() - started) * 1000)),
        )

    def _dry_image(self, request: ImageRequest) -> ImageResult:
        return ImageResult(
            goal_id=request.goal_id,
            request=request,
            prompt_summary=request.prompt,
            runtime_metadata=RuntimeMetadata(),
        )

    def _dry_audio(self, request: AudioRequest) -> AudioResult:
        return AudioResult(
            goal_id=request.goal_id,
            request=request,
            transcript_hint=request.spoken_text,
            runtime_metadata=RuntimeMetadata(),
        )


def _metadata_from_modal(result: dict[str, Any]) -> RuntimeMetadata:
    return RuntimeMetadata(
        lifecycle_stage=str(result.get("lifecycle_stage") or "testing"),
        app_host="hf_space" if os.environ.get("SPACE_ID") else "local",
        model_runtime=str(result.get("model_runtime") or "modal"),
        model_backend=str(result.get("model_backend") or "modal_http"),
        inference_engine=str(result.get("inference_engine") or "unknown"),
        model_artifact_format=str(result.get("model_artifact_format") or "unknown"),
        quantization=str(result.get("quantization") or "unknown"),
        model_id=str(result.get("model_id") or "unknown"),
        latency_ms=int(result.get("latency_ms") or 0),
        fallback_used=bool(result.get("fallback_used")),
    )


def _title_for(goal: str, theme: str) -> str:
    lowered = goal.lower()
    if "room" in lowered or "clean" in lowered:
        base = "The Tidy Treasure Quest"
    elif "read" in lowered:
        base = "The Reading Lantern Mission"
    elif "project" in lowered or "class" in lowered:
        base = "The Bright Ideas Expedition"
    else:
        base = "The Tiny Triumph Quest"
    if theme == "comic":
        return base.replace("Quest", "Action")
    if theme == "classroom":
        return base.replace("Quest", "Challenge")
    return base


def _reward_for(theme: str) -> str:
    return {
        "questbook": "Brave Helper Badge",
        "classroom": "Bright Ideas Star",
        "comic": "Everyday Hero Sticker",
    }.get(theme, "Brave Helper Badge")


def _steps_for(goal: str) -> list[str]:
    return [
        "Say the mission out loud.",
        "Gather the first thing you need.",
        f"Do the real-world task: {goal}.",
        "Show a parent or trusted grown-up when it is done.",
    ]
