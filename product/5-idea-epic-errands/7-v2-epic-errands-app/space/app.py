from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any

from fastapi import Body
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import gradio as gr
from gradio.workflow import WRITE_TOKEN
from gradio import Server

from diy_lab.epic_errands_diy_workflow.workflow_adapter import build_workflow_canvas_app
from epic_errands_v2.generation import (
    build_app_bootstrap,
    build_diy_state,
    build_generated_goal,
    build_generated_goal_with_live_fallback,
)


ROOT = Path(__file__).resolve().parent
FRONTEND_ROOT = ROOT / "frontend"
ASSETS_ROOT = FRONTEND_ROOT / "assets"
DIY_FRONTEND_ROOT = ROOT / "diy_lab" / "frontend"
DIY_WORKFLOW_GRAPH_PATH = ROOT / "diy_lab" / "workflow.json"
LOCAL_WORKFLOW_WRITE_COOKIE = "gradio_workflow_write_token_epic_errands_v2"


def build_server() -> Server:
    app = Server(
        title="Epic Errands V2",
        description="A local V2 mobile UI served by a Gradio-compatible Server.",
        docs_url=None,
        redoc_url=None,
    )

    app.mount("/frontend", StaticFiles(directory=FRONTEND_ROOT), name="frontend")
    app.mount("/epic", StaticFiles(directory=FRONTEND_ROOT), name="epic_frontend")
    app.mount("/assets", StaticFiles(directory=ASSETS_ROOT), name="assets")
    app.mount("/diy-assets", StaticFiles(directory=DIY_FRONTEND_ROOT), name="diy_assets")
    app.mount("/epic-diy", StaticFiles(directory=DIY_FRONTEND_ROOT), name="epic_diy_assets")
    workflow_app = build_workflow_canvas_app(DIY_WORKFLOW_GRAPH_PATH)
    if workflow_app is not None:
        gr.mount_gradio_app(
            app,
            workflow_app,
            path="/diy-workflow",
            footer_links=[],
            show_error=True,
        )

    @app.get("/")
    async def homepage() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "index.html")

    def diy_file_response() -> FileResponse:
        response = FileResponse(DIY_FRONTEND_ROOT / "index.html")
        if not os.environ.get("SPACE_ID"):
            response.set_cookie(
                LOCAL_WORKFLOW_WRITE_COOKIE,
                WRITE_TOKEN,
                path="/",
                httponly=True,
                samesite="lax",
            )
        return response

    @app.get("/diy")
    async def diy_homepage() -> FileResponse:
        return diy_file_response()

    @app.get("/diy/")
    async def diy_homepage_slash() -> FileResponse:
        return diy_file_response()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "app": "epic-errands-v2",
            "frontend": "fully-custom-ui",
            "version": "v2",
            "proof_claim": "local_implementation_only",
            "live_generation": _live_generation_label(),
            "quality_text_model": "nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF",
            "quality_image_model": "black-forest-labs/FLUX.2-klein-9B",
            "quality_audio_model": "openbmb/VoxCPM2",
            "space_id": "set" if os.environ.get("SPACE_ID") else "missing",
        }

    @app.get("/api/bootstrap")
    async def bootstrap() -> JSONResponse:
        return JSONResponse(build_app_bootstrap())

    @app.post("/api/generate-goal")
    async def generate_goal(payload: dict[str, Any] = Body(default_factory=dict)) -> JSONResponse:
        return JSONResponse(
            build_generated_goal_with_live_fallback(
                str(payload.get("ordinary_goal") or ""),
                str(
                    payload.get("ui_theme_id")
                    or payload.get("theme_id_at_creation")
                    or payload.get("theme_id")
                    or "questbook"
                ),
                selected_generation_reference_ids=[
                    str(item) for item in payload.get("selected_generation_reference_ids", []) if str(item).strip()
                ],
                audio_used_parent_reference=bool(payload.get("audio_used_parent_reference")),
            )
        )

    @app.post("/api/diy-preview")
    async def diy_preview(payload: dict[str, Any] = Body(default_factory=dict)) -> JSONResponse:
        return JSONResponse(
            build_diy_state(
                str(payload.get("theme_id") or payload.get("selected_theme_id") or "questbook"),
                str(payload.get("ordinary_goal") or ""),
                selected_generation_reference_ids=[
                    str(item) for item in payload.get("selected_generation_reference_ids", []) if str(item).strip()
                ],
            )
        )

    return app


