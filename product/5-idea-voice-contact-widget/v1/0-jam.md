# Voice Contact Widget V1 Jam

Date: 2026-06-14

## Participants

| Participant | Type | Role |
| --- | --- | --- |
| @cu | Human | Product owner, hackathon participant, release decision maker, and approval gate. |
| Codex | AI agent | Product/design/implementation collaborator. |

## Seed

A mobile website visitor wants to contact a business but does not want to type
a full English message. They speak in Hindi or Hinglish. The widget drafts a
clear English contact-form message, lets the visitor review/edit it, and sends
it to the configured site contact.

## V1 Direction

V1 is not a broad model-comparison spike. It is a focused branded demo for
`metime.to`:

- branded by an ingestible end-user onboarding packet;
- configured to send to `founders@metime.to`;
- styled from generated metime.to design tokens;
- allowed to collect audio for eval because the onboarding packet enables it;
- run on a Hugging Face Space with `t4-medium` hardware;
- run without Modal.

## Product Promise

Add a voice contact widget to a site so Hindi/Hinglish-speaking visitors can
leave an English message they control.

## Open Questions For Build-Time Smoke

- For `Hinglish`, does Nemotron perform better with `target_lang=hi-IN` or
  `target_lang=auto`?
- Should audio retention use notice-only consent for the hackathon demo, or an
  explicit visitor checkbox before recording?

V1 implementation may proceed with notice-plus-metadata consent unless @cu
changes this before public release.
