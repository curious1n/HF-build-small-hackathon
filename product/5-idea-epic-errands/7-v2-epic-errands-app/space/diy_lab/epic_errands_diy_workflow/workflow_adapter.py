from __future__ import annotations

import inspect
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from .nodes import (
    compose_outputs_json,
    generate_audio_json,
    generate_image_json,
    generate_text_json,
    plain_goal_input_json,
)
from epic_errands_v2.generation import build_diy_state


@dataclass(frozen=True)
class WorkflowInspection:
    gradio_version: str
    has_workflow_module: bool
    has_workflow_class: bool
    workflow_signature: str
    module_file: str
    issues: list[str]

    @property
    def api_available(self) -> bool:
        return self.has_workflow_module and self.has_workflow_class


def inspect_workflow_api() -> WorkflowInspection:
    try:
        import gradio as gr
    except Exception as exc:
        return WorkflowInspection(
            gradio_version="unavailable",
            has_workflow_module=False,
            has_workflow_class=False,
            workflow_signature="",
            module_file="",
            issues=[f"Could not import gradio: {exc}"],
        )

    workflow_module = getattr(gr, "workflow", None)
    workflow_class = getattr(gr, "Workflow", None)
    issues: list[str] = []
    signature = ""
    if workflow_class is not None:
        try:
            signature = str(inspect.signature(workflow_class))
        except Exception as exc:
            issues.append(f"Could not inspect gr.Workflow signature: {exc}")
    if workflow_module is None:
        issues.append("gr.workflow module is not exposed.")
    if workflow_class is None:
        issues.append("gr.Workflow class is not exposed.")
    if workflow_class is not None and "bind" not in signature:
        issues.append("gr.Workflow signature does not expose bind=.")

    return WorkflowInspection(
        gradio_version=getattr(gr, "__version__", "unknown"),
        has_workflow_module=workflow_module is not None,
        has_workflow_class=workflow_class is not None,
        workflow_signature=signature,
        module_file=getattr(workflow_module, "__file__", "") if workflow_module else "",
        issues=issues,
    )


def workflow_bindings() -> dict[str, Callable]:
    return {
        "plain_goal_input": plain_goal_input_json,
        "generate_text": generate_text_json,
        "generate_image": generate_image_json,
        "generate_audio": generate_audio_json,
        "compose_outputs": compose_outputs_json,
    }


def workflow_edges() -> list[tuple[str, str]]:
    return [
        ("plain_goal_input", "generate_text"),
        ("generate_text", "generate_image"),
        ("generate_text", "generate_audio"),
        ("plain_goal_input", "compose_outputs.goal_json"),
        ("generate_text", "compose_outputs.text_json"),
        ("generate_image", "compose_outputs.image_json"),
        ("generate_audio", "compose_outputs.audio_json"),
    ]


def build_preview(ordinary_goal: str, selected_theme_id: str = "questbook") -> dict[str, object]:
    return build_diy_state(selected_theme_id, ordinary_goal)


def write_workflow_graph_preview(path: Path) -> dict:
    inspection = inspect_workflow_api()
    if not inspection.api_available:
        payload = {
            "available": False,
            "inspection": asdict(inspection),
            "graph": None,
        }
    else:
        import gradio.workflow as workflow

        builder = getattr(workflow, "_workflow_from_bind", None)
        if builder is None:
            payload = {
                "available": True,
                "inspection": asdict(inspection),
                "graph": None,
                "issue": "Private _workflow_from_bind helper unavailable; Workflow can still generate from bind=.",
            }
        else:
            graph_json = builder(
                workflow_bindings(),
                workflow_edges(),
                name="Epic Errands DIY Modal Dry Run",
            )
            payload = {
                "available": True,
                "inspection": asdict(inspection),
                "graph": json.loads(graph_json),
                "issue": "Graph preview uses Gradio's private _workflow_from_bind helper for evidence only.",
            }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def build_workflow_canvas_app(graph_path: Path):
    inspection = inspect_workflow_api()
    if not inspection.api_available:
        return None
    payload = write_workflow_graph_preview(graph_path.with_suffix(".preview.json"))
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    if not graph_path.exists():
        graph = payload.get("graph") or payload
        graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True), encoding="utf-8")
    import gradio as gr

    return gr.Workflow(
        graph=str(graph_path),
        bind=workflow_bindings(),
        edges=workflow_edges(),
    )
