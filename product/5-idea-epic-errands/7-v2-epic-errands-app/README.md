# Epic Errands V2 App

Status: V2 product contract, local implementation, local browser/mobile UAT
evidence, one local Modal-backed live model smoke, and private HF Space hosted
testing proof. Public release, submission, and judge-ready proof are not
claimed here.

Epic Errands V2 is a fast iteration of
`../5-v1-epic-errands-app/`. It preserves the V1 visual styling and mobile app
shape, then adds V2 settings, personalized generation inputs, editable text
overlays, always-on audio generation, and an isolated DIY Lab inside the same
app package.

Start future build threads with:

- [UX_FLOW.md](UX_FLOW.md): final user flow and verification checklist.
- [implementation-readiness.md](implementation-readiness.md): build contract.
- [SOURCE_MAP.md](SOURCE_MAP.md): prior versions, spikes, evidence, and
  do-not-redo lessons.
- [initial-inputs/models.md](initial-inputs/models.md): locked model matrix and
  runtime/proof links.

## Locked V2 Decisions

- Preserve V1 visual styling: Classroom, Questbook, and Comic.
- App UI styling is independent from generation mode and from already-generated
  media. Changing the app theme should not regenerate or mutate accepted image
  or audio assets.
- Quality mode is the only enabled hackathon generation mode.
- Speed mode may be visible as planned, but it is disabled for the hackathon.
- Generation mode owns model selection and output-size policy. Quality uses
  1024 x 1024 images; planned Speed uses 720 x 720 images.
- Quality text generation uses
  `nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF`, `llama.cpp`, GGUF, `Q4_K_M`.
- Quality image generation uses `black-forest-labs/FLUX.2-klein-9B`,
  Diffusers, safetensors, `bf16`, with 1024 x 1024 outputs.
- Audio generation is enabled. A parent's reference voice input is optional.
- If no parent reference audio exists, audio still generates using the default
  configured voice behavior.
- Parents can upload/remove parent photos, parent reference audio, child
  photos, and a custom image/reference for goal generation.
- Review Goal lets the parent accept or cancel the generated goal.
- The visible goal text is an app-owned editable text layer over the generated
  image.
- The generated image and generated audio cannot be edited or regenerated from
  the Review Goal screen in the fast V2 build.
- The DIY tab is isolated in its own folder inside the same app package.
- DIY mirrors the main app generation flow, shows model/runtime details, lets
  the parent edit the hardcoded workflow draft, and labels saving/updating the
  app as coming soon.

## Planned Folder Shape

```text
product/5-idea-epic-errands/7-v2-epic-errands-app/
  README.md
  UX_FLOW.md
  implementation-readiness.md
  initial-inputs/
    models.md
  space/
    app.py
    requirements.txt
    frontend/
    epic_errands_v2/
    diy_lab/
      app.py
      epic_errands_diy_workflow/
      tests/
      evidence/
```

## Proof Boundary

This folder records the V2 contract, local implementation, local browser/mobile
UAT evidence, one scoped live model smoke, and private hosted testing evidence.

Not claimed here:

- public hosted proof;
- hosted live model proof;
- public release;
- judge-ready status.

Local evidence:

- [Local browser/mobile UAT](evidence/local-browser-mobile-uat-2026-06-15/UAT_NOTES.md)
- [Live model smoke](evidence/live-model-smoke-2026-06-15/summary.json)
- [Private HF Space deploy check](evidence/hf-space-v2-deploy-check.json)
- [Private HF Space DIY hotfix check](evidence/hf-space-v2-diy-hotfix-2026-06-15.md)
- [Local DIY growth hotfix check](evidence/local-diy-growth-hotfix-2026-06-15.md)
- [Private HF Space no-iframe hotfix check](evidence/hf-space-v2-no-iframe-hotfix-2026-06-15.md)

Local Modal smoke scripts load account/HF credentials from repo root `.env` and
idea-specific Modal config from `product/5-idea-epic-errands/.env.modal.local`.

Prior evidence linked from [SOURCE_MAP.md](SOURCE_MAP.md) remains reusable
planning context only. It is not hosted, model-backed, or judge-ready V2 proof.
