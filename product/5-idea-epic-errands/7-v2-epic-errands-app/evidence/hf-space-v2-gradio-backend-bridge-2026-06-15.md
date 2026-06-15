# HF Space V2 Gradio Backend Bridge Check

Date: 2026-06-15

Status: pass for private hosted Gradio named-API smoke.

Space:

- Repo: `build-small-hackathon/epic-errands`
- URL: `https://build-small-hackathon-epic-errands.hf.space/`
- Namespace env: `HF_HACKATHON`
- Token env: `HF_TOKEN_2`
- Visibility: private
- SDK: Gradio
- Hardware: `cpu-basic`
- Observed SHA: `36d237625793c842601ec3209f6a255fa9e82060`

What changed:

- The HF entrypoint remains `gr.Blocks`, preserving the fully-custom HTML/CSS/JS surface inside Gradio.
- Hosted mode now exposes Gradio named APIs:
  - `epic_bootstrap`
  - `epic_generate_goal`
  - `epic_diy_preview`
- The custom frontend calls `/gradio_api/call/<api_name>` in embedded Space mode instead of relying on FastAPI `/api/*` routes that are not served by the HF `Blocks` entrypoint.
- The Generate Goal button shows a visible generating state and a backend status line.
- Browser fallback remains available but is no longer silent.

Local HF-parity browser proof:

- Started the app with `SPACE_ID=local-test` so the same `Blocks` object used by HF was served locally.
- Browser flow:
  - Opened Parent tab.
  - Clicked Generate Goal.
  - Observed disabled `Generating...` button.
  - Observed status: `Backend Generating through the hosted Gradio backend...`
  - Observed final status: `Backend Generated through gradio_blocks_named_api; fallback_used=true.`
  - Observed Review Goal screen.
- Console errors/warnings: none.

Hosted proof:

- `/config` returned `mode=blocks`.
- `/config` contained `epic_bootstrap`, `epic_generate_goal`, and `epic_diy_preview`.
- Authenticated hosted call to `/gradio_api/call/epic_generate_goal` returned HTTP 200 and a generated goal.
- Returned provenance:
  - `backend_transport=gradio_blocks_named_api`
  - `model_runtime=none`
  - `model_backend=static_review_asset`
  - `fallback_used=true`
  - `fallback_reason=deterministic hosted dry-run; Modal/live model not wired to hosted app`

Proof boundary:

- This is not hosted live-model proof.
- This is not public release proof.
- This is not judge-ready proof.
- This is not full private hosted browser UAT.
