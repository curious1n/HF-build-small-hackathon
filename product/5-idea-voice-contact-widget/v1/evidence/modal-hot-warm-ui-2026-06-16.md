# Voice Reach V1 Modal Hot/Warm UI Pass - 2026-06-16

## Scope

- Product: `product/5-idea-voice-contact-widget/v1`.
- Modal app/function: `voice-reach-v1-modal` / `process`.
- Endpoint: `https://curious1n--voice-reach-v1-modal-process.modal.run`.
- Hardware: Modal `T4`.
- Warm settings: `min_containers=1`, `scaledown_window=600`.
- Runtime: `VCW_MODEL_RUNTIME=modal`.
- UI target: local app at `http://127.0.0.1:7860`.

## Approval And Guard

- @cu approved budget: `$50`.
- Current official Modal pricing checked: T4 listed at `$0.000164/sec`.
- Stop condition used: stop after one schema-valid text warm and one
  schema-valid full-audio hot proof with `fallback_used=false`.
- Secrets were read from `.env` and ignored `.env.modal.local`; values were not
  printed.

## Preflight

No-GPU Hugging Face file access preflight passed for:

- `nvidia/nemotron-3.5-asr-streaming-0.6b` /
  `nemotron-3.5-asr-streaming-0.6b.nemo`.
- `CohereLabs/tiny-aya-fire-GGUF` / `tiny-aya-fire-q8_0.gguf`.

Modal auth check passed through `scripts/setup_modal_usage.py check`.

## Deploy

Command shape:

```bash
VCW_MODAL_MIN_CONTAINERS=1 VCW_MODAL_SCALEDOWN_WINDOW=600 VCW_MODAL_GPU=T4 \
  .venv/bin/modal deploy product/5-idea-voice-contact-widget/v1/modal/modal_voice_reach_v1.py
```

Result:

- Deployment passed.
- Web function remained
  `https://curious1n--voice-reach-v1-modal-process.modal.run`.

## Warm/Hot Results

| Check | HTTP ms | Modal total ms | ASR ms | Text ms | fallback_used |
|---|---:|---:|---:|---:|---|
| Direct Modal text warm | 12,324 | 9,043 | 0 | 9,043 | false |
| Direct Modal first audio warm | 125,869 | 123,384 | 122,177 | 1,207 | false |
| Direct Modal hot audio | 4,725 | 2,158 | 1,125 | 1,033 | false |
| Local app-to-Modal text smoke | 2,719 | 888 | 0 | 888 | false |
| Local app-to-Modal full audio smoke | 5,156 | 2,835 | 1,709 | 1,126 | false |

Audio fixture used:

```text
product/5-idea-voice-contact-widget/v0/eval/audio/hinglish_pricing_callback.wav
```

Hot audio transcript preview:

```text
Namaste, mujhe aapki service ke pricing aur availability ke baare mein jaana hai. Please mujhe call back kar dijiye.
```

Hot audio message preview:

```text
Hello, I would like to know the pricing and availability of your service. Please call me back.
```

## UI Update

- Header runtime pill changes from `Voice` to `Modal warm` when Modal is the
  selected available runtime.
- Runtime selector still shows all three options.
- Modal option note is `warm GPU` when Modal endpoint/auth are configured.
- Local `/api/packet` returned:
  - `model_runtime=modal`
  - `fallback_used=false`
  - `runtime_controls.selected=modal`
  - Modal option `enabled=true`, `available=true`, `note=warm GPU`
- Local `/api/process` with the audio fixture returned HTTP 200,
  `trace_id=vcw_594d377c96fc`, `model_runtime=modal`, and
  `fallback_used=false`.

## Local Host

Local app restarted on:

```text
http://127.0.0.1:7860
```

Run mode:

```text
VCW_MODEL_MODE=real
VCW_MODEL_RUNTIME=modal
VCW_ALLOW_RUNTIME_SWITCH=1
```

## Not Claimed

- No HF Space hosted proof was run in this pass.
- No judge-ready or final submission proof is claimed.
- Modal is still a testing runtime, not the official submission runtime.
