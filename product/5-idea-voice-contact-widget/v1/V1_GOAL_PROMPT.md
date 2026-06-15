# Voice Contact Widget V1 Goal Prompt

Use this prompt in a fresh Codex thread.

```text
Work in /Users/cuStd/Desktop/dev/HF-build-small-hackathon.

Goal: build Voice Contact Widget V1 from scratch under
product/5-idea-voice-contact-widget/v1.

Read first:
- AGENTS.md
- COAGENTS.md
- TRIBAL.md
- product/HACKATHON_PRODUCT_WORKFLOW.md
- product/workflow/LANE_ROUTER.md
- product/workflow/FEATURE_FIRST.md
- product/workflow/PRODUCT_BRIEFING.md
- product/workflow/PRODUCT_DESIGN.md
- product/workflow/IMPLEMENTATION_READINESS.md
- product/workflow/RUNTIME_LABELS_AND_AXES.md
- product/5-idea-voice-contact-widget/v1/README.md
- product/5-idea-voice-contact-widget/v1/1-product-brief.md
- product/5-idea-voice-contact-widget/v1/2-ux-ui-design.md
- product/5-idea-voice-contact-widget/v1/3-end-user-onboarding.md
- product/5-idea-voice-contact-widget/v1/model-runtime-decision.md
- product/5-idea-voice-contact-widget/v1/implementation-readiness.md
- product/5-idea-voice-contact-widget/v1/onboarding/metime-to.json

Workflow lanes to declare before work:
- Feature-First: product/workflow/FEATURE_FIRST.md
- Product Design: product/workflow/PRODUCT_DESIGN.md
- Implementation Readiness: product/workflow/IMPLEMENTATION_READINESS.md
- Runtime Feasibility: product/workflow/MODEL_RUNTIME_FEASIBILITY.md only if doing model load/smoke
- HF Space Shipping: product/workflow/HF_SPACE_SHIPPING.md only if packaging/deploying/proving hosted Space

Fixed decisions:
- End user: metime.to.
- Contact email: founders@metime.to.
- Use generated brand tokens from onboarding/metime-to.json and design/metime-to-tokens.css.
- Audio eval collection is enabled for metime.to.
- Show visitor-facing eval notice before recording.
- Speech mode UI is a segmented control with only Hindi and Hinglish.
- Do not expose English as a speech mode.
- Output is an editable English contact-form message.
- ASR model: nvidia/nemotron-3.5-asr-streaming-0.6b.
- Text model: CohereLabs/tiny-aya-fire-GGUF:Q8_0 through llama.cpp or llama-cpp-python.
- Runtime target: one Hugging Face Space on t4-medium.
- Do not use Modal.

Build target:
- Create the V1 app under product/5-idea-voice-contact-widget/v1/space.
- Load and validate onboarding/metime-to.json.
- Render a custom visitor-first widget using the metime.to design tokens.
- Implement the browser recording flow and full UI states:
  idle, permission pending, recording, processing, review, editing, sending,
  success, mic denied, empty audio, ASR failure, text failure, send failure.
- Keep model/runtime/debug details collapsed.
- Preserve trace/provenance fields from implementation-readiness.md.
- Use demo ledger fallback if real email credentials are absent.

Initial proof claim:
- Local/package proof only unless @cu explicitly asks for hosted Space or paid
  hardware proof.
- Do not claim model proof unless real audio passes through both model legs with
  fallback_used=false.
- Do not claim hosted proof unless the actual HF Space is deployed and tested.

Suggested first verification:
- Run focused tests or import/startup checks for the V1 Space package.
- Inspect local UI in browser if a local dev server is started.
- Confirm only Hindi/Hinglish are visible as speech modes.
- Confirm onboarding packet values appear in UI/debug provenance.

Stop before:
- buying/running paid hardware without explicit approval and stop condition;
- deploying publicly without explicit approval;
- introducing Modal;
- changing models;
- changing contact email;
- removing eval notice or retention metadata.
```
