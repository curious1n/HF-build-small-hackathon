# Reload Demo Implementation Spec

Date: 2026-06-15

## Purpose

V2 should present one believable venue-ops day, not a set of artificial demo
modes. The app loads a canonical seed world, lets the operator make temporary
runtime changes, and provides a top-right `Reload Demo` control that restores
the original seed.

This spec is the implementation contract for that behavior in:

```text
product/5-idea-venue-manager/3-v2-venue-manager
```

## Product Decision

Use one immutable demo world.

Do not expose the old scenario switcher in the judge-facing UI. Scenario
coverage remains important, but it should be represented by rows inside the
single seed world:

| Scenario category | Seeded representation |
| --- | --- |
| Clean approval | Aman Sharma, Karan Mehta, Arjun Nair |
| Existing demand / partial slot | Rohit Verma |
| Slot conflict | Vikas Singh, Siddharth Rao |
| Clarification needed | Neha Iyer, Meera Rao |
| Already terminal | Priya Menon |
| Older non-cricket/practice thread | Dev Arora |
| Provider/model unavailable | API/model-status and extract-booking blocker states, not a visible scenario mode |
| Empty queue | Internal QA only, not the default product demo |

## Source Of Truth

The canonical seed is:

```text
space/floodlight_space/data/state_snapshot.v1.json
```

The app must treat this file as read-only at runtime. A demo run may mutate
in-memory backend sessions and frontend state, but must not write changes back
to the snapshot.

## State Ownership

| State | Owner | Persistence | Reload behavior |
| --- | --- | --- | --- |
| Seed inventory, requests, bookings, players, teams, integrations | `state_snapshot.v1.json` | Durable repo file | Reloaded unchanged |
| Bootstrap payload | `/api/bootstrap` | Derived per request | Recreated from seed |
| Conversation sessions and owner-review traces | `InMemoryConversationStore` | Process memory only | Cleared |
| Frontend selected request, edits, notes, traces, sync status | `space/frontend/js/app.js` state object | Browser memory only | Cleared |
| Temporary confirmed booking markers | `Data.bookings` in frontend | Browser memory only | Replaced by seed bookings |
| Detail panel width preference | `localStorage` | Browser local preference | May remain; it is layout preference, not demo data |

## Functional Requirements

### Initial Load

- The frontend loads `/api/bootstrap` without requiring a visible scenario
  choice.
- The selected request comes from `payload.decision.selected_request_id`; if it
  is missing, select the first request.
- The loaded world must include a reasonable calendar, existing bookings,
  pending demand, new chats, mid-process chats, and one terminal/sent example.
- The top bar must show a `Reload Demo` button with
  `data-design-id="reload-demo"`.

### Temporary Mutations

These changes are allowed during one browser/server process run:

- Selecting a request syncs or creates a fixture-shaped backend conversation.
- Editing detected fields, slot, price, or notes affects only runtime state.
- Approving a confirmable request can mark the conversation
  `confirmed_simulated`.
- Clarifying or rejecting records the owner decision without claiming live send.
- A confirmed approval can add a temporary booking marker to the visible
  calendar.
- Request badges, pending counts, trace rows, and reply draft labels may update
  temporarily.

These changes must not modify `state_snapshot.v1.json`.

### Reload Demo

Clicking `Reload Demo` must:

1. Disable or busy-label the button while the reload is in progress.
2. Call `POST /api/reload-demo`.
3. Clear `InMemoryConversationStore` on the backend.
4. Return a fresh bootstrap payload derived from `state_snapshot.v1.json`.
5. Clear frontend runtime state:
   - conversations;
   - traces;
   - sync status;
   - backend error;
   - field edits;
   - active edit field;
   - slot draft;
   - notes;
   - any stale request sequence.
6. Replace frontend data with the returned payload:
   - requests;
   - venues;
   - slots;
   - seed bookings;
   - integrations;
   - runtime stats.
7. Re-select the seed-selected request and re-sync that request.
8. Show a short success toast such as `Demo data reloaded`.

If reload fails, the app should keep the current screen available, show a
failure toast, and surface the backend error in the detail panel.

## API Contract

### `GET /api/bootstrap`

Returns the current immutable seed payload.

Required response fields:

- `runtime`
- `slots`
- `venues`
- `bookings`
- `registered_teams`
- `players`
- `requests`
- `decision`
- `integrations`
- `trace`
- `state_snapshot`

The judge-facing frontend should call this as `/api/bootstrap`. The legacy
`scenario` query parameter may remain for internal QA, but visible UI should
not depend on it.

### `POST /api/reload-demo`

