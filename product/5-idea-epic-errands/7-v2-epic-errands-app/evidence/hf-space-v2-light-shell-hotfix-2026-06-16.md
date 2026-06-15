# Epic Errands V2 Light Shell Hotfix

Date: 2026-06-16

## Scope

- Fix the private HF Space rendering with a black hosted background.
- Preserve the fully custom Gradio `gr.HTML` shell and named backend APIs.
- Do not claim public release, judge-ready status, or hosted live-model proof.

## Cause

The hosted Gradio wrapper in `space/app.py` explicitly set:

```css
.gradio-container { background: #111 !important; }
```

This made the Space look like it was inheriting dark mode. In local/browser
proof, Gradio still set `body.className = "dark"`, but the issue was the app's
own hosted override.

## Fix

- Replaced the black Gradio wrapper override with light shell overrides.
- Added `color-scheme: light` to the hosted shell and standalone HTML/CSS path.
- Kept the app's named visual themes intact, including the intentional Comic
  theme styling.

## Local Proof

Run label: Local App Dry Run

- URL: `http://127.0.0.1:7867/`
- Entry point: `app = build_hosted_demo()` via `space/app.py`
- `body.className`: `dark`
- `body` background: `rgb(244, 245, 247)`
- `.gradio-container` background: `rgb(244, 245, 247)`
- `color-scheme`: `light`
- Parent tab opened.
- Generate Goal showed `Generating...`.
- Review Goal appeared.

Checks:

```bash
node --check product/5-idea-epic-errands/7-v2-epic-errands-app/space/frontend/scripts/app.js
PYTHONPYCACHEPREFIX=/private/tmp/epic-errands-v2-pycache python3 -m compileall -q product/5-idea-epic-errands/7-v2-epic-errands-app/space
PYTHONPYCACHEPREFIX=/private/tmp/epic-errands-v2-pycache PYTHONPATH=product/5-idea-epic-errands/7-v2-epic-errands-app/space SPACE_ID=local-test .venv/bin/python -c "import app; css=app._hosted_css(); print(type(app.app).__name__); print('#111' in css); print('color-scheme:light' in css); print('background:#f4f5f7' in css)"
```

Import/CSS check output:

```text
Blocks
False
True
True
```

## Hosted Proof

Run label: Hosted Space Dry Run

- Space repo: `build-small-hackathon/epic-errands`
- Space URL: `https://build-small-hackathon-epic-errands.hf.space/`
- namespace env: `HF_HACKATHON`
- upload actor/token env: `HF_2` / `HF_TOKEN_2`
- lifecycle stage: `testing`
- SDK: Gradio
- hardware: `cpu-basic`
- visibility: private
- deployed SHA: `8173b0bf0de9c8c2bb109320d5f8aae1e98f9484`

Hosted `/config` proof:

```json
{
  "api_names": ["epic_bootstrap", "epic_generate_goal", "epic_diy_preview"],
  "has_light_override": true,
  "has_old_black": false,
  "html_component_count": 1,
  "runtime_stage": "RUNNING"
}
```

Hosted named API smoke:

```json
{
  "backend_transport": "gradio_blocks_named_api",
  "event_id_present": true,
  "fallback_used": true,
  "model_backend": "static_review_asset",
  "model_runtime": "none",
  "title": "Quest: Small Brave Step"
}
```

## Boundary

This proves the private hosted deterministic Gradio app was hotfixed for the
black hosted shell issue. It does not prove hosted Modal/live model execution.
