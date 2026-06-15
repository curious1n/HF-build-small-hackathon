# UX Flow

Date: 2026-06-15

## Product Invariant

Model extraction is a candidate. Backend deterministic rules own truth. Owner
review is required before any outbound reply is marked sent. The current send
adapter is a simulator.

## Primary Flow

1. App loads the immutable demo world from `/api/bootstrap`.
2. Owner sees a live request queue, WhatsApp-style conversation preview,
   booking detail panel, availability calendar, reply draft, integrations, and
   trace ledger.
3. Owner selects a request.
4. Frontend sends a fixture-shaped candidate booking to
   `/api/whatsapp/simulated-message`.
5. Backend validates the candidate, runs deterministic checks, and returns a
   reviewable conversation state.
6. Owner may edit detail fields, price, slot, or notes.
7. Owner chooses approve, clarify, or reject.
8. Backend applies `/api/conversations/{session_id}/owner-review`.
9. The UI renders terminal simulator state or a safe not-sent state.
10. Owner can click `Reload Demo` to restore the immutable seed.

## Terminal Outcomes

| Outcome | Meaning |
| --- | --- |
| `confirmed_simulated` | Owner-approved reply was marked sent through simulator. |
| `conflict_possible` | Backend blocked confirmation and drafted alternatives. |
| `needs_player_info` | Backend needs clarification before confirmation. |
| `cancelled` | Owner rejected/cancelled the request. |
| `failed_model` | Model/runtime/schema path blocked without fallback. |

## Required Visible Anchors

- `brand-header`
- `reload-demo`
- `request-queue`
- `conversation-stage`
- `booking-detail-panel`
- `availability-board`
- `reply-draft`
- `approval-actions`
- `channel-status`
- `disabled-integrations`
- `trace-ledger`

## Non-Goals

No live WhatsApp, external scoring/admin, video telecast, public HF deploy, or
fresh model proof is claimed by this local UX flow.
