# Modal World Smoke Evidence

Date: 2026-06-15

## Scope

Run label: `venue-manager-v2-world-modal-smoke`

Standing approval used:

- Source: `COAGENTS.md` standing bounded approval.
- Budget: max `$20`.
- Duration: max `15 minutes` wall-clock.
- Stop condition: one world-demo scenario returns schema-valid
  `fallback_used=false`, or exact blocker.

Claimed:

- One local v2 world-demo simulator scenario used server-side Modal extraction.
- Modal model output passed schema validation.
- Deterministic booking rules moved the scenario to owner review.

Not claimed:

- Broad/batch eval.
- Public or hosted HF Space proof.
- Live WhatsApp/Baileys inbound or outbound send.
- Judge readiness.

## Command

```bash
.venv/bin/python product/5-idea-venue-manager/3-v2-venue-manager/scripts/run_world_modal_smoke.py --write --max-seconds 900 --session-id venue-v2-world-modal-20260615-001 --trace-id venue-v2-world-modal-20260615-001
```

## Result

| Field | Value |
| - | - |
| Result | Pass |
| HTTP status | `200` |
| Scenario | `normal` |
| Session/trace | `venue-v2-world-modal-20260615-001` |
| Model | `nvidia/Nemotron-Cascade-2-30B-A3B` |
| Modal app/function | `venue-manager-agent-cascade` / `extract_booking` |
| Hardware | `H100:2` |
| Backend/engine | `modal_http` / `vllm` |
| Artifact/quantization | `safetensors` / `bf16` |
| `fallback_used` | `false` |
| Validation | `valid=true`, `errors=[]` |
| Backend action | `ready_for_owner_review` |
| Wall clock | `387.941s` |
| Modal latency | `357365ms` |
| Client latency | `387934ms` |
| Modal billing report row for today | `$0.85406953` |
| Post-run app state | `deployed`, `tasks=0` after scale-down wait |

Evidence JSON:

```text
product/5-idea-venue-manager/3-v2-venue-manager/evidence/modal-world-smoke-20260615-123352.json
```

## Runtime Axes

```text
lifecycle_stage=testing
app_host=local
model_runtime=modal
model_backend=modal_http
inference_engine=vllm
model_artifact_format=safetensors
quantization=bf16
model_id=nvidia/Nemotron-Cascade-2-30B-A3B
fallback_used=false
```

## Extracted Booking Summary

The model extracted Aman Sharma's cricket booking request for North Field,
tomorrow morning, 12 players, natural grass, budget `Rs 6000`, with no missing
fields. The local deterministic rules found North Field morning available,
quoted `Rs 6000`, and left the reply drafted for owner review rather than live
sending.

## Warm-Pool Implementation Pass

Date: 2026-06-15

Standing approval used:

- Source: `COAGENTS.md` active-candidate Modal warm/runtime smoke approval.
- Budget: max `$20`.
- Duration: max `15 minutes` wall-clock warm/always-on runtime per run.
- Stop condition: one world-demo scenario returns schema-valid
  `fallback_used=false`, or exact blocker.

Changes made:

- `modal/modal_venue_manager_cascade.py` now supports deploy-time warm-pool
  knobs:
  - `VENUE_MODAL_MIN_CONTAINERS`
  - `VENUE_MODAL_BUFFER_CONTAINERS`
  - `VENUE_MODAL_SCALEDOWN_WINDOW`
- `scripts/setup_modal_usage.py deploy-venue-manager` deploys the Venue
  Manager Modal endpoint with those knobs without printing secrets.

Warm deploy command:

```bash
.venv/bin/python scripts/setup_modal_usage.py deploy-venue-manager --min-containers 1 --scaledown-window 900
```

Warm-smoke command:

```bash
.venv/bin/python product/5-idea-venue-manager/3-v2-venue-manager/scripts/run_world_modal_smoke.py --write --max-seconds 900 --session-id venue-v2-warm-modal-20260615-001 --trace-id venue-v2-warm-modal-20260615-001
```

Result:

| Field | Value |
| - | - |
| Result | Pass |
| HTTP status | `200` |
| Model | `nvidia/Nemotron-Cascade-2-30B-A3B` |
| Modal app/function | `venue-manager-agent-cascade` / `extract_booking` |
| Hardware | `H100:2` |
| Backend/engine | `modal_http` / `vllm` |
| Artifact/quantization | `safetensors` / `bf16` |
| `fallback_used` | `false` |
| Validation | `valid=true`, `errors=[]` |
| Backend action | `ready_for_owner_review` |
| Wall clock | `592.055s` |
| Modal latency | `577572ms` |
| Client latency | `592053ms` |
| Evidence JSON | `product/5-idea-venue-manager/3-v2-venue-manager/evidence/modal-world-smoke-20260615-184111.json` |

Important finding:

- `min_containers=1` keeps the Modal function container warm, but the current
  function still lazy-loads vLLM weights on the first request. That first
  warm-up request therefore still took about 9.9 minutes. Follow-up requests
  during the warm window should benefit from the loaded `_LLM`, but this pass
  stopped after the approved single schema-valid scenario.
- The endpoint was redeployed back to `min_containers=0` and
  `scaledown_window=60` after the smoke to satisfy the standing approval's
  scale-down requirement.
