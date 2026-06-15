# V2 Source Map

Status: fast-build lookup map. Use this file to find source files and avoid
redoing settled work. Do not read every linked artifact before building.

This map links prior artifacts. It does not turn prior evidence into V2 proof.
V2 proof still requires the matching V2 app, runtime, hosted Space, or UAT
workflow.

## Fast Build Use

Read first:

1. [UX flow](UX_FLOW.md)
2. [Implementation readiness](implementation-readiness.md)
3. [Locked model matrix](initial-inputs/models.md)
4. This file only for targeted source lookup

Skip broad product history, model discovery, deploy docs, and evidence
archaeology during the first implementation pass.

## V1 Files To Reuse

| Source | What To Reuse |
| --- | --- |
| [V1 visual design](../5-v1-epic-errands-app/design/visual-design.md) | Questbook default, Classroom/Comic support, must-preserve visual decisions. |
| [V1 style modes](../5-v1-epic-errands-app/design/style-modes.md) | Theme labels, parent/kid titles, reward names, copy tone, audio/image directions. |
| [V1 handoff](../5-v1-epic-errands-app/design/handoff.json) | Preserve `generated_theme_lens`, `generated_card_no_steps`, `playable_seed_audio`, `v2_seed_assets_packaged`, and `parent_kid_approval_loop` unless explicitly changed. |
| [V1 data contract](../5-v1-epic-errands-app/design/data-contract.json) | State/data structure source for implementation alignment. |
| [Static app JS](../5-v1-epic-errands-app/static/scripts/app.js) | Theme lens, generated variants, native audio controls, completion/approval actions. |
| [Space frontend JS](../5-v1-epic-errands-app/space/frontend/scripts/app.js) | Space-packaged copy of the visible frontend behavior. |
| [Token CSS](../5-v1-epic-errands-app/static/styles/tokens.css) | V1 theme token system. |
| [Component CSS](../5-v1-epic-errands-app/static/styles/components.css) | V1 reusable layout/control styling. |
| [App CSS](../5-v1-epic-errands-app/static/styles/app.css) | V1 screen-specific styling. |
| [Space app](../5-v1-epic-errands-app/space/app.py) | Custom UI served by `gradio.Server` with `/health`, `/api/bootstrap`, and `/api/quest-pack`. |

Packaged generated assets, if cached demo media is needed:

- [Static generated-v2 assets](../5-v1-epic-errands-app/static/assets/generated-v2)
- [Space generated-v2 assets](../5-v1-epic-errands-app/space/frontend/assets/generated-v2)

Do not confuse older `generated-hero-*` / `generated-audio-*` files with the
active 9 PNG + 9 WAV generated-v2 set.

## Personalized Image And Text Overlay

| Source | What To Reuse |
| --- | --- |
| [Add-elements README](../6-spike-add-elements-assets/README.md) | Base scene plates, reference portraits, direct-likeness hackathon caveat. |
| [Phase 0 spec and QA](../6-spike-add-elements-assets/phase-0-spec-and-qa.md) | Quality image size, required input dimensions, prompt contracts, QA checklist. |
| [Text overlay prototype](../6-spike-add-elements-assets/text-overlay-prototype/index.html) | App-owned overlay approach and theme-specific placement/font choices. |

Important image lesson: generated images can include unwanted text, blank
boards, or text containers. V2 should keep goal text as an app-owned editable
overlay and should not ask Review Goal to mutate generated pixels.

Product acceptance note: @cu reviewed the add-elements image spike and accepted
it as good enough for the fast V2 build, especially the outputs where parent
and child photos were added into the generated image. Do not pause the first
build pass for more image-model proof unless implementation is blocked.

## Text Generation

| Source | What To Reuse |
| --- | --- |
| [GGUF raw output](../6-spike-text-gen-check/evidence/speed_gguf_q4_raw_text.txt) | Raw output from `nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF`. |
| [Text Modal script](../6-spike-text-gen-check/modal_nemotron_text_compare.py) | Working Modal implementation for llama.cpp GGUF. |

