# Modal Demo-World Suite Evidence

Date: 2026-06-15

## Scope

Run label: `venue-manager-v2-demo-world-modal-suite`

Approval used:

- Budget: max `$20`.
- Duration: max `15 minutes` per bounded run.
- Stop condition: complete the requested seeded demo-world scenarios or record
  the exact blocker.

Claimed:

- The ten seeded v2 demo-world requests were sent to the Modal-backed
  `nvidia/Nemotron-Cascade-2-30B-A3B` extractor.
- The final batch run completed all requested seed cases with
  `fallback_used=false`.
- Local deterministic venue rules replayed each model extraction into the owner
  review backend.

Not claimed:

- Hosted HF Space proof.
- Live WhatsApp/Baileys inbound or outbound send.
- Broad eval or judge-ready release.

## Commands

First per-case attempt:

```bash
.venv/bin/python product/5-idea-venue-manager/3-v2-venue-manager/scripts/run_demo_world_modal_suite.py --write --max-seconds 900
```

Result: stopped at the 15-minute guardrail after Aman passed and Rohit was still
waiting for an HTTP response. Evidence:

```text
product/5-idea-venue-manager/3-v2-venue-manager/evidence/modal-demo-world-suite-20260615-125611/summary.json
product/5-idea-venue-manager/3-v2-venue-manager/evidence/modal-demo-world-suite-20260615-125611/rows.jsonl
```

Fix applied: the existing `extract_booking` Modal endpoint now accepts either a
single payload or an `items` batch payload, avoiding one cold start per seed
request while staying under the existing one-Web-Function limit.

Final batch run:

```bash
.venv/bin/python product/5-idea-venue-manager/3-v2-venue-manager/scripts/run_demo_world_modal_suite.py --write --transport batch --max-seconds 900
```

Evidence:

```text
product/5-idea-venue-manager/3-v2-venue-manager/evidence/modal-demo-world-suite-20260615-131029/summary.json
product/5-idea-venue-manager/3-v2-venue-manager/evidence/modal-demo-world-suite-20260615-131029/rows.jsonl
```

## Final Result

| Field | Value |
| - | - |
| Transport | `batch` through existing `extract_booking` Modal URL |
| Requested cases | `10` |
| Attempted cases | `10` |
| Passed objective checks | `9` |
| Failed objective checks | `1` |
| `fallback_used` | `false` for all 10 model results |
| Schema validation | `valid=true`, `errors=[]` for all 10 model results |
| Wall clock | `409.889s` |
| Modal billing row before suite attempt | `$1.04900744` |
| Modal billing row after per-case timeout attempt | `$3.08698045` |
| Modal billing row after final batch run | `$4.26568768` |
| Post-run app state | `deployed`, `tasks=0` after scale-down wait |

## Case Results

| Case | Seed tone | Backend action | Result |
| - | - | - | - |
| Aman Sharma | ready | `ready_for_owner_review` | Pass |
| Rohit Verma | partial | `conflict_possible` | Pass |
| Karan Mehta | ready | `ready_for_owner_review` | Pass |
| Vikas Singh | conflict | `conflict_possible` | Pass |
| Neha Iyer | clarification | `conflict_possible` | Objective mismatch |
| Arjun Nair | ready | `ready_for_owner_review` | Pass |
| Siddharth Rao | conflict | `conflict_possible` | Pass |
| Meera Rao | clarification | `needs_player_info` | Pass |
| Priya Menon | ready | `ready_for_owner_review` | Pass |
| Dev Arora | partial | `ready_for_owner_review` | Pass |

## Neha Finding

Neha is the only objective mismatch. The model extraction itself was valid and
useful:

- `booking_status=needs_clarification`
- `missing_fields=["format", "overs", "time"]`
- `fallback_used=false`

However, the model also inferred `time_window=afternoon`. The deterministic
rules matched South Field afternoon, found partial/competing demand, and
returned `conflict_possible` instead of the suite's expected
`needs_player_info`.

First failure:

```text
case_id=neha-iyer
first_failure=backend_action
expected_backend_action=needs_player_info
observed_backend_action=conflict_possible
```

This is a model/policy alignment finding, not a Modal plumbing blocker.

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

## Verification

Before the paid run:

```text
.venv/bin/python -m py_compile product/5-idea-venue-manager/3-v2-venue-manager/modal/modal_venue_manager_cascade.py product/5-idea-venue-manager/3-v2-venue-manager/scripts/run_demo_world_modal_suite.py
.venv/bin/python -m pytest product/5-idea-venue-manager/3-v2-venue-manager/tests/test_modal_extractor_contract.py product/5-idea-venue-manager/3-v2-venue-manager/tests/test_booking_conversation.py
```

Result: `30 passed`, one Starlette/httpx deprecation warning.

Token-backed no-GPU model-file preflight passed for:

```text
nvidia/Nemotron-Cascade-2-30B-A3B/config.json
nvidia/Nemotron-Cascade-2-30B-A3B/tokenizer_config.json
```
