# Voice Reach V1 HF Hackathon Boot Evidence - 2026-06-15

## Scope

Deploy V1 to the hackathon Space target:

- Space repo: `build-small-hackathon/voice-reach`
- App URL: `https://build-small-hackathon-voice-reach.hf.space`
- Namespace env: `HF_HACKATHON`
- Upload/auth token env: `HF_TOKEN_2`
- Requested default hardware: `t4-medium`
- Requested keep-running sleep policy: `sleep_time=-1`

## Repo and Runtime Changes

- V1 deploy helper now defaults to `HF_HACKATHON/voice-reach` and `HF_TOKEN_2`.
- V1 smoke helper now defaults to `https://build-small-hackathon-voice-reach.hf.space` and `HF_TOKEN_2`.
- Space card and visible app titles use `Voice Reach V1`.
- Runtime token config set Space secrets by name only: `HF_TOKEN`, `HF_TOKEN_2`.
- Runtime variable set by name/value: `VCW_MODEL_MODE=real`.

## Local Verification

```text
PYTHONPYCACHEPREFIX=/tmp/vcw_v1_pycache python3 -m py_compile product/5-idea-voice-contact-widget/v1/deploy_space.py product/5-idea-voice-contact-widget/v1/space/app.py product/5-idea-voice-contact-widget/v1/space/tools/smoke_api.py
```

Passed.

```text
PYTHONPYCACHEPREFIX=/tmp/vcw_v1_pycache .venv/bin/python -m pytest product/5-idea-voice-contact-widget/v1/tests -q
```

Passed: `5 passed in 1.24s`.

```text
PYTHONPYCACHEPREFIX=/tmp/vcw_v1_pycache .venv/bin/python product/5-idea-voice-contact-widget/v1/space/app.py --check
```

Passed locally in deterministic mode.

## Model File Preflight

Model file access preflight passed with `HF_TOKEN_2` before paid hardware:

- `nvidia/nemotron-3.5-asr-streaming-0.6b` / `nemotron-3.5-asr-streaming-0.6b.nemo`
- `CohereLabs/tiny-aya-fire-GGUF` / `tiny-aya-fire-q8_0.gguf`

Both returned `access=pass`, `will_download=true`.

## Upload

Uploaded V1 package to the hackathon Space:

- Commit: `74719281f0d8c23c8f2b91fb6690b778367f9d27`
- Commit time: `2026-06-15 15:05:09+00:00`
- Commit URL: `https://huggingface.co/spaces/build-small-hackathon/voice-reach/commit/74719281f0d8c23c8f2b91fb6690b778367f9d27`

## T4 Hardware Request

The `t4-medium` hardware request failed with HF HTTP `402 Payment Required`:

```text
You must purchase pre-paid credits to host Spaces with paid hardware.
Billing URL: https://huggingface.co/organizations/build-small-hackathon/settings/billing
```

Current result: V1 is deployed and running, but on `cpu-basic`, not `t4-medium`.

## Boot Timing

Build log highlights:

- Python/NVIDIA/NeMo dependency install and wheel build finished in `134.8s`.
- Image push finished in `89.1s`.
- Runtime log showed application startup at `2026-06-15 15:11:44+00:00`.
- Runtime log then showed Uvicorn startup complete and `GET /health` plus `GET /api/packet` returning `200`.

Explicit public boot monitor:

- Monitor start: `2026-06-15T15:15:19.361263+00:00`
- Initial public state: Hub stage `RUNNING_APP_STARTING`; `/health` still served old V0 app `voice-contact-widget`; `/api/packet` returned `404`.
- Public V1 serving: `2026-06-15T15:17:06.198215+00:00`
- Elapsed from monitor start to public V1 serving: `106.8s`.

Approximate elapsed from V1 upload commit time to public V1 serving:

- `2026-06-15 15:05:09+00:00` to `2026-06-15 15:17:06+00:00`
- About `11m57s`.

## Final Hosted Smoke

Command:

```text
PYTHONPYCACHEPREFIX=/tmp/vcw_v1_pycache .venv/bin/python product/5-idea-voice-contact-widget/v1/space/tools/smoke_api.py --timeout 45
```

Result:

- Base URL: `https://build-small-hackathon-voice-reach.hf.space`
- Token env: `HF_TOKEN_2`
- `/health`: HTTP `200`
- `/api/packet`: HTTP `200`
- Client elapsed: `2189ms`
- Health app: `voice-reach-v1`
- Health version: `v1-space-local-model-2026-06-15`
- Health mode: `model_mode=real`, `model_runtime=hf_space`
- Packet provenance: `fallback_used=false`, `model_backend=nemo+llama.cpp`

Final Hub status:

```text
stage=RUNNING
hardware=cpu-basic
requested_hardware=cpu-basic
sleep_time=172800
raw_error=None
```

## Proof Boundary

Claimed:

- V1 package is deployed to `build-small-hackathon/voice-reach`.
- Space is publicly serving V1 `/health` and `/api/packet`.
- Runtime token config is present by secret names.
- Boot timing from explicit public monitor is recorded.

Not claimed:

- `t4-medium` is active; it is blocked by org billing.
- Real ASR/Tiny Aya inference has been re-smoked on this `voice-reach` target.
- Judge-ready submission status.
