# Local UAT Evidence

Date: 2026-06-15

Run label: `venue-manager-v2-local-fixture-uat`

Target URL:

```text
http://127.0.0.1:7870/
```

Note: this verification pass used `7870` because an existing local process was
already bound to `7862`.

## Scope

Claimed:

- Clean v2 active folder runs locally.
- Immutable demo-world seed loads from `state_snapshot.v1.json`.
- `Reload Demo` clears temporary in-memory conversations and restores the seed.
- Fixture-shaped simulator owner review works locally.
- Desktop and mobile browser UX are usable with no horizontal overflow.

Not claimed:

- Public HF Space deploy.
- Fresh Modal/Nemotron model proof.
- Live WhatsApp/Baileys send.
- External scoring/admin or video integration.
- Judge readiness.

## Commands

```bash
python3 scripts/check_design_handoff.py --idea product/5-idea-venue-manager/3-v2-venue-manager --gate ux
```

Result: pass, `P0=0`, `P1=0`, `P2=0`.

```bash
.venv/bin/python -m pytest product/5-idea-venue-manager/3-v2-venue-manager/tests/test_booking_conversation.py product/5-idea-venue-manager/3-v2-venue-manager/tests/test_modal_extractor_contract.py
```

Result: `30 passed`, one Starlette/httpx deprecation warning.

```bash
node --check product/5-idea-venue-manager/3-v2-venue-manager/space/frontend/js/app.js
node --check product/5-idea-venue-manager/3-v2-venue-manager/space/frontend/js/components.js
node --check product/5-idea-venue-manager/3-v2-venue-manager/space/frontend/js/dom.js
```

Result: pass.

```bash
PORT=7870 ../../../../.venv/bin/python app.py
```

Workdir: `product/5-idea-venue-manager/3-v2-venue-manager/space`.

## API Smoke

| Check | Result |
| --- | --- |
| `/health` | `status=ok`, `version=v2-active-demo`, model id `nvidia/Nemotron-Cascade-2-30B-A3B`. |
| `/api/bootstrap` | 10 request rows, 9 active pending rows, 3 seed bookings, snapshot `floodlight-demo-world-2026-06-15`. |
| `/api/reload-demo` | `state=reloaded`, `temporary_sessions_cleared=true`, 10 request rows restored and pending count reset to 9. |
| `/api/model-status` | Modal config not present locally: `configured=false`, no secrets exposed. |
| `/api/extract-booking` without Modal config | Expected blocker: `502`, `ok=false`, `fallback_used=false`, `APP_MODAL_BASE_URL and APP_MODAL_AUTH_TOKEN must be configured on the Space.` |

## Browser UAT

Desktop viewport: 1280 x 720.

| Check | Result |
| --- | --- |
| Render anchors | Pass: `brand-header`, `reload-demo`, `request-queue`, `conversation-stage`, `booking-detail-panel`, `availability-board`, `reply-draft`, `approval-actions`, `channel-status`, `disabled-integrations`, `trace-ledger`. |
| Seed state | Pass: 10 request rows; 9 active pending rows; Aman selected; `Reload Demo` visible; draft says `Draft reply - not sent`; no visible scenario switcher. |
| Assets | Pass: `floodlight-logo.png` decoded 774 x 234; `cricket-ball.png` decoded 70 x 70. |
| Horizontal overflow | Pass after shell/layout fix: document scroll width equals client width. |
| Happy path | Pass: Approve on Aman changes badge to `Sent`, draft to `Simulator sent - terminal`, backend action to `confirmed_simulated`, send adapter to `simulator - simulated_sent`, disables owner actions, and temporarily changes pending count from 9 to 8. |
| Reload reset | Pass: `Reload Demo` restores 10 request rows, 9 active pending rows, Aman badge `New`, draft `Draft reply - not sent`, approve enabled, and toast `Demo data reloaded`. |
| Conflict path | Pass: Vikas shows `Conflict draft - not sent`, backend action `conflict_possible`, send adapter `simulator - not_sent`, and alternative slots in the outgoing draft. |
| Console errors | Pass: browser error log empty. |

Mobile viewport: 390 x 844.

| Check | Result |
| --- | --- |
| Horizontal overflow | Pass: client width 375, scroll width 375. |
| Reload control | Pass: `Reload Demo` visible near top of first viewport. |
| Owner action reachability | Pass: after selecting Karan, approve/clarify/reject bar remains fixed at viewport bottom and enabled. |
| Mobile reload path | Pass: `Reload Demo` restores Aman as selected, draft to `Draft reply - not sent`, approve enabled, and no horizontal overflow. |

## Notes

- The seed request count is 10, while `Pending Requests` is 9 active unsent
  rows because the seed includes one already-sent simulator request.
- Browser proof used fixture-shaped simulator extraction; this is not fresh
  model proof.

## TRY ME Model Visibility Pass

Run label: `venue-manager-v2-try-me-ux-2026-06-15`

Scope:

- Add a pinned `TRY ME` request as the first queue item.
- Clicking `TRY ME` initiates the existing
  `/api/whatsapp/simulated-model-message` route instead of the deterministic
  simulator route.
- Show visible model-call proof in the right panel before and during the call.

Commands:

```bash
node --check product/5-idea-venue-manager/3-v2-venue-manager/space/frontend/js/app.js
node --check product/5-idea-venue-manager/3-v2-venue-manager/space/frontend/js/components.js
```

Result: pass.

```bash
.venv/bin/python -m pytest product/5-idea-venue-manager/3-v2-venue-manager/tests/test_booking_conversation.py product/5-idea-venue-manager/3-v2-venue-manager/tests/test_modal_extractor_contract.py
```

Result: `30 passed`, one Starlette/httpx deprecation warning.

Browser UAT at `http://127.0.0.1:7860/`:

| Check | Result |
| --- | --- |
| Initial queue | Pass: `TRY ME` is first, marked `Live demo`, while Aman remains selected. |
| No load-time model call | Pass: the right-panel `Model Run` block is absent before clicking `TRY ME`. |
| Click-to-call state | Pass: clicking `TRY ME` selects it, queue badge changes to `Calling`, chat composer disables as `Calling`, and right panel shows `Model Run`, `Runtime=Modal`, `Backend=modal_http`, pending latency/schema/fallback, and a `ui-modal-*` trace id. |
| Live completion | Not claimed in this pass. The local Modal request did not complete before the run was stopped to stay inside the bounded runtime guardrail. |

Non-paid browser layout pass at `http://127.0.0.1:7860/`, without Modal
credentials:

| Check | Result |
| --- | --- |
| Desktop initial state | Pass: width `1280`, scroll width `1280`, `TRY ME` visible, composer hidden before activation. |
| Desktop blocker state | Pass: clicking `TRY ME` shows queue badge `Error`, right-panel `Model Run` with `Runtime=Modal`, `Backend=modal_http`, `Latency`, trace id, and `HTTP 502` blocker; no horizontal overflow. |
| Mobile initial state | Pass: viewport width `375`, scroll width `375`, `TRY ME` visible, approval actions visible. |
| Mobile blocker state | Pass: after clicking `TRY ME`, model proof block and composer remain contained at scroll width `375`; no horizontal overflow. |

Proof boundary:

- This pass proves the UX visibly initiates the model route and surfaces the
  call state.
- It does not claim a fresh completed HF Space-to-Modal result or judge-ready
  hosted proof.