Clears temporary backend sessions and returns a fresh seed payload.

Required response additions:

```json
{
  "demo_reset": {
    "state": "reloaded",
    "source": "floodlight-demo-world-2026-06-15",
    "temporary_sessions_cleared": true
  }
}
```

The `source` value should be the current snapshot id when available.

### Owner Review Endpoints

`POST /api/conversations/{session_id}/owner-review` remains the only path for
approve, clarify, reject, and owner edits. Reload does not call owner-review; it
clears the temporary session history and restores the seed.

## Frontend Contract

### Top Bar

- The `Reload Demo` control belongs in the top-right action area of the
  masthead.
- It must be visible on desktop and reachable near the first mobile viewport.
- It should use the existing Floodlight visual system and icon style.
- It should expose `data-design-id="reload-demo"` for browser UAT.

### Runtime Store

The frontend should keep a single runtime state object that separates:

- seed-derived data stored in `Data`;
- mutable UI state stored in `state`;
- temporary conversations/traces keyed by request id;
- temporary calendar booking markers in `Data.bookings`.

Reload must replace seed-derived `Data` from the response before re-rendering
the full app.

### Request Sync

After bootstrap or reload, the frontend should sync the selected request through
`/api/whatsapp/simulated-message` so Backend Review and Trace Ledger are
populated. The sync must guard against stale async responses by using a request
sequence or equivalent cancellation check.

### Old Scenario Switcher

Do not render a visible `scenario-switcher` in v2. Scenario coverage is now
proved through seeded rows and internal API/UAT checks.

## Acceptance Criteria

### API

- `/api/bootstrap` returns snapshot id `floodlight-demo-world-2026-06-15`.
- `/api/bootstrap` returns 10 seeded requests and the expected seed bookings.
- Creating a simulated conversation stores a session in memory.
- `POST /api/reload-demo` clears that session and returns the seed payload.
- `/api/reload-demo` includes `demo_reset.state=reloaded` and
  `temporary_sessions_cleared=true`.
- `/api/extract-booking` without Modal config reports a blocker with
  `fallback_used=false`; this is model-front honesty, not reload behavior.

### Desktop Browser

- Initial render shows `brand-header`, `reload-demo`, `request-queue`,
  `conversation-stage`, `booking-detail-panel`, `availability-board`,
  `reply-draft`, `approval-actions`, `channel-status`,
  `disabled-integrations`, and `trace-ledger`.
- Approving Aman changes the row/draft/backend review to terminal simulator
  state and disables owner actions for that conversation.
- The calendar shows the temporary booking marker after approval.
- Clicking `Reload Demo` restores the original 10 request rows, seed bookings,
  Aman as a new/ready request, unsent draft label, and enabled owner actions.
- There is no visible old scenario switcher.

### Mobile Browser

- No horizontal overflow at 390 px width.
- `Reload Demo` is visible or quickly reachable near the top.
- Owner actions remain reachable after selecting a request.
- Reload restores the seed without requiring a full browser refresh.

### Evidence

When implementation changes are made, update:

- `evidence/local-uat.md` with API and browser proof;
- `design/handoff.json` if implementation anchors change;
- `implementation-readiness.md` if API names or verification commands change.

## Non-Goals

- No live WhatsApp/Baileys outbound send proof.
- No external scoring/admin integration.
- No video telecast integration.
- No public HF Space deploy claim.
- No fresh Modal/Nemotron model proof unless explicitly run with approved
  config and `fallback_used=false`.
- No hidden writes to the seed snapshot during runtime.

## Implementation Checklist

- Confirm `state_snapshot.v1.json` contains all seeded business cases.
- Ensure `/api/bootstrap` builds from `state_snapshot.v1.json`.
- Ensure `/api/reload-demo` resets `CONVERSATION_STORE` and returns a fresh
  bootstrap payload.
- Ensure the active frontend, not legacy scripts, renders `Reload Demo`.
- Ensure frontend reload clears runtime state and replaces seed-derived data.
- Remove/de-emphasize judge-facing scenario-switcher UI.
- Add or keep focused tests for bootstrap and reload.
- Run focused Python tests.
- Run JS syntax checks.
- Run desktop/mobile browser UAT before claiming UX proof.

## Open Questions

- Should temporary approvals affect `Confirmed Today` during the run, or should
  that stat remain seed-stable until reload?
- Should `Reload Demo` also clear browser `localStorage` layout preferences, or
  keep them as non-demo-data personalization?
- Should internal QA keep `/api/bootstrap?scenario=empty`, or should empty-queue
  coverage move to a separate test fixture outside the judge-facing API?
