# Voice Contact Widget V1 Product Brief

Last updated: 2026-06-14

## Product Frame

Voice Contact Widget V1 is an embedded contact widget for `metime.to`. A
visitor speaks in Hindi or Hinglish, receives an editable English message, and
sends it to `founders@metime.to`.

Primary user:

- a mobile website visitor who can explain their request faster by speaking
  than by typing in English.

Site owner:

- `metime.to`, represented in V1 by an onboarding packet.

Trigger:

- the visitor reaches a contact moment and wants to send a message.

Smallest success:

- visitor selects `Hindi` or `Hinglish`;
- records a short voice note;
- gets an English draft;
- edits if needed;
- sends the final message;
- backend records model/runtime provenance and the configured metime.to packet.

Demo promise:

```text
Speak in Hindi or Hinglish. We will draft an English message you can review and send.
```

## In Scope

- One end-user packet for `metime.to`.
- `founders@metime.to` as contact destination.
- Generated metime.to design tokens.
- Hindi/Hinglish segmented control.
- Browser microphone recording.
- ASR through `nvidia/nemotron-3.5-asr-streaming-0.6b`.
- Text rewrite/translation through `CohereLabs/tiny-aya-fire-GGUF:Q8_0`.
- Same HF Space runtime on `t4-medium`.
- Explicit review/edit/send flow.
- Demo ledger fallback when email delivery credentials are absent.
- Audio eval collection enabled for metime.to, with visitor notice recorded.

## Out Of Scope

- Modal.
- English as a selectable speech mode.
- Kannada, Tamil, or arbitrary-language claims.
- Model selector UI for visitors.
- Multi-tenant admin UI.
- Production embed SDK.
- CRM integration.
- Always-on or judge-ready hosting proof.
- Claiming quality or `fallback_used=false` before a real smoke.

## Privacy Position

The onboarding packet can enable audio collection for eval. Default is no for
future end users, but metime.to enables it for V1.

Visitor-facing UI must still make audio retention visible before recording. For
the hackathon V1 build, notice-plus-metadata consent is acceptable:

```text
metime.to allows recordings to be used to improve this demo. Do not share sensitive information.
```

The app should record:

- `audio_eval_consent=true` from the packet;
- `visitor_notice_shown=true` when the notice is rendered;
- `raw_audio_retained=true|false` per request.
