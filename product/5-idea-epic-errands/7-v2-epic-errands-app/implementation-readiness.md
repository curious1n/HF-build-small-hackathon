# Implementation Readiness

Status: V2 contract for a fast build-and-verify pass. This file records locked
decisions and does not claim implementation has started.

Read [SOURCE_MAP.md](SOURCE_MAP.md) before implementation. It is the source map
for prior product docs, V1 anchors, spikes, reusable evidence, proof caveats,
and do-not-redo lessons.

## Product Decision

Epic Errands V2 is a mobile-first app for parents and children. Parents turn an
ordinary goal into a generated goal card, review it, then publish it for the
child. Children complete goals, and parents approve rewards.

V2 optimizes for a fast hackathon build and verification pass:

- preserve the V1 visual system;
- enable Quality mode only;
- avoid spending time reproving models that already have enough spike evidence;
- keep model/runtime provenance visible but concise;
- isolate DIY while keeping it in the same app package.
- keep app UI styling independent from generation mode and from already
  accepted generated assets.

## UX Decision

Primary tabs:

- Home
- Parent Goals
- Kid Goals
- Settings
- DIY

Primary flow:

1. Parent configures theme, photos, optional parent reference audio, child
   photos, and generation mode in Settings.
2. Parent creates an ordinary goal in Parent Goals.
3. Parent chooses parent/child/custom image references for generation.
4. The app generates text, image, and audio in Quality mode.
5. Parent reviews the generated goal.
6. Parent edits the app-owned text layer if needed.
7. Parent accepts or cancels the generated goal.
8. Accepted goals appear in Kid Goals.
9. Kid completes a goal.
10. Parent approves the reward.

Review Goal rules:

- Parent can edit the visible goal text layer over the generated image.
- Parent can accept the generated goal.
- Parent can cancel the generated goal.
- Parent cannot change the generated image from Review Goal.
- Parent cannot change the generated audio from Review Goal.
- Text-layer edits do not alter image pixels or regenerate audio.

Audio rules:

- Audio generation is enabled in V2.
- Parent reference audio is optional.
- If a reference audio file exists, it may be used for parent-voice generation.
- If no reference audio exists, audio still generates with the default voice
  behavior.

Styling and generation rules:

- App UI styling controls the shell, copy tone, and overlay styling.
- App UI styling is independent from generation mode and model selection.
- Changing the app theme after a goal is accepted should not regenerate or
  mutate that goal's image or audio.
- Generation references selected for a run are the inputs to image generation.

DIY rules:

- DIY mirrors the same app generation pipeline.
- DIY is isolated in its own folder inside the same app package.
- DIY uses hardcoded flow data for the fast build.
- DIY lets the parent edit workflow draft fields and see local preview/trace
  changes.
- Saving/updating the main app from DIY is a coming soon feature.

## Design Decision

Use the V1 visual styling without a new visual exploration pass.

Authoritative V1 sources:

- `SOURCE_MAP.md`
- `../5-v1-epic-errands-app/design/style-modes.md`
- `../5-v1-epic-errands-app/design/visual-design.md`
- `../5-v1-epic-errands-app/design/handoff.json`
- `../5-v1-epic-errands-app/design/implementation-trace.md`
- `../5-v1-epic-errands-app/static/styles/`

V2 should keep:

- V1 must-preserve anchors from `design/handoff.json`, especially
  `generated_theme_lens`, `generated_card_no_steps`, `playable_seed_audio`,
  `v2_seed_assets_packaged`, and `parent_kid_approval_loop`;
- Questbook as a supported/default app theme unless @cu changes it during the
  build;
- Classroom and Comic as selectable app styling;
- mobile-first 390px target;
- parent/kid approval loop from V1;
- generated media card feeling from V1.

## Tech Decision

App host:

- Gradio-compatible Space package.
- Custom frontend remains the visible product surface.
- Use V1 `gradio.Server` style unless a blocker appears during build.

Generation mode:

- `quality` is enabled.
- `speed` is disabled/planned for hackathon.
- Quality mode uses 1024 x 1024 image output.
- Planned Speed mode uses 720 x 720 image output.

Quality model matrix:

