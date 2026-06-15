# V1 HF Space t4-medium Model Path Attempt

Date: 2026-06-14

## Continuation after blocker limit update

Continuation approval:

- @cu approved continuing and changed the blocker limit to `5`.
- Hardware remained restricted to `t4-medium`.
- Budget cap and pause/downgrade guardrail remained active.

Source guidance used:

- The Nemotron model card says this is a prompt-conditioned multilingual model
  and the streaming inference path passes `target_lang`, for example `hi-IN` or
  `auto`.
- The official NeMo cache-aware streaming script sets
  `asr_model.set_inference_prompt(target_lang)` and uses
  `CacheAwareStreamingAudioBuffer` with `conformer_stream_step`.

Fix attempt for blocker 2:

- Replaced the generic NeMo `transcribe(...)` calls in `NemoAsrAdapter` with a
  minimal cache-aware streaming loop based on the official NeMo script.
- Uploaded commit:
  `26151a5ad60965dd2fbba0929e0e68e496356dc7`.

Result:

- Space rebuilt and reached `RUNNING` on `t4-medium`.
- Authenticated `/health` passed.
- The same 15 second Hindi FLEURS smoke failed with HTTP 424 before ASR output.

Blocker 3:

```text
trace_id=vcw_3ed6920d2a38
fallback_used=true
fallback_reason=real_model_error:SyntaxError
blocker=invalid syntax (streaming_utils.py, line 2467)
```

Cause:

- The pinned NeMo commit's `streaming_utils.py` uses Python syntax unsupported
  by Python 3.10.
- The original Docker base was `nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04`,
  whose system `python3` is Python 3.10.

Fix attempt:

- Verified Python 3.12 wheels exist for:
  - `torch==2.6.0+cu124`
  - `torchaudio==2.6.0+cu124`
  - `llama-cpp-python==0.3.29`
- Tried switching to `nvidia/cuda:12.4.1-cudnn-devel-ubuntu24.04`.
- Uploaded commit:
  `65bc290295b9688b17c5cc81ea397f9b400dc90c`.

Blocker 4:

```text
docker.io/nvidia/cuda:12.4.1-cudnn-devel-ubuntu24.04: not found
```

Fix attempt:

- Queried Docker Hub tags and found Ubuntu 24.04 cudnn-devel tags start at
  CUDA 12.6.x for this line.
- Switched to `nvidia/cuda:12.6.3-cudnn-devel-ubuntu24.04`.
- Uploaded commit:
  `da95752695c1a98020dbf9f2fe77c6e6cce69c4b`.

Blocker 5:

```text
error: externally-managed-environment
```

Cause:

- Ubuntu 24.04 enforces PEP 668 and rejects system-wide `python3 -m pip install`
  into the OS-managed Python environment.

Local fix applied after pausing/downgrading:

- Updated the Dockerfile to create `/opt/venv`.
- Installs torch, torchaudio, llama-cpp-python, and requirements into that venv.
- Runs the app with `python` from the venv.
- Uploaded commit:
  `d2b2e09fb052e302a065df41be6f099ec905a091`.

Post-upload safety state:

```text
stage=PAUSED
hardware=None
requested_hardware=cpu-basic
raw_error=None
```

Continuation conclusion:

- The NeMo streaming-call fix is implemented.
- The Python 3.10 incompatibility has a Docker-level fix path.
- The current Space repo includes the venv-based Ubuntu 24.04 Dockerfile fix.
- No additional `t4-medium` proof run was started after blocker 5.
- Required `fallback_used=false` hosted audio trace is still not achieved.

## Resumed preflight and paid smoke attempt

Resume time: 2026-06-14.

Run label: `Hosted Space With Space-Local Model`.

Scope:

- Resume only the V1 HF Space-local model proof.
- Keep UX/UAT, Modal, submission, and judge-ready claims out of scope.
- Use only `t4-medium`; pause/downgrade after proof or blocker.

Preflight results before the resumed paid run:

