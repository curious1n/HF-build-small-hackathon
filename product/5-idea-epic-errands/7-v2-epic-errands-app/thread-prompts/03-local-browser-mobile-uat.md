# Prompt 03: Local Browser/Mobile UAT

```text
Work in /Users/cuStd/Desktop/dev/HF-build-small-hackathon.

Goal: run local browser/mobile UAT for Epic Errands V2 and record evidence for
the real local app. Fix small UAT blockers when clearly scoped.

Before substantial work, follow the repo startup contract:
- Read COAGENTS.md
- Read TRIBAL.md
- Read product/HACKATHON_PRODUCT_WORKFLOW.md
- Declare workflow lanes, prompt cards, excluded lanes, and proof claim.

Workflow lanes to take:
- UX/UAT Evidence: product/workflow/UX_UAT_EVIDENCE.md
- Feature-First only for small fixes discovered during UAT.
- Product Design only for the handoff trace check consumed by UAT.

Prompt cards to use:
- product/workflow/prompts/browser-mobile-uat-proof.md
- product/workflow/prompts/design-to-code-trace-gate.md

Do not take unless scope expands:
- Runtime Feasibility
- Sponsor Model Proof
- Modal Sidecar
- HF Space Shipping
- Submission Readiness

Read first:
- product/5-idea-epic-errands/7-v2-epic-errands-app/README.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/UX_FLOW.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/implementation-readiness.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/handoff.json
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/visual-design.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/style-modes.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/component-tree.json
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/interaction-manifest.json
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/states.md
- the V2 app implementation under product/5-idea-epic-errands/7-v2-epic-errands-app/space/

Preflight:
- Run the smallest local build/start command for the V2 app.
- Run or review the implementation trace gate before the UX gate:
  python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate implementation
- If implementation anchors are missing, use Prompt 02 or make a small scoped
  anchor fix before claiming local browser/mobile UAT.
- Use Browser/in-app browser for local web inspection when available.
- Test mobile widths, especially 390px and 360px.
- Do not use hosted Space proof unless HF Space Shipping lane is explicitly
  added.

UAT checklist:
- V1 visual styling is preserved: Questbook default is recognizable,
  Classroom/Comic are selectable, layout remains mobile-first, and the visible
  product surface does not leak default Gradio styling.
- Settings upload/remove controls render and update session state for parent
  photos, child photos, optional parent reference audio, and custom
  image/reference inputs.
- App theme changes affect UI shell/overlay style but do not mutate accepted
  generated media.
- Quality mode is enabled and selected.
- Speed mode is visibly disabled/planned.
- Quality image policy says 1024 x 1024.
- Planned Speed image policy says 720 x 720.
- Compact parent-facing provenance reflects the V2 Quality model contract:
  Nemotron GGUF text, FLUX.2-klein-9B image, and VoxCPM2 audio.
- Audio generation appears enabled when no parent reference audio exists.
- Parent can draft a goal, select parent/child/custom image references, generate
  in Quality mode, and reach Review Goal.
- Review Goal supports editable app-owned text overlay.
- Review Goal keeps the generated image in a stable square media frame and does
  not bake goal text into image pixels.
- Review Goal has Accept and Cancel.
- Review Goal does not offer image editing or audio editing.
- Accept publishes the goal to Kid Goals.
- Cancel does not publish the goal.
- Kid opens a thumbnail/card, sees a read-only app-owned text overlay, plays or
  previews generated audio, and completes the goal.
- Kid Goal cards do not expose raw model IDs, prompt text, raw JSON, generated
  steps, or completion-check internals.
- Parent approves the completed goal and reward state updates.
- DIY opens in an isolated surface.
- DIY mirrors plain goal -> text -> image -> audio -> composed card -> trace.
- DIY shows model IDs, runtimes, formats, quantization, and fallback labels for
  the hardcoded mirrored flow.
- DIY edits update only DIY preview/trace.
- DIY save-back-to-app is labelled coming soon.

Design trace:
- After implementation anchors exist and local UX evidence is recorded, run:
  python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate ux
- If the UX gate fails because evidence paths are missing, record evidence in
  the V2 folder and update handoff refs only if appropriate.

Proof claim:
- Local browser/mobile UAT only.
- Do not claim hosted Space proof, model proof, sponsor proof, public release,
  submission readiness, or judge-ready status.
- Deterministic/cached/fallback behavior is allowed for local UX proof but is
  not model proof.

Finish with:
- Local URL and command used.
- Browser/mobile viewports tested.
- Pass/fail checklist.
- Screenshots/evidence files created.
- Known limitations.
- Design handoff UX gate result, if run.
- Next lane needed before any hosted/model/submission claim.
```
