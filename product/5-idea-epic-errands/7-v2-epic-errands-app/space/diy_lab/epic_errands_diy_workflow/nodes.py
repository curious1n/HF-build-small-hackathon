from __future__ import annotations

import html
import time
from dataclasses import replace
from typing import Any

from .contracts import (
    AudioRequest,
    AudioResult,
    ContractError,
    ImageRequest,
    ImageResult,
    PlainGoalInput,
    RuntimeMetadata,
    TextResult,
    WorkflowOutput,
    from_json,
    normalize_theme,
    slugify,
    to_dict,
    to_json,
    validate_goal_text,
)
from .modal_client import ModalClient
from .trace import StatusStore


class WorkflowRunError(RuntimeError):
    def __init__(self, message: str, trace):
        super().__init__(message)
        self.trace = trace


def plain_goal_input(raw_goal: str, theme: str = "questbook", actor: str = "parent") -> PlainGoalInput:
    ordinary_goal = validate_goal_text(raw_goal)
    normalized_theme = normalize_theme(theme)
    return PlainGoalInput(
        goal_id=f"goal-{slugify(ordinary_goal)}",
        ordinary_goal=ordinary_goal,
        theme=normalized_theme,
        actor=(actor or "parent").strip() or "parent",
    )


def generate_text(goal: PlainGoalInput, client: ModalClient | None = None) -> TextResult:
    return (client or ModalClient()).generate_text(goal)


def build_image_request(text: TextResult) -> ImageRequest:
    card_text = {
        "title": text.title,
        "narration": text.narration,
        "reward_label": text.reward_label,
        "steps": list(text.steps),
    }
    prompt = (
        "Image placeholder request for an Epic Errands goal card. "
        f"Theme={text.theme}. Plain goal={text.ordinary_goal}. "
        "Future Modal image generation must avoid readable text, logos, scary "
        "imagery, user photo references, and unsafe behavior."
    )
    return ImageRequest(
        goal_id=text.goal_id,
        ordinary_goal=text.ordinary_goal,
        theme=text.theme,
        card_text=card_text,
        prompt=prompt,
        seed=26000 + len(text.ordinary_goal),
    )


def generate_image(text: TextResult, client: ModalClient | None = None) -> ImageResult:
    request = build_image_request(text)
    return (client or ModalClient()).generate_image(request)


def build_audio_request(text: TextResult) -> AudioRequest:
    spoken_text = f"{text.title}. {text.narration}"
    return AudioRequest(
        goal_id=text.goal_id,
        ordinary_goal=text.ordinary_goal,
        theme=text.theme,
        card_text={
            "title": text.title,
            "narration": text.narration,
            "reward_label": text.reward_label,
        },
        spoken_text=spoken_text,
        audio_prompt=(
            "Audio placeholder request for a friendly child-paced narration. "
            "Future Modal audio generation should speak only the card title and narration."
        ),
    )


def generate_audio(text: TextResult, client: ModalClient | None = None) -> AudioResult:
    request = build_audio_request(text)
    return (client or ModalClient()).generate_audio(request)


def compose_outputs(
    goal: PlainGoalInput,
    text: TextResult,
    image: ImageResult,
    audio: AudioResult,
    trace,
) -> WorkflowOutput:
    return WorkflowOutput(
        goal=goal,
        text=text,
        image_request=image.request,
        image=image,
        audio_request=audio.request,
        audio=audio,
        trace=trace,
    )


def run_dry_workflow(
    raw_goal: str,
    theme: str = "questbook",
    actor: str = "parent",
    client: ModalClient | None = None,
    run_id: str | None = None,
) -> WorkflowOutput:
    active_client = client or ModalClient()
    runtime_metadata = RuntimeMetadata(
        model_runtime="none" if active_client.config.dry_run else "modal",
        model_backend="template" if active_client.config.dry_run else "modal_http",
        fallback_used=False,
        model_id="none" if active_client.config.dry_run else active_client.config.model_id or "unknown",
    )
    store = StatusStore(
        run_id=run_id or f"diy-workflow-{int(time.time())}",
        runtime_metadata=runtime_metadata,
    )

    try:
        store.start("plain_goal_input", "Validating goal payload.")
        goal = plain_goal_input(raw_goal, theme, actor)
        store.done("plain_goal_input", "Goal accepted.")

        store.start("generate_text", "Preparing text node.")
        text = generate_text(goal, active_client)
        store.done("generate_text", "Text placeholder ready." if active_client.config.dry_run else "Text generated.")

        store.start("generate_image", "Preparing image node.")
        image = generate_image(text, active_client)
        store.done(
            "generate_image",
            "Image placeholder ready." if active_client.config.dry_run else "Image generated.",
        )

        store.start("generate_audio", "Preparing audio node.")
        audio = generate_audio(text, active_client)
        store.done(
            "generate_audio",
            "Audio placeholder ready." if active_client.config.dry_run else "Audio generated.",
        )

        store.start("compose_outputs", "Composing output bundle.")
        store.done("compose_outputs", "Workflow output composed.")
        return compose_outputs(goal, text, image, audio, store.snapshot())
    except Exception as exc:
        failed_node = _active_node(store)
        store.error(failed_node, f"{type(exc).__name__}: {exc}")
        raise WorkflowRunError(str(exc), store.snapshot()) from exc


