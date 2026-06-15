# Prompt 04: Shipping Decision Gate

```text
Work in /Users/cuStd/Desktop/dev/HF-build-small-hackathon.

Goal: decide the next Epic Errands V2 proof path after local implementation and
local browser/mobile UAT. Prepare the right next action without accidentally
claiming or executing hosted/model/submission work.

Before substantial work, follow the repo startup contract:
- Read COAGENTS.md
- Read TRIBAL.md
- Read product/HACKATHON_PRODUCT_WORKFLOW.md
- Declare workflow lanes, prompt cards, excluded lanes, and proof claim.

Workflow lanes to take:
- Artifacts And Handoff: product/workflow/ARTIFACTS_AND_HANDOFF.md
- Implementation Readiness only to inspect current proof state and blockers:
  product/workflow/IMPLEMENTATION_READINESS.md

Prompt cards to use:
- product/workflow/prompts/thread-handoff-evidence-ledger.md
- Add product/workflow/prompts/hf-space-deploy-and-proof.md only if @cu
  explicitly asks to deploy/prove a Space in this same thread.
- Add product/workflow/prompts/sponsor-model-integration-smoke.md only if @cu
  explicitly asks for real model/sponsor proof in this same thread.
- Add product/workflow/prompts/gated-model-access-preflight.md before any paid
  GPU, Modal, ZeroGPU, paid Space, or gated-model file-load path.

Do not take unless @cu explicitly approves scope expansion:
- HF Space Shipping
- Runtime Feasibility
- Sponsor Model Proof
- Modal Sidecar
- Submission Readiness

Read first:
- product/5-idea-epic-errands/7-v2-epic-errands-app/README.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/UX_FLOW.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/implementation-readiness.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/SOURCE_MAP.md
- product/5-idea-epic-errands/7-v2-epic-errands-app/design/handoff.json
- current V2 evidence/UAT docs if they exist
- current V2 space package if it exists

Tasks:
1. Summarize current proof state:
   - design artifact readiness
   - implementation status
   - implementation trace gate status
   - local browser/mobile UAT status
   - hosted Space status
   - model/sponsor proof status
   - submission/judge-ready status
2. Identify the smallest honest next lane:
   - HF Space Shipping if local UAT is good and @cu wants hosted proof.
   - Sponsor Model Proof or Runtime Feasibility if a real model claim is needed.
   - Modal Sidecar only if endpoint/spend/runtime architecture is in scope.
   - Submission Readiness only after public hosted app and proof artifacts exist.
3. If approval is needed, stop and ask @cu with concrete budget/scope/stop
   condition instead of acting.
4. If @cu already approved a specific path in the prompt, execute only that
   path's lane and proof requirements.
5. Leave a concise handoff/evidence ledger.

Approval rules:
- Public release or final submission requires explicit @cu approval.
- Paid runtime, paid Space hardware, always-on runtime, warm pool, or credit
  spend requires explicit @cu approval, budget, max duration, and stop condition.
- Do not print token values. Use env var names only.
- Before paid GPU, Modal, ZeroGPU, or paid Space work that loads a gated model,
  run the required token-backed no-GPU model-file access check using
  product/workflow/prompts/gated-model-access-preflight.md.

Proof claim:
- Decision/handoff artifact only unless a lane is explicitly added and proof is
  produced.
- Do not claim hosted proof, sponsor/model proof, public release,
  submission-ready, or judge-ready status from prior planning docs alone.

Finish with:
- Recommended next lane.
- Whether @cu approval is required.
- Exact approval question if needed.
- If no approval is needed, exact next prompt/action to run.
- Do-not-redo notes from SOURCE_MAP.md and current evidence.
```
