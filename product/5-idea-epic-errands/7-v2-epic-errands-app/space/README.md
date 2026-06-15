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

Private hosted testing package for Epic Errands V2.

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

Main routes:

- `/`: custom mobile shell when the Gradio server route is exposed.
- `/epic/index.html`: explicit static hosted product shell.
- `/epic-diy/index.html`: explicit static DIY shell.
- `/health`: custom health endpoint when exposed by the Gradio server.
