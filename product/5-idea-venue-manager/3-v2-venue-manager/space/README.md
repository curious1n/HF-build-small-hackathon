---
title: Venue Manager Agent
emoji: 🏟️
colorFrom: green
colorTo: indigo
sdk: gradio
sdk_version: 6.18.0
app_file: app.py
pinned: false
---

# Floodlight Venue Manager

Floodlight Venue Manager is a custom venue-ops console for sports venue owners.
It turns WhatsApp-style booking requests into an owner-reviewable queue,
calendar context, booking details, reply drafts, and safe approval flow.

## Links

- App: [build-small-hackathon-venue-manager-agent.hf.space](https://build-small-hackathon-venue-manager-agent.hf.space)
- Source repo: [curious1n/HF-build-small-hackathon](https://github.com/curious1n/HF-build-small-hackathon)
- HF Article: [Venue Manager Running Notes](https://huggingface.co/blog/build-small-hackathon/venue-manager-running-notes)
- Agent traces: [modal demo-world suite rows](https://github.com/curious1n/HF-build-small-hackathon/tree/main/product/5-idea-venue-manager/3-v2-venue-manager/evidence/modal-demo-world-suite-20260615-131029)

## Demo Flow

1. Open the Floodlight venue-ops console.
2. Review the synthetic venue day, queue, calendar, and booking detail panel.
3. Use `Reload Demo` to return to the immutable seed world.
4. Send a simulator booking request.
5. Review the extracted booking, trace panel, reply draft, and owner approval
   state.

## Models And Runtime

Runtime path for this v2 demo:

- App host: Hugging Face Space.
- Visible product: custom Floodlight venue-ops console.
- Demo world: one immutable synthetic seed with temporary runtime mutations.
- Reset: top-right `Reload Demo` restores the seed world.
- Model runtime: Modal, when configured.
- Model: `nvidia/Nemotron-Cascade-2-30B-A3B`.
- Local/hosted UI demo uses fixture-shaped simulator extraction unless Modal
  config is supplied.
- No deterministic model fallback is claimed as model proof.

## Evidence

- Local UAT: `../evidence/local-uat.md`
- Hosted Space dry run: `../evidence/hf-space-deploy.md`
- Modal single-scenario smoke: `../evidence/modal-world-smoke-2026-06-15.md`
- Modal demo-world suite: `../evidence/modal-demo-world-suite-2026-06-15.md`
- Agent trace rows: `../evidence/modal-demo-world-suite-20260615-131029/rows.jsonl`

Proof claimed by this Space README:

- The hosted package serves the Floodlight app shell and demo-world endpoints.
- The app exposes simulator booking and trace-review surfaces.
- Modal-backed extraction can be wired when the required Space secrets are set.

Not claimed by this Space README:

- Public release readiness.
- Judge-ready status.
- Live WhatsApp/Baileys send.
- External scoring/admin or video telecast integration.

## API Surface

Frontend/API integration:

- Demo seed endpoint: `GET /api/bootstrap`.
- Demo reset endpoint: `POST /api/reload-demo`.
- Simulator conversation endpoint: `POST /api/whatsapp/simulated-message`.
- Booking extraction endpoint: `POST /api/extract-booking`.
- The browser calls the Space endpoint only; the Space server calls Modal
  privately when Modal config is set.

Optional Space configuration for Modal-backed extraction:

- `APP_MODAL_BASE_URL`
- `APP_MODAL_AUTH_TOKEN`
- `APP_MODAL_TIMEOUT_SECONDS`
- `APP_MODAL_MODEL_ID`

## Known Limits

- The default hosted demo proves the app shell and fixture-backed simulator
  flow only.
- Fresh hosted Space-to-Modal proof requires a separate `fallback_used=false`
  hosted smoke.
- The Venue Manager HF Article should be updated from `../articles/running-notes.md`
  when the local source changes.
