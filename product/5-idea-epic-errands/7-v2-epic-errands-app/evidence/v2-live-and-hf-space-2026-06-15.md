# Epic Errands V2 Live Model And Private HF Space Proof

Date: 2026-06-15 IST

## Scope

Claimed:

- One local V2 Modal-backed live model smoke completed with `fallback_used=false`.
- Private HF Space package uploaded to `build-small-hackathon/epic-errands`.
- Private hosted Gradio config serves the Epic Errands V2 embedded app component.

Not claimed:

- public release;
- judge-ready proof;
- hosted live model execution;
- full browser proof of the private hosted Space;
- final hackathon submission.

## Live Model Smoke

- Run label: `Local App With Modal`
- Evidence: `evidence/live-model-smoke-2026-06-15/summary.json`
- Preflight: `evidence/live-model-smoke-2026-06-15/model_access_preflight.json`
- Approved budget: `$20`
- Max runtime: 20 minutes
- Stop condition: one schema-valid V2 row, first blocker, 20 wall-clock minutes, or `$20` spend
- Result: `fallback_used=false`

Runtime axes:

- Text: `nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF`, Modal, `llama.cpp`, GGUF, `q4_k_m`
- Image: `black-forest-labs/FLUX.2-klein-9B`, Modal, Diffusers, safetensors, `bf16`
- Audio: `openbmb/VoxCPM2`, Modal, `voxcpm`, safetensors, `bf16`

## Private HF Space

- Space repo id: `build-small-hackathon/epic-errands`
- Space URL: `https://build-small-hackathon-epic-errands.hf.space/`
- Namespace env: `HF_HACKATHON`
- Upload actor env: `HF_2`
- Token env: `HF_TOKEN_2`
- SDK: Gradio
- Hardware: `cpu-basic`
- Visibility: private
- Lifecycle stage: hosted testing
- Evidence: `evidence/hf-space-v2-deploy-check.json`

Hosted proof status:

- `hosted_gradio_config_passed=true`
- Runtime SHA observed: `e643b7b68389ce91e810f3c345407639ab55c40a`
- Config title: `Epic Errands V2`
- Embedded component includes `epic-iframe` and `Epic Errands V2`

## Notes

- The hosted package uses deterministic/cached review assets.
- Live model proof was direct local-to-Modal smoke, not an HF Space-to-Modal smoke.
- The Space startup uses an embedded Gradio app for private hosted testing because
  HF Gradio hosting did not expose the custom `gradio.Server` routes reliably.