def build_hosted_demo() -> gr.Blocks:
    """HF Gradio SDK entrypoint: render the custom UI without an iframe."""
    with gr.Blocks(
        title="Epic Errands V2",
    ) as demo:
        gr.HTML(
            value=_hosted_html(),
            elem_id="epic-hosted-shell",
            container=False,
            padding=False,
            js_on_load=_hosted_js(),
        )
        backend_request = gr.Textbox(visible=False, container=False, label="Backend request")
        backend_response = gr.Textbox(visible=False, container=False, label="Backend response")
        gr.Button("Bootstrap", visible=False).click(
            fn=_hosted_bootstrap,
            inputs=backend_request,
            outputs=backend_response,
            api_name="epic_bootstrap",
            show_progress="hidden",
            queue=True,
        )
        gr.Button("Generate Goal", visible=False).click(
            fn=_hosted_generate_goal,
            inputs=backend_request,
            outputs=backend_response,
            api_name="epic_generate_goal",
            show_progress="hidden",
            queue=True,
        )
        gr.Button("DIY Preview", visible=False).click(
            fn=_hosted_diy_preview,
            inputs=backend_request,
            outputs=backend_response,
            api_name="epic_diy_preview",
            show_progress="hidden",
            queue=True,
        )
    return demo


def _hosted_css() -> str:
    css = "\n".join(
        [
            (FRONTEND_ROOT / "styles" / "tokens.css").read_text(encoding="utf-8"),
            (FRONTEND_ROOT / "styles" / "components.css").read_text(encoding="utf-8"),
            (FRONTEND_ROOT / "styles" / "app.css").read_text(encoding="utf-8"),
            (DIY_FRONTEND_ROOT / "styles" / "diy.css").read_text(encoding="utf-8"),
        ]
    )
    hosted_overrides = (
        ":root{color-scheme:light;}"
        "html,body{background:#f4f5f7!important;color-scheme:light!important;}"
        "gradio-app,.gradio-container{color-scheme:light!important;}"
        ".gradio-container{max-width:none!important;padding:0!important;background:#f4f5f7!important;color:#353a42!important;}"
        ".dark .gradio-container,.gradio-container.dark{background:#f4f5f7!important;color:#353a42!important;}"
        "footer{display:none!important;}"
        "#epic-hosted-shell{padding:0!important;margin:0!important;background:var(--page-bg)!important;color:var(--body-color)!important;}"
        "#epic-hosted-shell .card,#epic-hosted-shell .card-inner{color:var(--body-color)!important;font-family:var(--font-body)!important;}"
        "#epic-hosted-shell .wordmark .display,#epic-hosted-shell .lead h1,#epic-hosted-shell .panel-head h2,#epic-hosted-shell .section__title,#epic-hosted-shell .parent__head h3,#epic-hosted-shell .field .big,#epic-hosted-shell .field .pts,#epic-hosted-shell .kidnote b{color:var(--heading-color)!important;font-family:var(--font-display)!important;}"
        "#epic-hosted-shell .wordmark .sub,#epic-hosted-shell .lead p,#epic-hosted-shell .panel-head span,#epic-hosted-shell .section__sub,#epic-hosted-shell .empty-line,#epic-hosted-shell .kidnote,#epic-hosted-shell .foot{color:var(--muted-color)!important;font-family:var(--font-body)!important;}"
        "#epic-hosted-shell .tab-btn{background:var(--panel-bg)!important;color:var(--muted-color)!important;border-color:var(--panel-border-color)!important;font-family:var(--font-body)!important;font-size:11px!important;font-weight:850!important;}"
        "#epic-hosted-shell .tab-btn[aria-pressed='true']{background:var(--accent-soft)!important;color:var(--accent-ink)!important;border-color:var(--accent)!important;}"
        "#epic-hosted-shell .tab-btn b{background:var(--reward)!important;color:#17120c!important;}"
        "#epic-hosted-shell .seg-btn,#epic-hosted-shell .mode-btn,#epic-hosted-shell .ref-chip{background:var(--field-bg)!important;color:var(--field-fg)!important;border-color:var(--field-border-color)!important;font-family:var(--font-body)!important;font-weight:850!important;}"
        "#epic-hosted-shell .seg-btn[aria-pressed='true'],#epic-hosted-shell .mode-btn[aria-pressed='true'],#epic-hosted-shell .ref-chip[aria-pressed='true']{background:var(--accent-soft)!important;color:var(--accent-ink)!important;border-color:var(--accent)!important;}"
        "#epic-hosted-shell .btn-primary{background:var(--primary)!important;color:var(--primary-text)!important;border:0!important;font-family:var(--font-display)!important;font-weight:var(--display-weight)!important;text-transform:var(--display-transform)!important;letter-spacing:var(--display-tracking)!important;box-shadow:var(--primary-shadow)!important;}"
        "#epic-hosted-shell .btn-ghost,#epic-hosted-shell .field__input,#epic-hosted-shell .upload-chip{background:var(--field-bg)!important;color:var(--field-fg)!important;border-color:var(--field-border-color)!important;font-family:var(--font-body)!important;}"
        "#epic-hosted-shell .tab-btn span,#epic-hosted-shell .tab-btn svg,#epic-hosted-shell .seg-btn span,#epic-hosted-shell .mode-btn span,#epic-hosted-shell .ref-chip span,#epic-hosted-shell .ref-chip small,#epic-hosted-shell .btn-primary span,#epic-hosted-shell .btn-primary svg,#epic-hosted-shell .btn-ghost span,#epic-hosted-shell .btn-ghost svg,#epic-hosted-shell .upload-chip span{color:inherit!important;}"
        "#epic-hosted-shell .quest-headline .eyebrow{color:var(--banner-text)!important;font-family:var(--font-display)!important;}"
        "#epic-hosted-shell .quest-headline .quest-title{color:var(--quest-title-color)!important;font-family:var(--font-display)!important;}"
    )
    return (
        hosted_overrides
        + css
        + hosted_overrides
    )


