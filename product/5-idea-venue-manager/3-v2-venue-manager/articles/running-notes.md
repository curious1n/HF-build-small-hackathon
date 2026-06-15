# Floodlight Venue Manager Running Notes

Floodlight Venue Manager is a Build Small Hackathon venue-ops assistant for
sports venue owners. It turns WhatsApp-style booking messages into an
owner-reviewed queue, calendar context, booking details, reply drafts, and safe
approval actions.

## Artifacts

- Private Space: https://build-small-hackathon-venue-manager-agent.hf.space
- Source repo: https://github.com/curious1n/HF-build-small-hackathon
- Public Article: https://huggingface.co/blog/build-small-hackathon/venue-manager-running-notes
- Agent traces: https://github.com/curious1n/HF-build-small-hackathon/tree/main/product/5-idea-venue-manager/3-v2-venue-manager/evidence/modal-demo-world-suite-20260615-131029

## Current State

This file is the single running-notes source for the Venue Manager Article.

The hosted Space currently proves the Floodlight app shell and demo-world
endpoints. The Modal/Nemotron trace evidence below is local/demo-world evidence
unless a separate hosted Space-to-Modal smoke records `fallback_used=false`.

## Notes

### 2026-06-15 - Modal Demo-World Trace Note

The v2 demo-world flow has local Modal/Nemotron evidence with
`fallback_used=false` for structured booking extraction against synthetic
venue-owner scenarios.

Artifact snapshot:

- Local evidence summary: `product/5-idea-venue-manager/3-v2-venue-manager/evidence/modal-demo-world-suite-2026-06-15.md`
- Agent trace rows: `product/5-idea-venue-manager/3-v2-venue-manager/evidence/modal-demo-world-suite-20260615-131029/rows.jsonl`
- Model: `nvidia/Nemotron-Cascade-2-30B-A3B`
- Runtime: Modal HTTP extraction path

What ran:

The demo-world suite sent synthetic WhatsApp-style booking requests through the
venue-manager extraction path. The app validated structured output, checked the
request against the synthetic venue day, and recorded trace rows for reviewer
inspection.

What this proves:

- The Modal/Nemotron path can return schema-valid booking extraction output.
- Successful rows record `fallback_used=false`.
- The app records trace fields that connect the input, extraction result,
  validation, runtime axes, and owner-review state.

What this does not prove:

- Public release readiness.
- Judge-ready status.
- Live WhatsApp/Baileys send.
- Broad model quality across real venue traffic.
- Hosted Space-to-Modal proof unless a separate hosted smoke records it.

## Source Provenance

These paths are in the source repo, not necessarily inside the Hugging Face
Space package:

- `product/5-idea-venue-manager/3-v2-venue-manager/space/`
- `product/5-idea-venue-manager/3-v2-venue-manager/evidence/local-uat.md`
- `product/5-idea-venue-manager/3-v2-venue-manager/evidence/hf-space-deploy.md`
- `product/5-idea-venue-manager/3-v2-venue-manager/evidence/modal-world-smoke-2026-06-15.md`
- `product/5-idea-venue-manager/3-v2-venue-manager/evidence/modal-demo-world-suite-2026-06-15.md`
- `product/5-idea-venue-manager/3-v2-venue-manager/evidence/modal-demo-world-suite-20260615-131029/rows.jsonl`