| Capability | Model/runtime |
| --- | --- |
| Text / quest JSON | `nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF`, `llama.cpp`, GGUF, `Q4_K_M` |
| Image | `black-forest-labs/FLUX.2-klein-9B`, Diffusers, safetensors, `bf16`, 1024 x 1024 |
| Audio | `openbmb/VoxCPM2`, `voxcpm`, safetensors, `bf16` |

Text model override:

- V1 model-selection proposed BF16/vLLM as the old quality text path.
- V2 intentionally uses `nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF` with
  `llama.cpp`, GGUF, `Q4_K_M` for Quality mode.
- The older text spike labels that GGUF path `speed_gguf_q4`; for V2 it is the
  selected Quality text path.

ASR note:

- ASR models remain in `initial-inputs/models.md` as available pipeline/eval
  context.
- ASR is not required for the fast parent/kid V2 UX unless the build chooses to
  show transcript/QA evidence.

Speed model matrix:

- Keep the model contract from `initial-inputs/models.md`.
- Speed mode remains disabled/planned in the V2 app.

Prior evidence:

- Treat source-map evidence as reusable planning context, not V2 proof.
- Do not spend time reproving models during the fast build unless the app
  cannot be implemented or verified without a narrow smoke.
- Treat @cu's review of the add-elements image spike as sufficient product
  acceptance for the fast build, especially the outputs where photos were added
  into the image.
- Do not make public, hosted, model-backed, or judge-ready claims without the
  matching workflow lane and evidence.

Secrets:

- Use env var names only in docs/UI.
- Never print token values.
- Paid runtime, public release, or final submission still requires @cu
  approval.

## Build Decision

Start from relevant V1 files only:

- `space/app.py`
- `space/requirements.txt`
- `space/frontend/`
- `space/epic_errands_space/` as a reference for adapters/contracts
- `static/` only when useful for local static review parity
- selected V1 design docs for continuity

Do not bulk-copy:

- V1 evidence as active V2 evidence;
- generated caches unrelated to the V2 demo;
- stale V1-only runtime names;
- old disabled DIY placeholder behavior.

Planned V2 package shape:

```text
space/
  app.py
  requirements.txt
  frontend/
  epic_errands_v2/
    contracts.py
    fixtures.py
    generation.py
    runtime_metadata.py
  diy_lab/
    app.py
    epic_errands_diy_workflow/
      contracts.py
      nodes.py
      trace.py
      workflow_adapter.py
    tests/
    evidence/
```

Data/state contracts:

- uploaded parent photos are session/demo inputs;
- uploaded child photos are session/demo inputs;
- uploaded parent reference audio is optional session/demo input;
- audio generation is enabled even when no parent reference audio exists;
- generated image is immutable after Review Goal loads;
- generated audio is immutable after Review Goal loads;
- text overlay is editable app-owned state;
- accepted goals enter Kid Goals;
- canceled goals are discarded;
- DIY edits stay inside DIY until the future save-to-app feature exists.

## Acceptance Decision

Documentation acceptance for this pass:

- V2 README exists.
- V2 UX flow exists.
- V2 implementation readiness exists.
- The docs reflect @cu's changes about audio, Review Goal, editable text
  overlay, and isolated DIY.

Future build acceptance:

- app imports/starts locally;
- frontend JavaScript passes syntax checks;
- Python package compiles;
- browser/mobile UAT covers the V2 verification checklist in `UX_FLOW.md`;
- docs/evidence references in `SOURCE_MAP.md` remain valid enough for future
  thread startup;
- runtime/provenance labels are visible without overclaiming;
- no public, hosted, model, or judge-ready proof is claimed without the matching
  workflow lane.

## Human Review Assumptions

Codex may proceed with these implementation choices unless @cu changes the
contract:

- use Quality mode as the only enabled generation mode;
- keep Speed mode visible but disabled/planned;
- make audio generation always enabled with optional parent reference audio;
- make Review Goal accept/cancel only;
- make the image and audio fixed on Review Goal;
- make text overlay editable;
- keep DIY isolated inside the same app package;
- label DIY save-to-main-app behavior as coming soon.

@cu approval is still required for public release, paid runtime, final
submission, or new model/spend decisions.
