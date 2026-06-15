# Floodlight Venue Manager v2

Clean active folder for the Build Small Hackathon Venue Manager candidate.

This version keeps the Floodlight custom venue-ops console, uses one immutable
demo-world snapshot, and exposes a top-right `Reload Demo` control that clears
temporary runtime changes and reloads that snapshot.

## Run Locally

```bash
cd product/5-idea-venue-manager/3-v2-venue-manager/space
PORT=7862 ../../../../.venv/bin/python app.py
```

Open:

```text
http://127.0.0.1:7862/
```

Modal-backed local runs and HF Space config pushes load idea-specific Modal
client config from:

```text
product/5-idea-venue-manager/.env.modal.local
```

Keep `APP_MODAL_BASE_URL`, `APP_MODAL_AUTH_TOKEN`,
`APP_MODAL_TIMEOUT_SECONDS`, and `APP_MODAL_MODEL_ID` there so Venue Manager
does not inherit another idea's endpoint or model.

## Product Shape

- Primary user: venue owner/operator handling WhatsApp-style booking requests.
- Demo promise: turn a messy live day into an owner-reviewable queue, calendar,
  booking detail panel, reply draft, and safe approval flow.
- Demo world: `space/floodlight_space/data/state_snapshot.v1.json`.
- Reset behavior: `POST /api/reload-demo` clears in-memory conversations and
  returns the immutable snapshot.
- Model front: Modal/Nemotron Cascade extraction endpoint remains wired through
  `/api/extract-booking`, but local UI proof uses fixture-shaped simulator
  messages unless Modal config is explicitly supplied.

## Proof Boundary

This folder claims local app, UX, API, fixture-backed simulator proof, and a
private hosted HF Space dry run after verification.

It does not claim public HF release, judge readiness, live WhatsApp/Baileys
send, video telecast, external scoring/admin integration, or fresh
`fallback_used=false` model proof.

## Key Files

- Product brief: `product-brief.md`
- Demo-world contract: `design/demo-world.md`
- Reload implementation spec: `design/reload-demo-implementation-spec.md`
- UX flow: `design/ux-flow.md`
- Design handoff: `design/handoff.json`
- Local evidence: `evidence/local-uat.md`
- Hosted Space evidence: `evidence/hf-space-deploy.md`
- App server: `space/app.py`
- Active frontend: `space/frontend/js/*` and `space/frontend/styles/*`
- Focused tests: `tests/`
