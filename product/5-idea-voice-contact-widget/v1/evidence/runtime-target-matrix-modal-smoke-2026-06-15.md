# Voice Reach V1 Runtime Target Matrix And Modal Smoke - 2026-06-15

## Decision

Voice Reach V1 has three runtime/deployment locations:

1. `modal-test`
   - Purpose: model testing through Modal while the HF Space remains CPU Basic.
   - Space: `build-small-hackathon/voice-reach`
   - Runtime: `VCW_MODEL_RUNTIME=modal`
   - Submission: not allowed.

2. `hf2-t4-test`
   - Purpose: test the Space-local HF GPU path under the `HF_2` account.
   - Space: `curieous/voice-reach`
   - Runtime: `VCW_MODEL_RUNTIME=hf_space`
   - Hardware: `t4-medium`
   - Submission: not allowed.

3. `hackathon-t4-submit`
   - Purpose: official hackathon-org submission setting.
   - Space: `build-small-hackathon/voice-reach`
   - Runtime: `VCW_MODEL_RUNTIME=hf_space`
   - Hardware: `t4-medium`
   - Submission: allowed.
   - Modal disabled by runtime selection and Modal Space config cleanup.

Durable config:

- `product/5-idea-voice-contact-widget/v1/deployment-targets.json`
- `product/5-idea-voice-contact-widget/v1/deploy_space.py --target <profile>`

Important guardrail:

- The app no longer auto-selects Modal just because `APP_MODAL_BASE_URL` exists.
- Modal activates only when `VCW_MODEL_RUNTIME=modal`.
- Submission profiles set `VCW_MODEL_RUNTIME=hf_space`.
- The UI now always shows a `Model Runtime` selector with `HF hackathon space
  (credit issue)`, `HF personal space`, and `Modal`.
- `HF personal space` and `Modal` are selectable only when
  `VCW_ALLOW_RUNTIME_SWITCH=1`.
- `HF personal space` is proxied server-side through
  `APP_HF_PERSONAL_BASE_URL`; browser clients receive only runtime labels, not
  HF or Modal tokens.
- If the selected runtime is unavailable, the UI disables `Record message` and
  shows `Why it's disabled: ...`; API calls return `424` with
  `fallback_used=false` rather than substituting deterministic output.

## Modal Endpoint

- Modal app: `voice-reach-v1-modal`
- Endpoint: `https://curious1n--voice-reach-v1-modal-process.modal.run`
- Endpoint auth: `APP_MODAL_AUTH_TOKEN` bearer secret.
- Modal HF secret: `voice-reach-v1-hf`
- Latest update on 2026-06-16: `gpu=T4`, `min_containers=1`,
  `scaledown_window=600`.
- Latest hardware/runtime: Modal GPU sidecar with NeMo ASR and CUDA
  llama.cpp text path.

Model artifacts:

- ASR: `nvidia/nemotron-3.5-asr-streaming-0.6b`
- Text: `CohereLabs/tiny-aya-fire-GGUF` / `tiny-aya-fire-q8_0.gguf`

No-GPU model file preflight passed:

```text
onnx-community/nemotron-3.5-asr-streaming-0.6b-onnx-int4 genai_config.json access=pass will_download=True is_cached=False
CohereLabs/tiny-aya-fire-GGUF tiny-aya-fire-q4_k_m.gguf access=pass will_download=True is_cached=False
```

## Direct Modal Text Smoke

Payload used a supplied transcript to test the Modal text model path without ASR:

```text
Hi, mujhe metime.to ke pricing aur availability ke baare mein baat karni hai, please mujhe call back kar dijiye.
```

Result:

```json
{
  "status": 200,
  "elapsed_ms": 106971,
  "fallback_used": false,
  "fallback_reason": null,
  "latency_ms": 102384,
  "model_id": "supplied-transcript+CohereLabs/tiny-aya-fire-GGUF:Q4_K_M",
  "message_en": "I would like to discuss the pricing and availability of metime.to. Please call me back."
}
```

Interpretation:

- Pass for direct Modal text-model reachability.
- Not an ASR proof because the transcript was supplied.
- Hosted HF Space proof is captured separately below.

## HF2 T4 Test Space Proof

Target:

- Space: `curieous/voice-reach`
- Profile: `hf2-t4-test`
- Runtime: `VCW_MODEL_RUNTIME=hf_space`
- Hardware: `t4-medium`
- Token actor: `HF_TOKEN_2`