def run_workflow_for_ui(raw_goal: str, theme: str, actor: str) -> dict[str, Any]:
    try:
        output = run_dry_workflow(raw_goal, theme, actor)
        return {
            "ok": True,
            "output": output,
            "trace": output.trace,
            "error": "",
        }
    except WorkflowRunError as exc:
        return {
            "ok": False,
            "output": None,
            "trace": exc.trace,
            "error": str(exc),
        }


def plain_goal_input_json(raw_goal: str, theme: str = "questbook", actor: str = "parent") -> str:
    return to_json(plain_goal_input(raw_goal, theme, actor))


def generate_text_json(goal_json: str) -> str:
    return to_json(generate_text(from_json(goal_json, PlainGoalInput)))


def generate_image_json(text_json: str) -> str:
    return to_json(generate_image(from_json(text_json, TextResult)))


def generate_audio_json(text_json: str) -> str:
    return to_json(generate_audio(from_json(text_json, TextResult)))


def compose_outputs_json(
    goal_json: str,
    text_json: str,
    image_json: str,
    audio_json: str,
) -> str:
    goal = from_json(goal_json, PlainGoalInput)
    text = from_json(text_json, TextResult)
    image = from_json(image_json, ImageResult)
    audio = from_json(audio_json, AudioResult)
    store = StatusStore("workflow-canvas-preview")
    for node_id in (
        "plain_goal_input",
        "generate_text",
        "generate_image",
        "generate_audio",
        "compose_outputs",
    ):
        store.start(node_id)
        store.done(node_id)
    return to_json(compose_outputs(goal, text, image, audio, store.snapshot()))


def output_summary_markdown(result: dict[str, Any]) -> str:
    if not result["ok"]:
        return f"**Status:** error\n\n`{html.escape(result['error'])}`"
    output: WorkflowOutput = result["output"]
    return (
        f"**Run label:** Local App Dry Run  \n"
        f"**Title:** {output.text.title}  \n"
        f"**Runtime:** model_runtime={output.trace.runtime_metadata.model_runtime}, "
        f"model_backend={output.trace.runtime_metadata.model_backend}, "
        f"fallback_used={str(output.trace.runtime_metadata.fallback_used).lower()}  \n"
        "**Modal:** not called in dry-run mode."
    )


def text_output_markdown(result: dict[str, Any]) -> str:
    if not result["ok"]:
        return "No text output."
    text: TextResult = result["output"].text
    steps = "\n".join(f"- {step}" for step in text.steps)
    return (
        f"### {text.title}\n\n"
        f"{text.narration}\n\n"
        f"**Reward:** {text.reward_label}\n\n"
        f"{steps}"
    )


def image_placeholder_html(result: dict[str, Any]) -> str:
    if not result["ok"]:
        return _placeholder("Image", "No image request was created.", "error")
    image: ImageResult = result["output"].image
    return _placeholder("Image", image.placeholder_label, image.request.theme)


def audio_placeholder_html(result: dict[str, Any]) -> str:
    if not result["ok"]:
        return _placeholder("Audio", "No audio request was created.", "error")
    audio: AudioResult = result["output"].audio
    return _placeholder("Audio", audio.placeholder_label, audio.request.theme)


def trace_json(result: dict[str, Any]) -> str:
    if result["ok"]:
        return to_json(result["output"])
    return to_json({"error": result["error"], "trace": to_dict(result["trace"])})


def status_table_markdown(result: dict[str, Any]) -> str:
    rows = [
        "| Node | State | Message | Latency |",
        "| --- | --- | --- | --- |",
    ]
    for status in result["trace"].statuses:
        rows.append(
            f"| {status.label} | {status.state} | {status.message or ''} | {status.latency_ms}ms |"
        )
    return "\n".join(rows)


def _active_node(store: StatusStore):
    trace = store.snapshot()
    for status in trace.statuses:
        if status.state == "generating":
            return status.node_id
    return "plain_goal_input"


def _placeholder(kind: str, message: str, theme: str) -> str:
    escaped = html.escape(message)
    theme_label = html.escape(theme.title())
    return f"""
<div class="diy-placeholder diy-placeholder-{html.escape(theme)}">
  <div class="diy-placeholder-kicker">{html.escape(kind)} placeholder</div>
  <div class="diy-placeholder-mark">{'IMG' if kind == 'Image' else 'AUD'}</div>
  <p>{escaped}</p>
  <span>{theme_label}</span>
</div>
"""
