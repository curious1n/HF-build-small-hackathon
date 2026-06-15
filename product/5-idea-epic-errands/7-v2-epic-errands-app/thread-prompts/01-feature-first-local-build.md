# Prompt 01: Feature-First Local Build

```text
Goal: implement the fast local Epic Errands V2 app slice from the existing V2
design package. Keep this to local implementation and focused verification.

Before substantial work, follow the repo startup contract:
- Read COAGENTS.md
- Read TRIBAL.md
- Read product/HACKATHON_PRODUCT_WORKFLOW.md
- Declare workflow lanes, prompt cards, excluded lanes, and proof claim.

Workflow lanes to take:
- Feature-First: product/workflow/FEATURE_FIRST.md
- Implementation Readiness only as needed to keep the design/build handoff
  traceable: product/workflow/IMPLEMENTATION_READINESS.md

Prompt cards to use:
- None unless the lane router or implementation scope requires one.

Do not take unless scope expands:
- Product Design
- UX/UAT Evidence
- Runtime Feasibility
- Sponsor Model Proof
- Modal Sidecar
- HF Space Shipping
- Submission Readiness

Read first:
- product/5-idea-epic-errands/7-v2-epic-errands-app/README.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/UX_FLOW.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/implementation-readiness.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/SOURCE_MAP.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/initial-inputs/models.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/handoff.json
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/visual-design.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/style-modes.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/states.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/screen-package.json
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/component-tree.json
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/data-contract.json
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/interaction-manifest.json

Use V1 as source, not as proof:
- product/5-idea-epic-errands/5-v1-epic-errands-app/design/
- product/5-idea-epic-errands/5-v1-epic-errands-app/static/
- product/5-idea-epic-errands/5-v1-epic-errands-app/space/

Locked V2 behavior:
- Preserve V1 visual styling. Do not create a new visual direction.
- Classroom, Questbook, and Comic are app UI themes.
- App UI styling is independent from generation mode and accepted generated
  media.
- Quality mode only is enabled for hackathon.
- Speed mode is visible/planned but disabled.
- Quality text model is nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF via llama.cpp,
  GGUF, Q4_K_M.
- Quality image model is black-forest-labs/FLUX.2-klein-9B via Diffusers,
  safetensors, bf16, with 1024 x 1024 output.
- Quality audio model is openbmb/VoxCPM2 via voxcpm, safetensors, bf16.
- Planned Speed image output is 720 x 720.
- Audio generation is enabled; parent reference audio is optional.
- Settings lets parents upload/remove parent photos, child photos, parent
  reference audio, and custom image/reference inputs.
- Parent Goals lets parents select parent/child/custom image references for the
  generation run.
- Review Goal has Accept and Cancel.
- Goal text is an editable app-owned text layer over the generated image.
- Do not bake goal text into generated image pixels.
- Generated image and generated audio cannot be changed from Review Goal.
- Kid Goal cards use a read-only app-owned overlay, include playable audio, and
  hide raw model internals, prompt text, raw JSON, steps, and completion-check
  fields.
- Keep compact model/provenance labels available in parent Review and DIY, but
  do not turn the main parent/kid app into a model lab.
- DIY is isolated inside the same app package, mirrors the app generation flow,
  lets parent edit the hardcoded workflow draft, and labels saving back to the
  app as coming soon.

Implementation target:
- Create or update the V2 app package under:
  product/5-idea-epic-errands/7-v2-epic-errands-app/space/
- Build enough local app behavior to support:
  - Home
  - Settings
  - Parent Goals
  - Review Goal
  - Kid Goals
  - DIY isolated surface
- Include stable design anchors from design/handoff.json and
  design/component-tree.json, especially upload/remove actions, Review Goal
  Accept/Cancel, read-only kid overlay, playable audio, and DIY save-back
  notice.
- Prefer the V1 custom frontend pattern and Gradio-compatible package shape
  unless a blocker appears.

Proof claim:
- Local implementation/focused checks only.
- Do not claim browser/mobile UAT unless the UX/UAT lane is added and evidence
  is recorded.
- Do not claim hosted proof, model proof, public release, or judge-ready status.

Verification to run if available:
- Python compile/import checks for the V2 package.
- JavaScript syntax check for frontend files.
- JSON validation for modified/generated design or contract files.
- Do not run paid model, Modal, HF deploy, or public release actions.

Finish with:
- Files changed.
- Commands run and results.
- What is implemented.
- Known gaps.
- Whether the implementation gate is ready to run next:
  python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate implementation
```
