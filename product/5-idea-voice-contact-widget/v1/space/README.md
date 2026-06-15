---
title: Voice Reach V1
colorFrom: indigo
colorTo: green
sdk: docker
app_port: 7860
suggested_hardware: t4-medium
tags:
  - track:backyard
  - sponsor:openai
  - sponsor:nvidia
  - achievement:offgrid
  - achievement:offbrand
  - achievement:llama
  - achievement:sharing
  - achievement:fieldnotes
---

# Voice Reach V1

Voice Reach V1 is a metime.to voice contact widget that lets a site visitor
speak in Hindi or Hinglish, review an editable English contact message, and
send it through a site-owner contact flow.

NOTE: This is designed to be run 'Off Grid', so needs HF runtime (GPU) but since I'm unable to add credits to this org, it uses Modal.

NOTE: This competes for 'Tiny Titan' prize

## Links

- App: [build-small-hackathon-voice-reach.hf.space](https://build-small-hackathon-voice-reach.hf.space)
- Source repo: [curious1n/HF-build-small-hackathon](https://github.com/curious1n/HF-build-small-hackathon)
- HF Article: [Voice Reach Running Notes](https://huggingface.co/blog/build-small-hackathon/voice-reach-running-notes)
- Agent traces: [build-small-hackathon/voice-reach-agent-traces](https://huggingface.co/datasets/build-small-hackathon/voice-reach-agent-traces)

## Demo Flow

1. Open the widget and choose `Hindi` or `Hinglish`.
2. Record or submit a spoken visitor request.
3. Review the generated English message.
4. Edit the message if needed and submit it through the demo contact ledger.
5. Inspect recent trace summaries through `/api/traces`.

## Models And Runtime

- ASR: `nvidia/nemotron-3.5-asr-streaming-0.6b` through NeMo/PyTorch.
- Text: `CohereLabs/tiny-aya-fire-GGUF:Q8_0` through `llama.cpp`.
- Official Space runtime: `VCW_MODEL_RUNTIME=hf_space` on `t4-medium`.
- Local default without a selected real runtime: deterministic fallback,
  clearly labeled with `fallback_used=true`.
- When a UI-selected runtime is unavailable, `Record message` is disabled and
  the line below explains `Why it's disabled`; deterministic output is not
  substituted for selected runtime failures.
- Submission path: Space-local model runtime; Modal is testing-only and is not
  part of the official submission runtime.

## Evidence

- Recent runtime traces are exposed by the app through `/api/traces`.
- The linked agent-trace dataset is the review surface for packaged trace
  evidence.
- Hosted proof requires a trace with `fallback_used=false`.
- The collapsed debug panel and `/gradio` status panel preserve runtime
  provenance for reviewers.

Proof claimed by this Space README:

- The Space package loads and validates the metime.to onboarding packet.
- The UI renders a custom visitor-first widget with only Hindi and Hinglish
  speech modes.
- The app records trace summaries for processing and send events.

Not claimed by this Space README:

- Broad ASR quality across real traffic.
- Production email delivery.
- Judge-ready status without a fresh public submission check.

## Run Locally

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

- Modal testing: `VCW_MODEL_RUNTIME=modal` calls the `voice-reach-v1-modal`
  Modal sidecar from the HF Space CPU shell.
- HF Space proof: `VCW_MODEL_MODE=real` on `t4-medium`.
- Model Runtime UI switch:
  - Always shows `HF hackathon space`, `HF personal space`, and `Modal`.
  - `HF personal space` and `Modal` are enabled only when
    `VCW_ALLOW_RUNTIME_SWITCH=1`.
  - `HF personal space` is a server-side proxy to
    `APP_HF_PERSONAL_BASE_URL`; browser clients never receive HF or Modal
    tokens.
  - A selected runtime must be available before recording starts. Unavailable
    selected runtimes block the recorder and `/api/process` or
    `/api/text-smoke` returns `424` with `fallback_used=false`.
  - Official submission config clears the switch flag and proxy secrets.

Deployment targets are recorded in `../deployment-targets.json`:

- `modal-test`: testing only; HF Space CPU Basic plus Modal model sidecar; UI
  switch enabled.
- `hf2-t4-test`: testing only; `${HF_2}/voice-reach` on `t4-medium`; UI switch
  enabled.
- `hackathon-t4-submit`: official submission; `${HF_HACKATHON}/voice-reach`
  on `t4-medium` with `VCW_MODEL_RUNTIME=hf_space`; UI switch disabled.

Switch the official Space with:

```bash
python3 product/5-idea-voice-contact-widget/v1/deploy_space.py \
  --target hackathon-t4-submit \
  --configure-target-runtime \
  --request-hardware
```

## Known Limits

- Full audio ASR proof still depends on fresh hosted traces.
- The send step uses `demo-ledger.jsonl`; it is not production email delivery.
- Paid hardware or model-path retesting should follow the project approval
  gates before being run.
