# Voice Contact Widget V1 UX/UI Design

Last updated: 2026-06-14

## Design Mode

Mode: Detailed Design Light.

Goal: a polished visitor-facing custom widget surface, using Gradio only as the
hosting/event shell where needed. Avoid a stock Gradio-looking first screen.

## Visual Direction

Use the metime.to onboarding tokens:

- calm, personal, focused;
- soft white/lavender surface;
- violet primary action;
- mint accent for success/progress;
- rounded but not bubbly;
- compact mobile-first contact widget, not a landing page.

## Primary Flow

### 1. Entry

The widget appears near a contact moment.

Visible content:

```text
Tell us what you need
Speak in Hindi or Hinglish. We will draft an English message.
```

Controls:

- segmented control: `Hindi | Hinglish`;
- primary record button;
- small eval notice if packet enables audio retention.

### 2. Speech Mode

The visitor chooses:

- `Hindi`: mostly Hindi speech.
- `Hinglish`: natural Hindi/English code-switching.

This is product language, not a model selector. Do not expose ASR hints.

### 3. Recording

States:

- idle: ready to record;
- permission pending;
- recording;
- stopping;
- audio too short;
- microphone denied.

Recording state should be unmistakable and mobile-friendly.

### 4. Processing

Processing should show human progress stages:

```text
Preparing your recording
Listening to your message
Drafting your English message
```

Do not show model names in the default visitor path.

### 5. Review

Show an editable English message.

Primary actions:

- `Send message`;
- `Record again`.

Secondary action:

- `Show transcript`.

If model confidence is low or fields are missing, nudge review rather than
blocking:

```text
Please review before sending. Some details may be missing.
```

### 6. Send

Use explicit send in V1. Do not auto-send.

Backend either sends to configured email or writes to the demo ledger when
email credentials are absent.

### 7. Success

Terminal copy:

```text
Message sent.
Thanks. The team will get back to you.
```

If ledger fallback was used:

```text
Message saved for the demo.
```

### 8. Failure States

| State | Visitor copy | Required action |
| --- | --- | --- |
| Mic denied | Microphone access is blocked. | Show browser permission guidance and retry. |
| Empty audio | We did not catch that. | Record again. |
| ASR failed | We could not understand the recording. | Record again. |
| Text model failed | We got the transcript but could not draft the message. | Let visitor edit transcript or retry. |
| Send failed | Could not send. Your message is still here. | Retry send or copy message. |

## Developer/Debug Surface

Keep debug details collapsed:

- site id;
- packet version;
- ASR model id;
- text model id;
- speech mode;
- ASR hint;
- timings;
- fallback flags;
- eval retention flags;
- trace id.

## Must-Preserve Decisions

- Two-option segmented speech control: `Hindi`, `Hinglish`.
- No visible English speech option.
- Explicit review/edit before send.
- Explicit send only; no auto-send countdown.
- Visitor-facing model details hidden by default.
- Audio eval notice visible when packet enables eval collection.