def _hosted_html() -> str:
    return f'<style>{_hosted_css()}</style><main class="stage" aria-label="Epic Errands V2"><div id="app"></div></main>'


def _hosted_js() -> str:
    js = (FRONTEND_ROOT / "scripts" / "app.js").read_text(encoding="utf-8")
    manifest = {
        str(path.relative_to(ASSETS_ROOT)): _data_uri(path)
        for path in sorted(ASSETS_ROOT.rglob("*"))
        if path.is_file()
    }
    bootstrap = (
        "window.EPIC_ASSET_BASE = '';"
        "window.EPIC_EMBEDDED_SPACE_MODE = true;"
        "window.EPIC_GRADIO_API_PREFIX = '/gradio_api';"
        f"window.EPIC_ASSET_MANIFEST = {json.dumps(manifest, separators=(',', ':'))};"
    )
    return bootstrap + "\n" + js


def _decode_request(payload_json: str | None) -> dict[str, Any]:
    if not payload_json:
        return {}
    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _hosted_bootstrap(payload_json: str | None = None) -> str:
    payload = build_app_bootstrap()
    payload["backend_bridge"] = {
        "transport": "gradio_blocks_named_api",
        "bootstrap_endpoint": "epic_bootstrap",
        "generate_endpoint": "epic_generate_goal",
        "diy_preview_endpoint": "epic_diy_preview",
        "model_runtime": "none",
        "model_backend": "static_review_asset",
        "fallback_used": True,
    }
    return json.dumps(payload, separators=(",", ":"))


def _hosted_generate_goal(payload_json: str | None = None) -> str:
    payload = _decode_request(payload_json)
    generated = build_generated_goal(
        str(payload.get("ordinary_goal") or ""),
        str(
            payload.get("ui_theme_id")
            or payload.get("theme_id_at_creation")
            or payload.get("theme_id")
            or "questbook"
        ),
        selected_generation_reference_ids=[
            str(item) for item in payload.get("selected_generation_reference_ids", []) if str(item).strip()
        ],
        audio_used_parent_reference=bool(payload.get("audio_used_parent_reference")),
    )
    fallback_used = bool(generated.get("provenance", {}).get("fallback_used", True))
    generated["provenance"] = {
        **generated.get("provenance", {}),
        "app_host": "hf_space_gradio_blocks",
        "model_runtime": generated.get("provenance", {}).get("model_runtime") or ("none" if fallback_used else "modal"),
        "model_backend": generated.get("provenance", {}).get("model_backend") or ("static_review_asset" if fallback_used else "modal_http"),
        "backend_transport": "gradio_blocks_named_api",
        "api_name": "epic_generate_goal",
        "fallback_reason": generated.get("provenance", {}).get("fallback_reason")
        or (
            "partial fallback; see modal_runtime_steps"
            if fallback_used and generated.get("provenance", {}).get("model_runtime") == "modal"
            else "deterministic hosted dry-run; Modal/live generation disabled or unavailable"
            if fallback_used
            else ""
        ),
    }
    return json.dumps(generated, separators=(",", ":"))


def _hosted_diy_preview(payload_json: str | None = None) -> str:
    payload = _decode_request(payload_json)
    preview = build_diy_state(
        str(payload.get("theme_id") or payload.get("selected_theme_id") or "questbook"),
        str(payload.get("ordinary_goal") or ""),
        selected_generation_reference_ids=[
            str(item) for item in payload.get("selected_generation_reference_ids", []) if str(item).strip()
        ],
    )
    preview["backend_bridge"] = {
        "transport": "gradio_blocks_named_api",
        "api_name": "epic_diy_preview",
        "model_runtime": "none",
        "model_backend": "static_review_asset",
        "fallback_used": True,
    }
    return json.dumps(preview, separators=(",", ":"))


def _data_uri(path: Path) -> str:
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _live_generation_label() -> str:
    if os.environ.get("EPIC_ENABLE_LIVE_GENERATION", "").strip().lower() in {"1", "true", "yes"}:
        return "enabled"
    if os.environ.get("APP_DRY_RUN", "true").strip().lower() in {"0", "false", "no"}:
        return "enabled"
    return "disabled"


server = build_server()
app = build_hosted_demo()


if __name__ == "__main__":
    launch_target = app if os.environ.get("SPACE_ID") else server
    launch_target.launch(
        server_name=os.environ.get("HOST", "0.0.0.0"),
        server_port=int(os.environ.get("PORT", "7860")),
        footer_links=[],
        show_error=True,
    )