- `app.py` compiled.
- `app.py --check` passed with `speech_modes=["hindi","hinglish"]`,
  `model_runtime=none`, `fallback_used=true`, and `concurrency=1`.
- Space onboarding packet matched source onboarding packet.
- Requirement syntax passed.
- No-deps requirement dry-run passed.
- `llama-cpp-python==0.3.29` Python 3.10 manylinux CPU wheel existed.
- `torch==2.6.0+cu124` and `torchaudio==2.6.0+cu124` Linux Python 3.10
  wheels existed.
- Token-backed model-file access passed again for:
  - `nvidia/nemotron-3.5-asr-streaming-0.6b` /
    `nemotron-3.5-asr-streaming-0.6b.nemo`, size `2368284501`.
  - `CohereLabs/tiny-aya-fire-GGUF` / `tiny-aya-fire-q8_0.gguf`,
    size `3570654816`.
- Space pre-run safety state was `stage=PAUSED`, `hardware=None`,
  `requested_hardware=cpu-basic`.

Resumed uploads:

- `5efcfffaf275ff89e4f4d89e116aba6b138bb238`: uploaded corrected Docker
  package with fixed llama and NeMo requirement syntax.
- `72bffc490b905b61d793b30e6cd934aab6e19989`: bumped `pydantic` from
  `2.10.4` to `2.10.6` after NeMo dependency resolution required
  `pydantic>=2.10.6`.

Resumed blocker 1:

```text
ERROR: Cannot install ... nemo_toolkit and pydantic==2.10.4 because these
package versions have conflicting dependencies.
nv-one-logger-core 2.3.1 depends on pydantic<3.0.0 and >=2.10.6
```

Smallest fix applied:

```text
pydantic==2.10.6
```

Stronger resolver preflight after the fix:

- Full local resolver pass over the Docker `requirements-no-llama` step passed.
- Space Docker build then passed dependency installation, built the NeMo wheel,
  pushed the image, and reached `APP_STARTING`.

Hosted Space load result:

- Space reached `stage=RUNNING`.
- Actual hardware reported `hardware=t4-medium`.
- Authenticated `/health` returned HTTP 200.
- Space is private, so unauthenticated direct `.hf.space` requests returned the
  Hugging Face 404 page. Authenticated requests with `HF_TOKEN_1` reached the
  app.

Authenticated `/health` axes:

```text
lifecycle_stage=staging
app_host=hf_space
model_runtime=hf_space
model_backend=nemo+llama.cpp
inference_engine=nemo+llama.cpp
model_artifact_format=nemo_archive+gguf
quantization=unknown+q8_0
model_mode=real
fallback_used=false
concurrency=1
```

Audio smoke input:

- Source: one public Hindi `google/fleurs` `hi_in` test clip extracted from the
  converted parquet split.
- Duration: `15.00` seconds.
- Sample rate: `16000`.
- Request mode: `speech_mode=hindi`, ASR language hint `hi-IN`.

Hosted model request result: failed with HTTP 424 after both model adapters
loaded.

Runtime evidence from logs:

- NeMo restored `EncDecRNNTBPEModelWithPrompt` from
  `nemotron-3.5-asr-streaming-0.6b.nemo`.
- tiny-aya initialized through llama.cpp.
- NeMo logged `Inference prompt set to 'hi-IN' (index 6)`.
- `/api/process` returned HTTP 424.

Failed trace:

```text
trace_id=vcw_4149da7ad818
lifecycle_stage=staging
app_host=hf_space
model_runtime=hf_space
model_backend=nemo+llama.cpp
inference_engine=nemo+llama.cpp
model_artifact_format=nemo_archive+gguf
quantization=unknown+q8_0
model_id=nvidia/nemotron-3.5-asr-streaming-0.6b+CohereLabs/tiny-aya-fire-GGUF:Q8_0
fallback_used=true
fallback_reason=real_model_error:ValueError
blocker=Unknown prompt key: 'None'. Available: ['en-US', 'en', 'en-GB', 'enGB', 'es-ES', 'esES', 'es-US', 'es', 'zh-CN', 'zh-ZH']...
```

