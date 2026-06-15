# Voice Contact Widget V1 Implementation Readiness

Last updated: 2026-06-14

## Locked Product Slice

Build V1 from this folder only.

User: a mobile visitor contacting metime.to.

Trigger: the visitor wants to send a contact message without typing a full
English note.

Smallest success:

- load metime.to onboarding packet;
- render branded widget;
- choose `Hindi` or `Hinglish`;
- record audio;
- generate transcript with Nemotron ASR;
- generate editable English message with tiny-aya Q8_0;
- send to configured destination or demo ledger;
- record trace metadata and eval retention fields.

## Human-Approved Decisions

- `contact_email=founders@metime.to`.
- Generate reasonable metime.to brand tokens.
- `audio_eval_consent=true` for metime.to.
- Three runtime locations, recorded in `deployment-targets.json`:
  - Modal-hosted model sidecar for testing only.
  - HF_2-owned `t4-medium` Space for testing the HF GPU path.
  - HF hackathon-org `t4-medium` Space for official submission.
- Modal must be disabled for submission by setting `VCW_MODEL_RUNTIME=hf_space`.
- No English speech option in UI.

## Build Shape

Recommended files for implementation:

```text
product/5-idea-voice-contact-widget/v1/space/
  app.py
  requirements.txt
  README.md
  static/
    widget.css
    widget.js
product/5-idea-voice-contact-widget/v1/onboarding/metime-to.json
```

The implementation can choose Gradio for hosting/backend callbacks, but the
first visible widget should be custom and visitor-first.

## Data Contracts

Onboarding packet:

- loaded from `onboarding/metime-to.json`;
- validates required keys before launch;
- values appear in debug provenance.

Trace record:

```json
{
  "trace_id": "string",
  "site_id": "metime-to",
  "speech_mode": "hindi|hinglish",
  "asr_language_hint": "hi-IN|auto",
  "audio_eval_consent": true,
  "visitor_notice_shown": true,
  "raw_audio_retained": true,
  "asr_model_id": "nvidia/nemotron-3.5-asr-streaming-0.6b",
  "text_model_id": "CohereLabs/tiny-aya-fire-GGUF:Q8_0",
  "fallback_used": false,
  "timings_ms": {}
}
```

Send payload:

```json
{
  "site_id": "metime-to",
  "contact_email": "founders@metime.to",
  "model_message_en": "string",
  "final_message_en": "string",
  "user_edited": true,
  "trace_id": "string"
}
```

## Acceptance Criteria

Local/package proof:

- app imports;
- packet validates;
- UI renders with metime.to tokens;
- segmented control has only Hindi/Hinglish;
- no visible English speech option.

Runtime proof, when authorized:

- Space runs on `t4-medium`;
- ASR model loads through NeMo;
- tiny-aya Q8_0 loads through llama.cpp or llama-cpp-python;
- real audio returns transcript and English message;
- send path reaches email or demo ledger;
- trace shows `fallback_used=false` for model-backed proof.

UX/UAT proof, later:

- desktop and mobile browser recording path;
- mic denied state;
- empty/short recording state;
- processing state;
- review/edit/send;
- eval notice shown when packet enables audio retention.

## Stop Conditions

Stop and ask @cu before:

- changing selected models;
- introducing Modal;
- showing English as a speech option;
- disabling metime.to eval collection;
- publishing or claiming judge-ready;
- leaving paid hardware running without a bounded approval.
