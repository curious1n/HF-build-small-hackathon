# Voice Contact Widget V1 End-User Onboarding

Last updated: 2026-06-14

## Purpose

The app ingests an end-user onboarding packet. The packet configures where
messages go, how the widget looks, and whether audio may be collected for eval.

V1 includes one onboarded end user: `metime.to`.

## Packet Contract

Required fields:

- `site_id`: stable lowercase id.
- `brand_name`: display name.
- `contact_email`: message destination.
- `design_tokens`: widget styling tokens.
- `audio_eval_consent`: whether this site permits audio collection for eval.
- `audio_eval_notice`: visitor-facing retention notice.

Default policy:

- `audio_eval_consent` defaults to `false` for future end users.
- metime.to sets it to `true`.
- Even when enabled, the UI must show the notice before recording.

## metime.to Assumptions

The values below are generated assumptions for V1, not scraped brand data.

- Brand name: `metime.to`.
- Contact email: `founders@metime.to`.
- Tone: calm, direct, human, private.
- Visual feel: personal productivity / wellbeing SaaS, light UI, violet
  primary, mint accent.
- Eval: enabled for hackathon improvement traces.

## Ingestible Packet

Canonical packet:

- `onboarding/metime-to.json`

Token export:

- `design/metime-to-tokens.css`

Implementation should load the packet at startup and pass packet values into:

- widget styling;
- send destination;
- trace metadata;
- privacy/eval behavior;
- debug provenance.