Resumed blocker 2:

The first real audio request failed inside NeMo transcription with:

```text
Unknown prompt key: 'None'
```

This happened after calling `set_inference_prompt("hi-IN")`, so the next
smallest fix is to align the transcribe call with the Nemotron streaming prompt
API instead of relying only on model-level prompt state. Check the model card or
official sample for the expected per-request language/prompt argument, then
retry one Hindi `hi-IN` smoke before considering `auto`.

Final safety state after resumed attempt:

```text
stage=PAUSED
hardware=None
requested_hardware=cpu-basic
raw_error=None
```

Conclusion for resumed attempt:

- Hosted Space load on `t4-medium`: passed.
- Both model adapters loaded: passed.
- One real audio request completed ASR + text generation: failed.
- Required `fallback_used=false` trace: not achieved.
- Stop condition: hit two distinct resumed blockers, then paused/downgraded.

## Current objective

Prove the Voice Contact Widget V1 model-backed Hugging Face Space path on
`t4-medium` with both model legs running inside the same Space.

## Workflow lanes used

- Runtime Feasibility: `product/workflow/MODEL_RUNTIME_FEASIBILITY.md`
- Sponsor Model Proof: `product/workflow/SPONSOR_MODEL_PROOF.md`
- HF Space Shipping: `product/workflow/HF_SPACE_SHIPPING.md`
- Artifacts/Handoff: `product/workflow/ARTIFACTS_AND_HANDOFF.md`

Prompt cards used:

- `product/workflow/prompts/gated-model-access-preflight.md`
- `product/workflow/prompts/sponsor-model-integration-smoke.md`
- `product/workflow/prompts/hf-space-deploy-and-proof.md`
- `product/workflow/prompts/thread-handoff-evidence-ledger.md`

Not used:

- UX/UAT Evidence. No browser/mobile hosted flow proof was claimed.
- Modal Sidecar. Modal remains out of scope for V1.
- Submission Readiness. No judge-ready claim was made.

## Proof claim

Intended run label: `Hosted Space With Space-Local Model`.

Intended runtime axes:

```text
lifecycle_stage=staging
app_host=hf_space
model_runtime=hf_space
model_backend=nemo+llama.cpp
inference_engine=nemo+llama.cpp
model_artifact_format=nemo_archive+gguf
quantization=unknown+q8_0
model_id=nvidia/nemotron-3.5-asr-streaming-0.6b+CohereLabs/tiny-aya-fire-GGUF:Q8_0
fallback_used=false
```

Actual result: blocked before hosted model smoke. Do not claim hosted model
proof or sponsor-model proof from this attempt.

## Durable artifacts to trust

- Space package root: `product/5-idea-voice-contact-widget/v1/space/`
- Staging Space repo id: `aitacu/vcw-v1-t4-space-local`
- App URL: `https://aitacu-vcw-v1-t4-space-local.hf.space`
- Namespace env: `HF_1`
- Token env: `HF_TOKEN_1`
- SDK: Docker Space
- Requested paid hardware during attempt: `t4-medium`
- Final safety state after blocker: Space paused, requested hardware downgraded
  to `cpu-basic`.
- Resume check after continuation: Space still reported `stage=PAUSED`,
  `hardware=None`, `requested_hardware=cpu-basic`, `raw_error=null`.

Uploaded commits:

- `cc9392285903e359e5be4edaf6bfbaeb660cbbce`: initial Docker Space package.
- `682fb5987c9a0c0454906c3c5d50b2f389019e9a`: switched llama-cpp-python to
  CPU install path after CUDA wheel build was too slow/unavailable.
- `ece2b9714929e7dbfb22e70e88e90b8bb1805bc0`: pinned available
  `llama-cpp-python==0.3.29` CPU wheel.

## Verification state

Model-file access preflight passed with `HF_TOKEN_1` without GPU spend:

