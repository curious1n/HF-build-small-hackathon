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

## Warm Preload Endpoint Pass

Date: 2026-06-15 UTC / 2026-06-16 local

Standing approval used:

- Source: `COAGENTS.md` active-candidate Modal warm/runtime smoke approval.
- Budget: max `$20`.
- Duration: max `15 minutes` wall-clock warm/always-on runtime per run.
- Stop condition: one world-demo scenario returns schema-valid
  `fallback_used=false`, or exact blocker.

Changes deployed:

- `modal/modal_venue_manager_cascade.py` now uses a GPU class with
  `@modal.enter()` to preload vLLM/Nemotron once per container.
- The public `extract-booking` web function calls the preloaded
  `VenueManagerCascade.run` class method.
- The endpoint URL is `https://curious1n--extract-booking.modal.run`.

Warm deploy command:

```bash
.venv/bin/python scripts/setup_modal_usage.py deploy-venue-manager --min-containers 1 --scaledown-window 900
```

Smoke command:

```bash
.venv/bin/python product/5-idea-venue-manager/3-v2-venue-manager/scripts/run_world_modal_smoke.py --write --max-seconds 900 --session-id venue-v2-warm-preload-20260616-004 --trace-id venue-v2-warm-preload-20260616-004
```

Result:

| Field | Value |
| - | - |
| Result | Pass |
| HTTP status | `200` |
| Model | `nvidia/Nemotron-Cascade-2-30B-A3B` |
| Modal app/function | `venue-manager-agent-cascade` / `extract-booking` |
| Hardware | `H100:2` |
| Backend/engine | `modal_http` / `vllm` |
| Artifact/quantization | `safetensors` / `bf16` |
| `fallback_used` | `false` |
| Validation | `valid=true`, `errors=[]` |
| Backend action | `ready_for_owner_review` |
| Wall clock | `344.153s` |
| Modal model latency | `3985ms` |
| Client latency | `344149ms` |
| Evidence JSON | `product/5-idea-venue-manager/3-v2-venue-manager/evidence/modal-world-smoke-20260615-210345.json` |

Timing finding:

- Preload worked for the actual model call: `timing_ms.load_llm_end=0`,
  `generation_end=3985`, and the returned model latency was about `4.0s`.
- End-to-end first-request latency was still about `344s` because the request
  arrived while the warm container was still starting/preloading. For demo
  responsiveness, deploy the warm pool and wait for preload to finish before
  starting the human demo, or add an explicit readiness/warmup poll.
- Three earlier smoke attempts were blocked by a stale/incorrect endpoint URL
  shape and are retained as blocker artifacts:
  `modal-world-smoke-20260615-205508.json`,
  `modal-world-smoke-20260615-205557.json`, and
  `modal-world-smoke-20260615-205735.json`.

Post-run scale-down:

```bash
.venv/bin/python scripts/setup_modal_usage.py deploy-venue-manager --min-containers 0 --scaledown-window 60
```

Result:

- Scale-to-zero deploy completed successfully with the preload code still in
  place and `min_containers=0`.
