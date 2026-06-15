# Prompt 02: Implementation Trace Check

```text
Work in /Users/cuStd/Desktop/dev/HF-build-small-hackathon.

Goal: verify that the Epic Errands V2 Detailed Design decisions in
design/handoff.json survived into the local implementation. Fix missing anchors
when the fix is small and clearly within scope.

Before substantial work, follow the repo startup contract:
- Read COAGENTS.md
- Read TRIBAL.md
- Read product/HACKATHON_PRODUCT_WORKFLOW.md
- Declare workflow lanes, prompt cards, excluded lanes, and proof claim.

Workflow lanes to take:
- Implementation Readiness: product/workflow/IMPLEMENTATION_READINESS.md
- Product Design only for the design-to-code trace gate:
  product/workflow/PRODUCT_DESIGN.md
- Feature-First only if a small code fix is needed to add missing anchors or
  repair a dropped must-preserve behavior.

Prompt cards to use:
- product/workflow/prompts/design-to-code-trace-gate.md

Do not take unless scope expands:
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
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/handoff.json
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/component-tree.json
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/data-contract.json
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/interaction-manifest.json
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/states.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/space/ if it exists

Run:
- python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate implementation

If the gate fails:
- Treat P0 findings as blockers unless @cu explicitly waives them.
- For missing implementation anchors, inspect the V2 implementation and add the
  smallest durable anchor or code hook that matches the existing UI.
- Do not invent new visual direction or broaden product behavior.
- Re-run the implementation gate after changes.

Must-preserve decisions to protect:
- V1 theme switching and Questbook default.
- App UI theme independent from generation mode and accepted media.
- Quality enabled; Speed disabled/planned.
- Quality model contract and 1024 x 1024 image policy.
- Audio enabled with optional parent reference audio.
- Review Goal editable app-owned overlay.
- Review Goal Accept and Cancel only.
- No image/audio editing from Review Goal.
- Kid cards do not expose raw model internals, steps, prompt text, or JSON.
- Parent/kid completion and reward approval loop.
- DIY isolated inside the same package with save-back coming soon.

Proof claim:
- Design-to-code implementation trace only.
- Do not claim UX works in browser unless UX/UAT Evidence lane is added.
- Do not claim hosted proof, model proof, public release, or judge-ready status.

Finish with:
- Gate run and exact result.
- P0 blockers, P1 warnings, P2 notes.
- Files changed, if any.
- Waivers, if any.
- Whether the local browser/mobile UAT prompt can run next.
```
