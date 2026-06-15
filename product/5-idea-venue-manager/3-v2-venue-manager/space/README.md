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

# Venue Manager Agent

Custom Gradio `Server` app for Floodlight venue booking operations.

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

Proof boundary:

- The default hosted demo proves the local/hosted app shell and fixture-backed
  simulator flow only.
- Fresh Modal proof requires a separate `fallback_used=false` hosted smoke.
- Live WhatsApp/Baileys, external scoring/admin, video telecast, and
  judge-ready submission are not claimed by this package alone.