- `nvidia/nemotron-3.5-asr-streaming-0.6b` file
  `nemotron-3.5-asr-streaming-0.6b.nemo`: access pass, size `2368284501`
  bytes.
- `CohereLabs/tiny-aya-fire-GGUF` file `tiny-aya-fire-q8_0.gguf`: access pass,
  size `3570654816` bytes.

Local/package checks passed:

```bash
.venv/bin/python -m py_compile product/5-idea-voice-contact-widget/v1/space/app.py
.venv/bin/python product/5-idea-voice-contact-widget/v1/space/app.py --check
cmp -s product/5-idea-voice-contact-widget/v1/onboarding/metime-to.json product/5-idea-voice-contact-widget/v1/space/onboarding/metime-to.json
```

Local deterministic API smoke passed at `http://127.0.0.1:7862`:

- `/health` returned `app_host=local`, `model_runtime=none`,
  `fallback_used=true`, `concurrency=1`.
- `/api/process` returned deterministic transcript/message with
  `asr_language_hint=hi-IN`.
- `/api/send` wrote the demo ledger path with `email_provider=ledger`.

Latest local deterministic trace from continuation:

```text
trace_id=vcw_98c54360a5f8
speech_mode=hinglish
asr_language_hint=hi-IN
model_runtime=none
fallback_used=true
text_model_id=CohereLabs/tiny-aya-fire-GGUF:Q8_0
```

No-paid dependency checks passed:

```bash
.venv/bin/python - <<'PY'
from packaging.requirements import Requirement
from pathlib import Path
for raw in Path('product/5-idea-voice-contact-widget/v1/space/requirements.txt').read_text().splitlines():
    line = raw.strip()
    if line and not line.startswith('#'):
        Requirement(line)
PY

.venv/bin/python -m pip install --dry-run --no-deps -r product/5-idea-voice-contact-widget/v1/space/requirements.txt

.venv/bin/python -m pip download --only-binary=:all: --platform manylinux2014_x86_64 --python-version 310 --implementation cp --abi cp310 --dest /tmp/vcw-wheel-check-2 llama-cpp-python==0.3.29 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

The dry-run resolved the corrected NeMo direct reference to
`nemo-toolkit-3.1.0+95f92737c`. The `llama-cpp-python==0.3.29` Linux/Python
3.10 wheel was available from the configured CPU wheel index.

Continuation hardening:

- NeMo is now pinned to the exact commit resolved by the successful dry-run:
  `95f92737cfb8ee0123bb328b07a2d24c6d859aff`.
- Docker now pins the CUDA PyTorch wheels observed in the prior Space build:
  `torch==2.6.0+cu124` and `torchaudio==2.6.0+cu124`.
- The exact torch/torchaudio wheels were verified with:

```bash
.venv/bin/python -m pip download --no-deps --only-binary=:all: --platform linux_x86_64 --python-version 310 --implementation cp --abi cp310 --dest /tmp/vcw-torch-wheel-check-nodeps 'torch==2.6.0+cu124' 'torchaudio==2.6.0+cu124' --index-url https://download.pytorch.org/whl/cu124
```

Note: using `--platform manylinux2014_x86_64` is the wrong check for PyTorch's
CUDA wheel index here; the wheels are tagged `linux_x86_64`.

Hosted proof status:

- Space package uploaded.
- `t4-medium` was requested.
- Hosted model-backed smoke did not run.
- No trace with `fallback_used=false` exists from this attempt.

## Open blockers

Blocker 1: `llama-cpp-python==0.3.5` was not available as a Python 3.10 CPU
wheel from the configured wheel index. The first replacement build also spent
time compiling from source. Smallest fix applied locally and uploaded:
`llama-cpp-python==0.3.29`, which was verified by local wheel availability
check for `cp310`/manylinux.

Blocker 2: pip rejected the NeMo requirement syntax:

```text
The 'nemo_toolkit[asr]' egg fragment is invalid
from 'git+https://github.com/NVIDIA/NeMo.git@main#egg=nemo_toolkit[asr]'
```

Smallest next fix applied locally but not redeployed because the two-blocker
stop condition fired:

```text
nemo_toolkit[asr] @ git+https://github.com/NVIDIA/NeMo.git@95f92737cfb8ee0123bb328b07a2d24c6d859aff
```

This corrected requirement was later verified locally with both
`packaging.requirements.Requirement` and `pip install --dry-run --no-deps`.

## Next thread should start with

1. Confirm the Space remains paused and requested hardware is `cpu-basic`.
2. If @cu re-approves another paid attempt, upload the current local package.
   It includes the corrected NeMo requirement and the verified
   `llama-cpp-python==0.3.29` wheel pin.
3. Request `t4-medium` only, keep sleep policy bounded, and poll the Docker
   build.
4. After the Space reaches `RUNNING`, call `/health`, then run one 15-30 second
   Hindi or Hinglish `/api/process` request with `audio_base64`.
5. Accept proof only if the trace shows `fallback_used=false` and the intended
   runtime axes above.
6. Pause or downgrade the Space immediately after proof or blocker.

## Do not redo

- Do not re-check only repo metadata for gated models. The real required files
  have already passed token-backed metadata access.
- Do not pin `llama-cpp-python==0.3.5` for this Space's Python 3.10 Docker
  target.
- Do not use `#egg=nemo_toolkit[asr]` in requirements with current pip.
- Do not claim hosted Space model proof from local deterministic fallback.

