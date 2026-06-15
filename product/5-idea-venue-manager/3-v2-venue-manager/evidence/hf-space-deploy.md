# HF Space Deploy Evidence

Date: 2026-06-15

Run label: `venue-manager-v2-hosted-space-dry-run`

## Scope

Claimed:

- V2 package uploaded to the existing private Hugging Face Space.
- Hosted Space dry-run API checks passed for health, immutable bootstrap, and
  reload-demo reset.
- No Modal extraction call was made in this pass.

Not claimed:

- Public HF release.
- Judge readiness.
- Fresh Modal/Nemotron `fallback_used=false` proof.
- Live WhatsApp/Baileys send.
- External scoring/admin or video integration.
- Hosted browser/mobile UX proof.

## Space

| Field | Value |
| --- | --- |
| Space repo | `build-small-hackathon/venue-manager-agent` |
| Space URL | `https://build-small-hackathon-venue-manager-agent.hf.space` |
| Lifecycle | `staging/private hosted dry run` |
| SDK | `gradio` |
| Visibility | private |
| Namespace env | `HF_HACKATHON` |
| Upload actor env | `HF_2` |
| Token env | `HF_TOKEN_2` |
| Package root | `product/5-idea-venue-manager/3-v2-venue-manager/space` |
| Uploaded revision | `b91584701e40ee5263695e588576dc1959ef3fe4` |
| Last modified | `2026-06-15 11:38:42+00:00` |

## Commands

Preflight:

```bash
cd product/5-idea-venue-manager/3-v2-venue-manager
../../../.venv/bin/python deploy_space.py
../../../.venv/bin/python -m pytest tests/test_booking_conversation.py tests/test_modal_extractor_contract.py
node --check space/frontend/js/app.js
node --check space/frontend/js/components.js
node --check space/frontend/js/dom.js
node --check space/frontend/js/data.js
python3 scripts/check_design_handoff.py --idea product/5-idea-venue-manager/3-v2-venue-manager --gate ux
```

Results:

- Deploy dry run resolved `build-small-hackathon/venue-manager-agent`,
  `HF_HACKATHON`, `HF_2`, and `HF_TOKEN_2` with secret values redacted.
- Python tests: `30 passed`, one Starlette/httpx deprecation warning.
- JS syntax checks: pass.
- Design handoff UX gate: pass, `P0=0`, `P1=0`, `P2=0`.

Upload:

```bash
cd product/5-idea-venue-manager/3-v2-venue-manager
../../../.venv/bin/python deploy_space.py --create --upload --commit-message "Deploy Venue Manager v2 Space"
```

Result:

- Upload complete.
- First upload attempt failed because `emoji: VM` was not valid HF Space
  metadata. Fixed to a pictographic emoji and retried successfully.

## Hosted Dry Run

Authenticated checks against:

```text
https://build-small-hackathon-venue-manager-agent.hf.space
```

| Check | Result |
| --- | --- |
| `/health` | `200`, `status=ok`, `version=v2-active-demo`, `model_runtime=modal`, model id `nvidia/Nemotron-Cascade-2-30B-A3B` |
| `/api/bootstrap` | `200`, snapshot `floodlight-demo-world-2026-06-15`, 10 requests, 3 seed bookings |
| `/api/reload-demo` | `200`, `demo_reset.state=reloaded`, `temporary_sessions_cleared=true`, 10 requests restored |

Initial hosted poll briefly saw the old container during Space restart. A
second poll passed after the v2 container became active.

## Runtime Axes

```text
lifecycle_stage=staging
app_host=hf_space
model_runtime=modal_configurable
model_backend=not_called_in_this_pass
model_id=nvidia/Nemotron-Cascade-2-30B-A3B
fallback_used=not_applicable_for_hosted_dry_run
send_adapter=simulator
```

## Proof Boundary

This is a hosted app dry run for v2 packaging and deterministic fixture-backed
demo reset behavior. It does not prove Modal model quality, live WhatsApp,
public release readiness, or judge readiness.

## Warm Preload Config Push

Date: 2026-06-15 UTC / 2026-06-16 local

Scope:

- Push the current Space package to `build-small-hackathon/venue-manager-agent`.
- Set redacted `APP_MODAL_*` variables/secrets for the new Modal
  `extract-booking` endpoint.
- Verify hosted deterministic endpoints after the Space rebuild.

Commands:

```bash
cd product/5-idea-venue-manager/3-v2-venue-manager
../../../.venv/bin/python deploy_space.py --create --upload --set-modal-config --commit-message "Fix Venue Manager hosted startup and Modal preload config"
```

Preflight and package checks:

- Deploy dry run resolved `build-small-hackathon/venue-manager-agent`,
  `HF_HACKATHON`, `HF_2`, and `HF_TOKEN_2` with secret values redacted.
- Python tests: `30 passed`, one Starlette/httpx deprecation warning.
- Python package compile: `app.py` and `floodlight_space/*.py` passed.
- JS syntax checks: `space/frontend/js/app.js`, `components.js`, `dom.js`,
  and `data.js` passed.

Hosted result:

| Field | Value |
| - | - |
| Space repo | `build-small-hackathon/venue-manager-agent` |
| Space URL | `https://build-small-hackathon-venue-manager-agent.hf.space` |
| Uploaded revision | `eb44c6f13cead44b71f95256c9a7c0423f6ed624` |
| Last modified | `2026-06-15 21:05:34+00:00` |
| Runtime stage | `RUNNING` after `APP_STARTING` polls |
| `/health` | `200`, model runtime `modal`, model id `nvidia/Nemotron-Cascade-2-30B-A3B` |
| `/api/model-status` | `200`, configured/base URL/auth all `true`, timeout `900.0` |
| `/api/bootstrap` | `200`, 10 requests, 3 seed bookings |
| `/api/reload-demo` | `200`, `demo_reset.state=reloaded`, 10 requests restored |

Fix applied:

- `space/app.py` no longer assumes a fixed parent depth when looking for local
  `.env.modal.local`; this prevents `/app/app.py` from crashing on HF Spaces.

Proof boundary:

- This proves the hosted Space package and redacted Modal config are deployed
  and the deterministic hosted endpoints are healthy.
- Modal model proof for the preload change is recorded separately in
  `evidence/modal-world-smoke-2026-06-15.md`.
  This pass did not run a hosted Space-to-Modal model call.