Deployment:

```text
commit: 1e46c16030ea559ec78b5923ae7531991cd126b2
url: https://huggingface.co/spaces/curieous/voice-reach/commit/1e46c16030ea559ec78b5923ae7531991cd126b2
final stage before smoke: RUNNING
hardware: t4-medium
requested_hardware: t4-medium
sleep_time: 900
```

Light hosted smoke:

```text
base_url: https://curieous-voice-reach.hf.space
/health: 200, model_runtime=hf_space, model_backend=nemo+llama.cpp, fallback_used=false
/api/packet: 200, model_runtime=hf_space, fallback_used=false
elapsed_ms: 7901
```

Hosted real text-model smoke:

```text
base_url: https://curieous-voice-reach.hf.space
/api/text-smoke: 200
elapsed_ms: 71572
text_load_ms: 16840
text_generation_ms: 51517
total_model_trace_ms: 68357
fallback_used: false
message_en: Hi, I would like to discuss the pricing and availability of metime.to. Please call me back.
```

Runtime state after proof:

```text
stage: PAUSED
hardware: t4-medium
requested_hardware: t4-medium
sleep_time: 900
```

Interpretation:

- Pass for the HF2-owned Space-local HF GPU text path.
- Not an ASR proof because the transcript was supplied.
- Paid HF2 test Space was paused immediately after proof.

## Official Hackathon Space Setting

Target:

- Space: `build-small-hackathon/voice-reach`
- Profile: `hackathon-t4-submit`
- Runtime: `VCW_MODEL_RUNTIME=hf_space`
- Intended hardware: `t4-medium`
- Token actor: `HF_TOKEN_2`

Configuration pass:

```text
commit: cda3bbf546a3e29f0c69b7ee1f27aec6ec295ebf
url: https://huggingface.co/spaces/build-small-hackathon/voice-reach/commit/cda3bbf546a3e29f0c69b7ee1f27aec6ec295ebf
VCW_MODEL_MODE: real
VCW_MODEL_RUNTIME: hf_space
removed_modal_keys: APP_MODAL_BASE_URL, APP_MODAL_TIMEOUT_SECONDS, APP_MODAL_MODEL_ID, APP_MODAL_ASR_MODEL_ID, APP_MODAL_AUTH_TOKEN
stage after config: PAUSED
requested_hardware: cpu-basic
sleep_time: 172800
```

Interpretation:

- Official Space has the latest code and official submission runtime config.
- Modal is disabled for the official Space.
- T4 hardware was not requested in this pass because the org billing/payment
  authorization issue is still unresolved.

## Verification

Local checks:

```text
PYTHONPYCACHEPREFIX=/tmp/vcw_v1_pycache python3 -m py_compile product/5-idea-voice-contact-widget/v1/deploy_space.py product/5-idea-voice-contact-widget/v1/space/app.py product/5-idea-voice-contact-widget/v1/modal/modal_voice_reach_v1.py scripts/setup_modal_usage.py
```

Passed.

```text
PYTHONPYCACHEPREFIX=/tmp/vcw_v1_pycache .venv/bin/python -m pytest product/5-idea-voice-contact-widget/v1/tests -q
```

Passed: `5 passed in 1.15s`.

Profile dry-runs passed:

```text
deploy_space.py --target modal-test
deploy_space.py --target hf2-t4-test
deploy_space.py --target hackathon-t4-submit
```

Resolved targets:

- `modal-test` -> `build-small-hackathon/voice-reach`, CPU Basic, `modal`
- `hf2-t4-test` -> `curieous/voice-reach`, `t4-medium`, `hf_space`
- `hackathon-t4-submit` -> `build-small-hackathon/voice-reach`, `t4-medium`, `hf_space`

## Budget And Active Runtime

Modal budget monitor after smoke:

```text
Spend estimate after final checks: $0.0279
Attribution confidence: medium
Thresholds crossed: none
Active app concerns: none from app list; Voice Contact Widget apps report tasks=0
```

## Known Blockers

- `hackathon-t4-submit` still depends on org billing permission for
  `build-small-hackathon`; previous probe showed `roleInOrg=contributor` and
  `canPay=False`.
- Full audio ASR proof is still pending for both Modal and HF Space paths; the
  proofs above used supplied transcripts to focus on text-model reachability.
- The 2026-06-16 Model Runtime UI switch change is locally verified only; it is
  not a fresh hosted Modal/HF paid-runtime proof.