## Learning delta

For Python 3.10 Docker Spaces, verify wheel availability for native packages
with `pip download --only-binary=:all: --platform manylinux2014_x86_64
--python-version 310 --implementation cp --abi cp310` before starting paid
hardware builds.

## Superseding resumed proof after blocker limit update to 25

Continuation approval:

- @cu approved proceeding toward the goal and changed the runtime blocker limit
  to `25`.
- Paid hardware remained restricted to `t4-medium`.
- Stop condition remained: stop after first successful model-backed smoke,
  guardrail exhaustion, or explicit blocker classification.

Pre-run safety state:

```text
stage=PAUSED
hardware=None
requested_hardware=cpu-basic
raw_error=None
```

Paid runtime request:

- Requested exactly `t4-medium` for Space
  `aitacu/vcw-v1-t4-space-local`.
- Space advanced through `BUILDING` and `APP_STARTING`.
- Space reached:

```text
stage=RUNNING
hardware=t4-medium
requested_hardware=t4-medium
raw_error=None
```

Authenticated `/health` on hosted Space returned HTTP 200 with:

```text
lifecycle_stage=staging
app_host=hf_space
model_runtime=hf_space
model_backend=nemo+llama.cpp
inference_engine=nemo+llama.cpp
model_artifact_format=nemo_archive+gguf
quantization=unknown+q8_0
model_mode=real
fallback_used=false
concurrency=1
```

Successful hosted audio smoke:

- Request: authenticated `POST /api/process`.
- Audio: 15 second public Hindi FLEURS clip,
  `/tmp/vcw-fleurs-hi-smoke.wav`.
- Speech mode: `hindi`.
- ASR language hint: `hi-IN`.
- HTTP status: `200`.
- Wall-clock request time: `116.5` seconds.

Successful trace:

```text
trace_id=vcw_4e2f51bade48
created_at=2026-06-14T18:14:50.717615+00:00
site_id=metime-to
speech_mode=hindi
asr_language_hint=hi-IN
audio_eval_consent=true
visitor_notice_shown=true
raw_audio_retained=true
retain_transcript_for_eval=true
retain_generated_message_for_eval=true
asr_model_id=nvidia/nemotron-3.5-asr-streaming-0.6b
text_model_id=CohereLabs/tiny-aya-fire-GGUF:Q8_0
lifecycle_stage=staging
app_host=hf_space
model_runtime=hf_space
model_backend=nemo+llama.cpp
inference_engine=nemo+llama.cpp
model_artifact_format=nemo_archive+gguf
quantization=unknown+q8_0
model_id=nvidia/nemotron-3.5-asr-streaming-0.6b+CohereLabs/tiny-aya-fire-GGUF:Q8_0
fallback_used=false
fallback_reason=None
audio_size_bytes=480044
audio_duration_ms=15000
```

