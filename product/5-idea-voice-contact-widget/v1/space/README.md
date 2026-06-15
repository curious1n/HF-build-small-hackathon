---
title: Voice Reach V1
colorFrom: indigo
colorTo: green
sdk: docker
app_port: 7860
suggested_hardware: t4-medium
---

# Voice Reach V1 Space

HF Space package for the metime.to Voice Contact Widget V1 slice.

Run:

```bash
python3 app.py --check
python3 app.py --port 7860
```

Non-inference hosted smoke:

```bash
python3 tools/smoke_api.py --include-traces
```

This checks `/health`, `/api/packet`, and recent `/api/traces` without sending
new audio through the paid model path. To intentionally test `/api/process`,
pass `--process-audio <path>` with `--allow-model-request`.

Tiny-aya text-only hosted smoke:

```bash
python3 tools/smoke_api.py \
  --text-transcript "Namaste, mujhe pricing details chahiye." \
  --speech-mode hinglish \
  --allow-model-request \
  --include-traces \
  --timeout 180
```

This checks `/api/text-smoke` with the Space-local GGUF text model. It is useful
for prompt-quality checks and does not claim ASR proof.

Runtime modes:

- Local default: deterministic fallback, clearly labeled with `fallback_used=true`.
- Modal testing: `VCW_MODEL_RUNTIME=modal` calls the `voice-reach-v1-modal`
  Modal sidecar from the HF Space CPU shell.
- HF Space proof: `VCW_MODEL_MODE=real` on `t4-medium`, loading
  `nvidia/nemotron-3.5-asr-streaming-0.6b` through NeMo/PyTorch and
  `CohereLabs/tiny-aya-fire-GGUF:Q8_0` through llama.cpp.

Deployment targets are recorded in `../deployment-targets.json`:

- `modal-test`: testing only; HF Space CPU Basic plus Modal model sidecar.
- `hf2-t4-test`: testing only; `${HF_2}/voice-reach` on `t4-medium`.
- `hackathon-t4-submit`: official submission; `${HF_HACKATHON}/voice-reach`
  on `t4-medium` with `VCW_MODEL_RUNTIME=hf_space`.

Submission must not use Modal. Switch the official Space with:

```bash
python3 product/5-idea-voice-contact-widget/v1/deploy_space.py \
  --target hackathon-t4-submit \
  --configure-target-runtime \
  --request-hardware
```

Proof boundary:

- Loads and validates `../onboarding/metime-to.json`.
- Renders a custom visitor-first widget using packet design tokens.
- Shows only `Hindi` and `Hinglish` speech modes.
- Sends browser recording audio to `/api/process`.
- Uses demo ledger fallback for send in `demo-ledger.jsonl`.
- Hosted model proof requires a trace with `fallback_used=false`.

Provenance is preserved in the collapsed debug panel and `/gradio` status panel.
