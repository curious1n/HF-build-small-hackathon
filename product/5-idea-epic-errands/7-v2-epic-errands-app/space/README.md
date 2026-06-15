---
title: Epic Errands V2 Mobile Review
emoji: 🧭
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 6.18.0
app_file: app.py
pinned: false
license: mit
---

# Epic Errands V2 Mobile Review

Epic Errands V2 is a mobile review app that turns a child's ordinary goal into
a themed goal card with parent review, generated-style assets, and an isolated
DIY Lab for editing the workflow draft.

## Links

- App: [build-small-hackathon-epic-errands.hf.space](https://build-small-hackathon-epic-errands.hf.space/)
- Source repo: [curious1n/HF-build-small-hackathon](https://github.com/curious1n/HF-build-small-hackathon)
- HF Article source: [Epic Errands Running Notes](https://github.com/curious1n/HF-build-small-hackathon/blob/main/product/5-idea-epic-errands/articles/running-notes.md)
- HF Article: [Epic Errands Running Notes](https://huggingface.co/blog/build-small-hackathon/epic-errands-running-notes)
- Agent traces: [build-small-hackathon/epic-errands-v1-agent-traces](https://huggingface.co/datasets/build-small-hackathon/epic-errands-v1-agent-traces)

## Demo Flow

1. Open the mobile app shell.
2. Choose the app theme and review the current goal-generation settings.
3. Generate or review the kid-facing goal card.
4. Accept or cancel the generated goal from the parent review flow.
5. Open DIY Lab to edit the workflow draft and inspect the local trace preview.

## Models And Runtime

Runtime honesty for this Space package:

```text
lifecycle_stage=hosted testing
app_host=hf_space
model_runtime=none
fallback_used=true
```

Fresh live model proof is recorded outside the Space package under the V2
evidence folder. The hosted app currently uses deterministic/cached review
assets and does not claim hosted live model execution or judge-ready status.

The separate live-model smoke for the V2 evidence folder covered text, image,
and audio generation with `fallback_used=false`, but that was a direct
local-to-Modal smoke rather than hosted Space model execution.

## Evidence

- Local browser/mobile UAT evidence is recorded in the V2 evidence folder.
- Private hosted Space checks are recorded in the V2 evidence folder.
- The linked agent-trace dataset is the packaged trace surface for the
  text-first V1 quick eval.

Proof claimed by this Space README:

- The hosted testing package serves the mobile review app and DIY Lab shell.
- The Space package labels deterministic/cached behavior as fallback behavior.
- DIY edits update the local preview and trace display without claiming
  save-back to the main app.

Not claimed by this Space README:

- Hosted live model execution.
- Public release readiness.
- Judge-ready status.

## Routes

Main routes:

- `/`: custom mobile shell when the Gradio server route is exposed.
- `/epic/index.html`: explicit static hosted product shell.
- `/epic-diy/index.html`: explicit static DIY shell.
- `/health`: custom health endpoint when exposed by the Gradio server.

## Known Limits

- The Space is a private hosted testing package.
- The Epic Errands HF Article should be updated from
  `../../articles/running-notes.md` when the local source changes.
- Current hosted behavior uses deterministic/cached assets.
