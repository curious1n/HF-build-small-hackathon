from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Literal, get_args


Theme = Literal["questbook", "classroom", "comic"]
NodeState = Literal["pending", "generating", "done", "error"]
NodeId = Literal[
    "plain_goal_input",
    "generate_text",
    "generate_image",
    "generate_audio",
    "compose_outputs",
]

THEME_ALIASES = {
    "quest": "questbook",
    "questbook": "questbook",
    "magical": "questbook",
    "class": "classroom",
    "classroom": "classroom",
    "comic": "comic",
}


class ContractError(ValueError):
    """Raised when a workflow payload is not safe to run."""


@dataclass(frozen=True)
class RuntimeMetadata:
    lifecycle_stage: str = "dev"
    app_host: str = "local"
    model_runtime: str = "none"
    model_backend: str = "template"
    inference_engine: str = "none"
    model_artifact_format: str = "none"
    quantization: str = "none"
    model_id: str = "none"
    latency_ms: int = 0
    fallback_used: bool = False


@dataclass(frozen=True)
class PlainGoalInput:
    goal_id: str
    ordinary_goal: str
    theme: Theme = "questbook"
    actor: str = "parent"


@dataclass(frozen=True)
class TextResult:
    goal_id: str
    ordinary_goal: str
    theme: Theme
    title: str
    narration: str
    reward_label: str
    steps: list[str]
    text_prompt: str
    runtime_metadata: RuntimeMetadata = field(default_factory=RuntimeMetadata)


@dataclass(frozen=True)
class ImageRequest:
    goal_id: str
    ordinary_goal: str
    theme: Theme
    card_text: dict[str, Any]
    prompt: str
    width: int = 768
    height: int = 768
    seed: int = 26000


@dataclass(frozen=True)
class ImageResult:
    goal_id: str
    request: ImageRequest
    asset_kind: str = "placeholder"
    artifact_uri: str = ""
    placeholder_label: str = "Image placeholder: Modal generation not run."
    prompt_summary: str = ""
    runtime_metadata: RuntimeMetadata = field(default_factory=RuntimeMetadata)


@dataclass(frozen=True)
class AudioRequest:
    goal_id: str
    ordinary_goal: str
    theme: Theme
    card_text: dict[str, Any]
    spoken_text: str
    audio_prompt: str


@dataclass(frozen=True)
class AudioResult:
    goal_id: str
    request: AudioRequest
    asset_kind: str = "placeholder"
    artifact_uri: str = ""
    placeholder_label: str = "Audio placeholder: Modal generation not run."
    transcript_hint: str = ""
    runtime_metadata: RuntimeMetadata = field(default_factory=RuntimeMetadata)


@dataclass(frozen=True)
class NodeStatus:
    node_id: NodeId
    label: str
    state: NodeState = "pending"
    message: str = ""
    started_at: float | None = None
    ended_at: float | None = None
    latency_ms: int = 0


@dataclass(frozen=True)
class RunTrace:
    run_id: str
    statuses: list[NodeStatus]
    events: list[dict[str, Any]]
    runtime_metadata: RuntimeMetadata


@dataclass(frozen=True)
class WorkflowOutput:
    goal: PlainGoalInput
    text: TextResult
    image_request: ImageRequest
    image: ImageResult
    audio_request: AudioRequest
    audio: AudioResult
    trace: RunTrace


def normalize_theme(value: str | None) -> Theme:
    normalized = (value or "questbook").strip().lower()
    theme = THEME_ALIASES.get(normalized)
    if theme not in get_args(Theme):
        raise ContractError(f"Unsupported theme: {value!r}")
    return theme  # type: ignore[return-value]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48] or "goal"


def validate_goal_text(value: str) -> str:
    compact = " ".join((value or "").strip().split())
    if not compact:
        raise ContractError("Plain goal is required.")
    if len(compact) > 240:
        raise ContractError("Plain goal must be 240 characters or fewer.")
    return compact


def to_dict(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    return value


def to_json(value: Any) -> str:
    return json.dumps(to_dict(value), indent=2, sort_keys=True)


def _metadata(data: dict[str, Any] | None) -> RuntimeMetadata:
    return RuntimeMetadata(**(data or {}))


def _image_request(data: dict[str, Any]) -> ImageRequest:
    return ImageRequest(**data)


def _audio_request(data: dict[str, Any]) -> AudioRequest:
    return AudioRequest(**data)


def from_json(payload: str | dict[str, Any], cls: type) -> Any:
    data = json.loads(payload) if isinstance(payload, str) else payload
    if cls is RuntimeMetadata:
        return _metadata(data)
    if cls is PlainGoalInput:
        return PlainGoalInput(**data)
    if cls is TextResult:
        return TextResult(
            **{**data, "runtime_metadata": _metadata(data.get("runtime_metadata"))}
        )
    if cls is ImageRequest:
        return _image_request(data)
    if cls is ImageResult:
        return ImageResult(
            **{
                **data,
                "request": _image_request(data["request"]),
                "runtime_metadata": _metadata(data.get("runtime_metadata")),
            }
        )
    if cls is AudioRequest:
        return _audio_request(data)
    if cls is AudioResult:
        return AudioResult(
            **{
                **data,
                "request": _audio_request(data["request"]),
                "runtime_metadata": _metadata(data.get("runtime_metadata")),
            }
        )
    if cls is NodeStatus:
        return NodeStatus(**data)
    if cls is RunTrace:
        return RunTrace(
            run_id=data["run_id"],
            statuses=[from_json(item, NodeStatus) for item in data.get("statuses", [])],
            events=list(data.get("events", [])),
            runtime_metadata=_metadata(data.get("runtime_metadata")),
        )
    if cls is WorkflowOutput:
        return WorkflowOutput(
            goal=from_json(data["goal"], PlainGoalInput),
            text=from_json(data["text"], TextResult),
            image_request=from_json(data["image_request"], ImageRequest),
            image=from_json(data["image"], ImageResult),
            audio_request=from_json(data["audio_request"], AudioRequest),
            audio=from_json(data["audio"], AudioResult),
            trace=from_json(data["trace"], RunTrace),
        )
    raise TypeError(f"Unsupported contract type: {cls!r}")
