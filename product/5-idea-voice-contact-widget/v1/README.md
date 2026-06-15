# Voice Contact Widget V1

Last updated: 2026-06-14

V1 is a fresh product slice for a branded Hindi/Hinglish voice contact widget.
It does not inherit V0 runtime code, Modal code, hosted evidence, eval traces,
articles, tests, or broad language claims.

## V1 Baseline

- End user: `metime.to`.
- Contact destination: `founders@metime.to`.
- Visitor speech modes: `Hindi` and `Hinglish`.
- Output: editable English contact-form message.
- Runtime: one Hugging Face Space on `t4-medium`.
- ASR: `nvidia/nemotron-3.5-asr-streaming-0.6b`.
- Text: `CohereLabs/tiny-aya-fire-GGUF:Q8_0` through `llama.cpp`.
- Modal: not used.
- Eval audio collection: enabled for metime.to in the onboarding packet.

Optional deploy-helper Modal test config, when explicitly using the `modal-test`
target, is read from `product/5-idea-voice-contact-widget/.env.modal.local`.
The V1 submission runtime remains the Space-local `t4-medium` path above.

## Source Of Truth Files

| File | Purpose |
| --- | --- |
| `1-product-brief.md` | Product scope, user, success, non-goals. |
| `2-ux-ui-design.md` | Full visitor UX flow and key states. |
| `3-end-user-onboarding.md` | Onboarding packet requirements and metime.to assumptions. |
| `model-runtime-decision.md` | Model, runtime, language, and proof boundaries. |
| `implementation-readiness.md` | Build contract for a fresh Codex thread. |
| `onboarding/metime-to.json` | Ingestible V1 end-user onboarding packet. |
| `design/metime-to-tokens.css` | Generated metime.to widget token export. |
| `V1_GOAL_PROMPT.md` | Prompt for running the implementation goal in another thread. |

## Fresh-Start Rule

If any older V0 note outside this folder conflicts with V1, follow this folder.
V1 should not reintroduce Modal, English as a speech option, Kannada/Tamil
claims, model-selector UI, or alternate model recommendations unless @cu
explicitly changes the decision.
