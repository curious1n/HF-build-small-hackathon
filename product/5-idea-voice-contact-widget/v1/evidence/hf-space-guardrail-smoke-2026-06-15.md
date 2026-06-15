# V1 HF Space Tiny Aya Guardrail Smoke

Date: 2026-06-15

## Scope

Run label:

- `Hosted Space With Space-Local Model`

Workflow lanes:

- Feature-First: `product/workflow/FEATURE_FIRST.md`
- Product Briefing: `product/workflow/PRODUCT_BRIEFING.md`
- Runtime Feasibility: `product/workflow/MODEL_RUNTIME_FEASIBILITY.md`
- Sponsor Model Proof: `product/workflow/SPONSOR_MODEL_PROOF.md`
- HF Space Shipping: `product/workflow/HF_SPACE_SHIPPING.md`

Prompt cards:

- `product/workflow/prompts/sponsor-model-integration-smoke.md`
- `product/workflow/prompts/hf-space-deploy-and-proof.md`

Proof boundary:

- Claim hosted staging proof for the Space-local model path and the V1 Tiny Aya
  guardrail behavior.
- Do not claim judge-ready, broad quality, production reliability, public
  release, or final hackathon submission readiness.

## Space

```text
repo_id=aitacu/vcw-v1-t4-space-local
url=https://aitacu-vcw-v1-t4-space-local.hf.space
namespace_env=HF_1
token_env=HF_TOKEN_1
lifecycle_stage=staging
sdk=docker
hardware=t4-medium during smoke
visibility=private
```

Uploaded commits:

- `ac5bbd8bfc32e80649d641c8c92ad3d6753aa9ae`: deployed app version bump,
  deploy helper, and Tiny Aya chat-completion default.
- `1c8ae83e3c5df38f3b548d9c2286d1968a9f3d96`: hardened Tiny Aya parser and
  guardrails after the first hosted text-smoke exposed nested `output_schema`
  output plus appointment/phone hallucination.

Final safety state:

```text
stage=PAUSED
hardware=None
requested_hardware=t4-medium
sleep_time=900
raw_error=None
```

Budget guard:

- Approved cap: `$10`.
- Requested hardware: `t4-medium` only.
- Sleep guard used: `900` seconds.
- At the current HF listed `t4-medium` rate used by the deploy helper
  (`$0.60/hour`), each 900 second window is bounded to about `$0.15` before
  manual pause. Actual billing was not retrieved from HF.

## Local Verification

```bash
PYTHONPYCACHEPREFIX=/tmp/vcw_v1_pycache python3 -m py_compile \
  product/5-idea-voice-contact-widget/v1/deploy_space.py \
  product/5-idea-voice-contact-widget/v1/space/app.py \
  product/5-idea-voice-contact-widget/v1/space/tools/smoke_api.py
```

Result: pass.

```bash
PYTHONPYCACHEPREFIX=/tmp/vcw_v1_pycache .venv/bin/python -m pytest \
  product/5-idea-voice-contact-widget/v1/tests -q
```

Result:

```text
5 passed
```

```bash
PYTHONPYCACHEPREFIX=/tmp/vcw_v1_pycache .venv/bin/python \
  product/5-idea-voice-contact-widget/v1/space/app.py --check
```

Result: pass with local deterministic mode, `fallback_used=true`.

Token-backed model-file preflight before paid hardware:

```text
nvidia/nemotron-3.5-asr-streaming-0.6b / nemotron-3.5-asr-streaming-0.6b.nemo: pass
CohereLabs/tiny-aya-fire-GGUF / tiny-aya-fire-q8_0.gguf: pass
```

## Hosted Status

Hosted `/health` after deploy:

```text
app_host=hf_space
model_runtime=hf_space
model_backend=nemo+llama.cpp
inference_engine=nemo+llama.cpp
model_artifact_format=nemo_archive+gguf
quantization=unknown+q8_0
model_mode=real
fallback_used=false
version=v1-space-local-model-2026-06-15
```

## Hosted Text Examples

### Antique Failure Regression

Endpoint: authenticated `POST /api/text-smoke`

Trace:

```text
trace_id=vcw_3ef91bfa4bfe
speech_mode=hindi
fallback_used=false
timings_ms.text_load=16251
timings_ms.text=63790
```