V2 intentionally supersedes older model-mode labels: the text spike calls the
GGUF path `speed_gguf_q4`, but V2 uses that same GGUF/llama.cpp/Q4_K_M path for
Quality mode.

## Audio And Voice

| Source | What To Reuse |
| --- | --- |
| [VoxCPM2 voice script](../6-spike-voice-change/modal_voxcpm2_voice_clone.py) | Voice-generation/clone runner shape. |
| [Voice evidence JSON](../6-spike-voice-change/outputs/voxcpm2-voice-clone-evidence.json) | VoxCPM2 smoke on A10, `fallback_used=false`, three WAV outputs, and timing. |

V2 product contract: audio generation is enabled even without parent reference
audio. Current evidence proves VoxCPM2 generation with reference/sample voice
inputs and seeded playback; default/no-reference voice behavior should be
treated as an implementation contract until separately proved.

## DIY

| Source | What To Reuse |
| --- | --- |
| [DIY Modal spike README](../3-spike-diy-workflow-modal/README.md) | Curated plain-goal to text/image/audio/composed-output lab shape. |
| [DIY readiness](../3-spike-diy-workflow-modal/implementation-readiness.md) | Dry-run-first app contract and acceptance criteria. |
| [DIY contracts](../3-spike-diy-workflow-modal/epic_errands_diy_workflow/contracts.py) | Dataclass boundaries and JSON shape. |
| [DIY nodes](../3-spike-diy-workflow-modal/epic_errands_diy_workflow/nodes.py) | Node IDs and pipeline order. |
| [DIY modal client](../3-spike-diy-workflow-modal/epic_errands_diy_workflow/modal_client.py) | Dry-run default and future Modal URL boundary. |

V2 DIY should mirror the main generation flow, stay isolated inside the same app
package, use hardcoded flow data for the fast build, and label save-back-to-app
as coming soon.

## Optional Evidence Archive

Read only when making proof, evidence, or model-quality claims:

- [Generated-media UAT](../5-v1-epic-errands-app/evidence/v1-generated-media-uat.md)
- [V1 HF deploy evidence](../5-v1-epic-errands-app/evidence/v1-hf-space-deploy.md)
- [V1 visual pass](../5-v1-epic-errands-app/evidence/v1-visual-design-pass.md)
- [V1 local UAT](../5-v1-epic-errands-app/evidence/v1-local-uat.md)
- [FLUX visual QA](../6-spike-add-elements-assets/evidence/flux2-klein-quality-phases-20260615-060104/qa/visual_qa.md)
- [FLUX runtime summary](../6-spike-add-elements-assets/evidence/flux2-klein-quality-phases-20260615-060104/metadata/summary.json)
- [Text access preflight](../6-spike-text-gen-check/evidence/model_access_preflight.json)
- [Text run summary](../6-spike-text-gen-check/evidence/summary.json)

Do not claim public, hosted, model-backed, or judge-ready proof from linked
docs alone.

## Do Not Redo

- Do not re-run broad model discovery for V2. Start from
  [initial-inputs/models.md](initial-inputs/models.md) and the specific source
  links above.
- Do not switch V2 Quality text back to BF16 just because V1 model-selection
  called BF16 the old quality path. V2 intentionally uses Nemotron GGUF Q4 via
  llama.cpp for Quality mode.
- Do not use `llama.cpp` language for image GGUF paths. Text GGUF uses
  `llama.cpp`; image GGUF uses other runtimes such as QVAC, ComfyUI-GGUF,
  Diffusers GGUF, or `stable-diffusion.cpp`.
- Do not let generated images carry goal text. Use app-owned HTML/text overlay.
- Do not expose arbitrary model IDs or paid runtime knobs in the kid-facing app.
- Do not treat deterministic dry-run, cached assets, or private `/health` checks
  as sponsor/model, public, or judge-ready proof.
- Do not store uploaded parent/child photos or reference audio beyond the
  session/demo path unless @cu approves persistence.
