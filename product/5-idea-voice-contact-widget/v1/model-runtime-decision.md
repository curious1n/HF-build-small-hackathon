# Voice Contact Widget V1 Model And Runtime Decision

Last updated: 2026-06-14

## Decision

Run both selected model legs inside one Hugging Face Space on `t4-medium`
hardware. Do not use Modal.

| Role | Model | Engine | Format | Quantization | Runtime |
| --- | --- | --- | --- | --- | --- |
| ASR | `nvidia/nemotron-3.5-asr-streaming-0.6b` | NVIDIA NeMo / PyTorch | `.nemo` checkpoint | Not specified on card | HF Space-local |
| Text rewrite / translation | `CohereLabs/tiny-aya-fire-GGUF:Q8_0` | `llama.cpp` / `llama-cpp-python` | GGUF | Q8_0 | HF Space-local |

Runtime axes for the intended model-backed proof:

```text
lifecycle_stage=testing
app_host=hf_space
model_runtime=hf_space
model_backend=nemo+llama.cpp
inference_engine=nemo+llama.cpp
model_artifact_format=nemo_archive+gguf
quantization=unknown+q8_0
fallback_used=false only after smoke
```

## Language Decision

Visible speech modes:

- `Hindi`
- `Hinglish`

Do not expose English, Kannada, Tamil, arbitrary language, model selection, or
ASR language IDs in the visitor UI.

Mapping:

```text
Hindi:
  speech_mode=hindi
  ASR target_lang=hi-IN
  output=en

Hinglish:
  speech_mode=hinglish
  ASR target_lang=hi-IN or auto, pending smoke
  output=en
```

## Prompt Contract

The text model receives structured context:

```json
{
  "site_id": "metime-to",
  "asr_transcript": "...",
  "speech_mode": "hinglish",
  "asr_language_hint": "hi-IN",
  "target_output_language": "en",
  "task": "Create a concise English contact-form message.",
  "rules": [
    "Preserve the user's intent.",
    "Do not invent names, phone numbers, emails, order IDs, prices, payment status, delivery outcomes, addresses, or links.",
    "If the transcript is unclear or language-mismatched, set needs_edit=true."
  ]
}
```

Expected parsed output:

```json
{
  "message_en": "string",
  "intent": "string",
  "confidence": 0.0,
  "needs_edit": true,
  "safety_flags": ["string"],
  "missing_fields": ["string"]
}
```

## Proof Boundary

This document is not hosted proof or model proof. A fresh implementation thread
must still prove:

- Space starts on `t4-medium`;
- both model legs load in the Space;
- real audio flows through ASR and text;
- visitor flow completes with `fallback_used=false`;
- known failures are visible and recoverable.