Input transcript:

```text
ऐसी कोई वैश्विक परिभाषा नहीं है जिसके लिए निर्मित समान एंटीक होते हैं, कुछ कर एजेंसियां सौ साल से पुराने सामान को एंटीक के तौर पर परिभाषित करती हैं।
```

Tiny Aya output:

```text
Hello, I need to book a Metime appointment. Please call me at 9876543210.
```

Guardrail result:

```text
needs_edit=true
guardrail_flags=[
  missing_preservation_cues:antique,
  unsupported_support_fields:phone,booking
]
```

Interpretation:

- Hosted real Tiny Aya still hallucinated on this bad/irrelevant transcript.
- The app no longer fails with HTTP 424 for the nested `output_schema` response.
- The app now marks the draft as unsafe for clean send/review.

### Pricing Callback

Endpoint: authenticated `POST /api/text-smoke`

Trace:

```text
trace_id=vcw_74c901bc471e
speech_mode=hinglish
fallback_used=false
timings_ms.text=31563
```

Input transcript:

```text
Hi, mujhe metime.to ke pricing aur availability ke baare mein baat karni hai, please mujhe call back kar dijiye.
```

Tiny Aya output:

```text
Hi, I would like to discuss the pricing and availability of metime.to. Please call me back.
```

Guardrail result:

```text
needs_edit=true
guardrail_flags=[]
```

Interpretation:

- Draft preserved the central request.
- `needs_edit=true` came from normalized model confidence, not a guardrail
  violation.

### Order Delivery Control

Endpoint: authenticated `POST /api/text-smoke`

Trace:

```text
trace_id=vcw_6c3f8a33d280
speech_mode=hinglish
fallback_used=false
timings_ms.text=31047
```

Input transcript:

```text
Mera order aaj delivery hona tha, abhi tak status nahi mila. Please delivery status bata dijiye.
```

Tiny Aya output:

```text
Your order was supposed to be delivered today, but we haven't received the delivery status yet. Please provide the delivery status.
```

Guardrail result:

```text
needs_edit=true
guardrail_flags=[]
```

Interpretation:

- Order/delivery terms were allowed because the source transcript included
  those cues.

## Hosted Audio Smoke

Endpoint: authenticated `POST /api/process`

Audio fixture:

```text
product/5-idea-voice-contact-widget/v0/eval/audio/hinglish_pricing_callback.wav
```

Trace:

```text
trace_id=vcw_6992866caad5
speech_mode=hinglish
asr_language_hint=hi-IN
fallback_used=false
timings_ms.asr_load=70906
timings_ms.text_load=1527
timings_ms.asr=3124
timings_ms.text=57485
timings_ms.total=60609
```

ASR output:

```text
नमस्ते, मुझे आपकी सर्विस के प्राइसिंग और अवेलाबीते के बारे में जाना है।  प्लीज मुझे कॉल बैक कर दीजिए।
```

Tiny Aya output:

```text
Hello, I am from Metime. Would you like to know more about our app?
```

Guardrail result:

```text
needs_edit=true
guardrail_flags=[missing_preservation_cues:pricing]
```

Interpretation:

- Full hosted ASR + Tiny Aya model path returned HTTP 200 with
  `fallback_used=false`.
- ASR captured pricing/callback intent well enough to test the text leg.
- Tiny Aya dropped pricing, so the deterministic preservation guardrail marked
  the draft for edit.

## Conclusion

Pass:

- Space deploy succeeded.
- Required model files were token-accessible before paid hardware.
- Hosted Space reached `RUNNING` on `t4-medium`.
- Hosted health showed real model mode and `fallback_used=false`.
- Three hosted Tiny Aya text examples and one hosted audio ASR+Tiny Aya smoke
  returned HTTP 200 with `fallback_used=false`.
- The known Tiny Aya hallucination case is now recovered and visibly guarded
  instead of becoming an opaque model failure or a clean draft.

Known limitation:

- Tiny Aya Q8_0 quality remains uneven for this contact-message rewrite task.
  The current build proves guarded review behavior, not high-quality automatic
  translation.

Do not claim:

- Judge-ready submission.
- Broad Hindi/Hinglish quality.
- Production email delivery.
- Public release approval.
