# Tiny Aya Intent Preservation Plan

Last updated: 2026-06-15

## Issue

The first hosted model-backed V1 smoke proved the plumbing but exposed a text
quality bug. Nemotron ASR returned a Hindi transcript about antique definitions,
then `CohereLabs/tiny-aya-fire-GGUF:Q8_0` drafted:

```text
Could you please provide your order ID and delivery address so we can assist you better?
```

That output did not preserve the transcript's intent. It invented support
fields and a customer-service scenario that were not present in the ASR text.

Current suspected cause:

- The text model is asked to produce broad support-style metadata:
  `intent`, `missing_fields`, and `safety_flags`.
- The prompt says "contact-form message" but does not strongly distinguish
  literal preservation from support-ticket completion.
- The app currently trusts model-owned business metadata instead of keeping
  field validation and risk flags in deterministic code.

## Provider Notes Being Applied

- The selected text model is `CohereLabs/tiny-aya-fire-GGUF:Q8_0`.
- The parent Tiny Aya Fire model card describes a text-only autoregressive
  multilingual model, strongest for clear prompts and multilingual generation,
  with Hindi in the covered language list.
- The provider usage example formats requests through the tokenizer chat
  template and uses low temperature (`0.1`) with `top_p=0.95`.
- The GGUF page lists `llama-cpp-python` and `llama.cpp` usage for local apps.

## Plan

1. Narrow tiny-aya's job to one model-owned task: rewrite/translate the ASR
   transcript into an English contact message.
2. Remove model-required support metadata fields from the prompt contract:
   `intent` and `missing_fields`.
3. Keep business/state checks in deterministic Python:
   - normalize the model output schema;
   - detect invented support fields;
   - mark `needs_edit=true` when the transcript is unclear, unrelated, or the
     draft adds support fields not present in the transcript.
4. Prefer `llama-cpp-python` chat completion when available, with a raw prompt
   fallback for compatibility.
5. Add a V1 seed fixture set that catches this exact failure mode:
   unrelated transcript must not create order, delivery, payment, refund,
   address, phone, email, account, or booking fields.
6. Run local deterministic/contract tests first.
7. Deploy the fix to the private staging Space and run one paid hosted
   model-backed check within the approved `$5` budget.
8. Stop paid hardware after the hosted check or blocker capture.

## Paid Hosted Check Boundary

Approved budget from @cu: `$5`.

Stop condition:

- one hosted model-backed `/api/process` request after the prompt fix, or
- first hosted blocker that prevents the request from completing, or
- cost risk approaches the approved budget.

Required evidence:

- Space repo id, URL, commit SHA, hardware, and lifecycle stage;
- runtime axes for the hosted check;
- `fallback_used` value;
- transcript, generated message, guardrail flags, latency, and blocker if any;
- whether forbidden support fields were absent or caught.

## Findings

### Local Build Findings

Status: pass for prompt contract and deterministic guardrail.

Files changed:

- `space/app.py`
- `space/tools/smoke_api.py`
- `tests/test_tiny_aya_prompting.py`
- `eval/cases/tiny_aya_seed_cases.jsonl`

Implementation notes:

- tiny-aya prompt now asks for only:
  - `message_en`
  - `confidence`
  - `needs_edit`
  - `notes`
- The prompt no longer asks tiny-aya for `intent` or `missing_fields`.
- The adapter prefers `llama-cpp-python` chat completion with low temperature
  (`0.1`) and `top_p=0.95`, with a raw completion fallback.
- Deterministic Python now detects unsupported support-field terms in the
  generated message when the transcript did not contain matching cues.
- A private staging/eval endpoint, `/api/text-smoke`, was added so the hosted
  check can exercise tiny-aya with a supplied transcript without rerunning ASR.

Local verification:

```bash
PYTHONPYCACHEPREFIX=/tmp/vcw_v1_pycache python3 -m py_compile \
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
4 passed in 2.29s
```

```bash
PYTHONPYCACHEPREFIX=/tmp/vcw_v1_pycache .venv/bin/python \
  product/5-idea-voice-contact-widget/v1/space/app.py --check
```

Result: pass; local deterministic mode reports `fallback_used=true`.

Environment note:

- System `python3 -m pytest` is unavailable because system Python does not have
  `pytest`.
- System `python3 -m py_compile` needed `PYTHONPYCACHEPREFIX` because the macOS
  Python cache path under `~/Library/Caches` is outside the workspace sandbox.

### Hosted Findings

Status: pass for hosted Space-local model reachability and guarded Tiny Aya
review behavior; quality remains limited.

Evidence:

- `evidence/hf-space-guardrail-smoke-2026-06-15.md`

Uploaded Space commits:

- `ac5bbd8bfc32e80649d641c8c92ad3d6753aa9ae`
- `1c8ae83e3c5df38f3b548d9c2286d1968a9f3d96`

Hosted verification:

- `/health` returned `model_mode=real`, `model_runtime=hf_space`, and
  `fallback_used=false`.
- Three hosted `/api/text-smoke` examples returned HTTP 200 with
  `fallback_used=false`.
- One hosted `/api/process` audio smoke returned HTTP 200 with
  `fallback_used=false`.

Important result:

- The original antique transcript still caused Tiny Aya to hallucinate a
  Metime appointment and phone callback, but the app now parses the nested
  `output_schema` response and marks the draft with
  `missing_preservation_cues:antique` and
  `unsupported_support_fields:phone,booking`.
- A pricing audio smoke completed ASR plus text generation, but Tiny Aya
  dropped pricing in the final draft; the app marked
  `missing_preservation_cues:pricing`.

Final Space safety state:

```text
stage=PAUSED
hardware=None
requested_hardware=t4-medium
sleep_time=900
raw_error=None
```
