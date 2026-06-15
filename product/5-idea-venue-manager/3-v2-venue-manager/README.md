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

## 100-Case Modal Trace Run

The 100 synthetic model-input cases live in the prior provenance folder:

```text
product/5-idea-venue-manager/2-sport-agnostic-venue-agent/eval/cases/booking_100_message_cases.jsonl
```

Run a no-spend validation first:

```bash
cd /Users/cuStd/Desktop/dev/HF-build-small-hackathon
.venv/bin/python product/5-idea-venue-manager/3-v2-venue-manager/scripts/run_100_modal_batch_traces.py --dry-run
```

To run the paid Modal/Nemotron trace capture yourself, use:

```bash
cd /Users/cuStd/Desktop/dev/HF-build-small-hackathon
.venv/bin/python product/5-idea-venue-manager/3-v2-venue-manager/scripts/run_100_modal_batch_traces.py \
  --approved-paid-modal-run \
  --upload-hf-dataset \
  --max-seconds 1200 \
  --chunk-size 10
```

The script deploys the warm Modal endpoint with `min_containers=1`, sends one
warmup request, runs the 100 examples in batch chunks of up to 12 items, writes
local artifacts, optionally uploads the dataset, and redeploys Modal back to
`min_containers=0` in its final cleanup path. If `--dataset-id` is omitted, the
dataset target defaults to `$HF_HACKATHON/venue-manager-v2-agent-traces` from
repo `.env`. The warmup request can take several minutes while Modal starts the
H100 container and preloads vLLM; the runner prints heartbeat lines during that
wait.

Monitor without spending Codex tokens:

```bash
tail -f product/5-idea-venue-manager/3-v2-venue-manager/eval/runs/latest/run.log
```

```bash
python3 -m json.tool product/5-idea-venue-manager/3-v2-venue-manager/eval/runs/latest/progress.json
```

Expected local outputs:

```text
product/5-idea-venue-manager/3-v2-venue-manager/eval/runs/<run-id>/agent_trace.jsonl
product/5-idea-venue-manager/3-v2-venue-manager/eval/runs/<run-id>/summary.json
product/5-idea-venue-manager/3-v2-venue-manager/eval/runs/<run-id>/run.log
product/5-idea-venue-manager/3-v2-venue-manager/eval/runs/<run-id>/README.md
```

Proof boundary: this is synthetic trace capture through Modal/vLLM with
`fallback_used=false` checks per successful row. It is not public release,
hosted Space UX proof, live WhatsApp proof, judge readiness, or a
human-reviewed model-quality eval.

Latest uploaded dataset:

```text
https://huggingface.co/datasets/build-small-hackathon/venue-manager-v2-agent-traces
```

Latest run summary:

```text
run_id=20260615-215214
rows=100
passed=88
failed=12
fallback_true=0
schema_invalid=0
wall_clock_seconds=325.567
modal_scaled_down=true
```

Runtime axes:

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

Dataset privacy note: the uploaded rows are synthetic booking messages from the
Venue Manager fixture suite. They do not contain live WhatsApp traffic, real
customer approvals, secrets, tokens, or private auth state.

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