Trace timings:

```text
asr_load=71118 ms
text_load=10747 ms
asr=2499 ms
text=29258 ms
total=31756 ms
```

ASR output observed:

```text
ऐसी कोई वैश्विक परिभाषा नहीं है जिसके लिए निर्मित समान एंटीक होते हैं, कुछ कर एजेंसियां सौ साल से पुराने सामान को एंटीक के तौर पर परिभाषित करती हैं।
```

tiny-aya Q8_0 English contact-form message observed:

```text
Could you please provide your order ID and delivery address so we can assist you better?
```

Post-proof safety state after pause/downgrade:

```text
stage=PAUSED
hardware=None
requested_hardware=cpu-basic
raw_error=None
```

Proof status:

- Hosted Space loaded on `t4-medium`.
- One real audio request completed ASR through NeMo/PyTorch and text
  generation through llama.cpp / tiny-aya Q8_0.
- Required runtime axes were present.
- `fallback_used=false`.

## Hosted UI Fix Update

Date: 2026-06-15 IST

Run label: `Hosted Space Dry Run`

Scope:

- Upload the V1 widget visibility/debug fixes to the existing private staging
  Space.
- Verify only non-inference hosted behavior.
- Do not send a new audio request through `/api/process`.

Space:

```text
repo_id=aitacu/vcw-v1-t4-space-local
url=https://aitacu-vcw-v1-t4-space-local.hf.space
namespace_env=HF_1
token_env=HF_TOKEN_1
lifecycle_stage=staging
sdk=docker
hardware=t4-medium
visibility=private
```

Uploaded commit:

```text
162c9dda5dea47ece762a5ceb7721fcc3acb218a
Fix hidden widget panels and add V1 smoke script
```

Files updated in the Space:

- `static/widget.css`: restores `[hidden] { display: none !important; }` so
  default hidden panels do not leak into the visitor UI.
- `static/widget.js`: keeps debug `send-failure` from calling `/api/process`
  without audio.
- `app.py`: accepts `simulate` on `/api/send` and returns the intended send
  failure before writing the ledger.
- `tools/smoke_api.py`: reusable non-inference hosted smoke helper.
- `README.md`: documents the smoke helper.

Hosted status after rebuild:

```text
stage=RUNNING
runtime_sha=162c9dda5dea47ece762a5ceb7721fcc3acb218a
hardware.current=t4-medium
hardware.requested=t4-medium
domain_stage=READY
```

Non-inference hosted smoke:

```bash
python3 product/5-idea-voice-contact-widget/v1/space/tools/smoke_api.py --include-traces
```

Result:

```text
/health HTTP 200
/api/packet HTTP 200
/api/traces HTTP 200
app_host=hf_space
model_runtime=hf_space
model_backend=nemo+llama.cpp
inference_engine=nemo+llama.cpp
model_artifact_format=nemo_archive+gguf
quantization=unknown+q8_0
model_mode=real
fallback_used=false
```

Additional hosted checks:

```text
/static/widget.css HTTP 200 and contains [hidden]
/static/widget.js HTTP 200 and contains debug-send-failure
/api/send simulate=send_failure returned HTTP 502 with expected detail
```

Proof boundary:

- This proves the hosted Space is updated and serving the UI/debug fixes.
- This does not prove a new ASR/text model trace.
- This does not resolve the separate model-path quality/robustness issues seen
  in earlier traces, including empty ASR transcript and tiny-aya hallucinated
  support/order fields.
- This proves only the tested hosted trace; it does not claim judge-ready
  readiness, broad language support, production reliability, or quality beyond
  this smoke.
