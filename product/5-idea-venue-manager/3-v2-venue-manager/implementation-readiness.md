# Implementation Readiness

Date: 2026-06-15

## Current Scope

This v2 folder is the clean active local app path for Venue Manager. It is
curated from the prior `2-sport-agnostic-venue-agent` folder, but the old folder
remains untouched.

## Runtime Shape

| Axis | Value |
| --- | --- |
| App host | Local Gradio `Server` custom frontend |
| Local path | `space/app.py` |
| Frontend | `space/frontend/js/*`, `space/frontend/styles/*` |
| Seed data | `space/floodlight_space/data/state_snapshot.v1.json` |
| Reload demo spec | `design/reload-demo-implementation-spec.md` |
| Model front | Modal HTTP client via `/api/extract-booking` |
| Model id | `nvidia/Nemotron-Cascade-2-30B-A3B` |
| Local Modal env | `product/5-idea-venue-manager/.env.modal.local` |
| Local demo model mode | Fixture-shaped simulator extraction |
| Fallback claim | Deterministic fallback is not model proof |
| Modal suite path | Existing `extract_booking` endpoint accepts a single payload or an `items` batch payload |

## Standing Modal Smoke Default

For this v2 folder, @cu has approved a default Modal/Nemotron single-scenario
smoke without repeated approval prompts:

- Budget: max `$20`.
- Duration: max `15 minutes` wall-clock.
- Stop condition: stop after one world-demo scenario returns schema-valid
  `fallback_used=false` result, or after recording the exact blocker.
- Scope: the scale-to-zero Modal `venue-manager-agent-cascade` path for
  `nvidia/Nemotron-Cascade-2-30B-A3B`.

This does not approve warm pools, always-on services, new GPU classes,
broad/batch evals, public release, judge-ready claims, or other products.
Token-backed model-file preflight is still required if not already verified in
the active thread.

## API Surface

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Local app status. |
| `GET` | `/api/model-status` | Modal config status without secrets. |
| `GET` | `/api/bootstrap` | Immutable demo seed payload. |
| `POST` | `/api/reload-demo` | Clear temporary sessions and reload seed. |
| `POST` | `/api/whatsapp/simulated-message` | Fixture-shaped simulator conversation path. |
| `POST` | `/api/whatsapp/simulated-model-message` | Server-side Modal extraction path when configured. |
| `POST` | `/api/conversations/{session_id}/owner-review` | Owner approve/clarify/reject/edit. |
| `GET` | `/api/conversations/{session_id}/trace` | Owner-safe trace and runtime axes. |

## Verification Commands

```bash
cd product/5-idea-venue-manager/3-v2-venue-manager
../../../.venv/bin/python -m pytest tests/test_booking_conversation.py tests/test_modal_extractor_contract.py
```

```bash
cd product/5-idea-venue-manager/3-v2-venue-manager/space
PORT=7862 ../../../../.venv/bin/python app.py
```

## Proof Boundary

This pass proves the local v2 app, fixture-backed simulator UX, private hosted
Space dry-run packaging, one local Modal/Nemotron world-demo smoke, and a
10-case local Modal/Nemotron demo-world seed suite.
Public HF release, live WhatsApp, and judge readiness remain future work.

Modal world-smoke evidence:

```text
evidence/modal-world-smoke-2026-06-15.md
```

Modal demo-world suite evidence:

```text
evidence/modal-demo-world-suite-2026-06-15.md
```
