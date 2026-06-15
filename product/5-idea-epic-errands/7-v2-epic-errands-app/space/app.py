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
from epic_errands_v2.generation import build_app_bootstrap, build_diy_state, build_generated_goal


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
            "live_generation": "disabled",
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
            build_generated_goal(
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
        for path in sorted((ASSETS_ROOT / "generated-v2").glob("*"))
        if path.is_file()
    }
    manifest["sc2-hero-scene-clean.png"] = _data_uri(ASSETS_ROOT / "sc2-hero-scene-clean.png")
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
    generated["provenance"] = {
        **generated.get("provenance", {}),
        "app_host": "hf_space_gradio_blocks",
        "model_runtime": "none",
        "model_backend": "static_review_asset",
        "backend_transport": "gradio_blocks_named_api",
        "api_name": "epic_generate_goal",
        "fallback_reason": "deterministic hosted dry-run; Modal/live model not wired to hosted app",
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
