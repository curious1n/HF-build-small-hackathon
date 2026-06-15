# Demo World Contract

Date: 2026-06-15

## Source Of Truth

The canonical seed is:

```text
space/floodlight_space/data/state_snapshot.v1.json
```

`Reload Demo` must discard temporary UI/backend mutations and reload this seed.
The old visible scenario switcher is not part of the v2 judge-facing UI.

Implementation details for state ownership, API contracts, frontend reset
behavior, and acceptance criteria live in:

```text
design/reload-demo-implementation-spec.md
```

## Inventory

| Area | Seed |
| --- | --- |
| Venues | North Field, South Field |
| Slots | 8 AM - 12 PM, 2 PM - 6 PM |
| Surfaces | Natural grass, astro turf |
| Existing demand | Pending owner-review bookings and one confirmed simulator booking |
| Future integrations | Video disabled, external scoring/admin not connected |

## Seeded Requests

| Request | State | What It Proves |
| --- | --- | --- |
| Aman Sharma | New, ready | Clean approval path. |
| Rohit Verma | New, partial demand | Owner sees existing demand before confirming. |
| Karan Mehta | New, league | Registered team and owner approval path. |
| Vikas Singh | Conflict | Requested slot should offer alternatives instead of confirming. |
| Neha Iyer | Clarification | Missing format/overs blocks confirmation copy. |
| Arjun Nair | New, football | Sport-agnostic activity labels. |
| Siddharth Rao | Conflict | A second competing-demand example. |
| Meera Rao | Clarification/old | Multi-turn conversation still needs a precise time window. |
| Priya Menon | Confirmed/sent | Terminal simulator outcome remains visible. |
| Dev Arora | Old/practice | Non-cricket practice request remains reviewable. |

## Temporary Mutation Rules

- Selecting a request syncs a fixture-shaped backend conversation.
- Editing detected fields changes only runtime UI/backend state.
- Approving a confirmable request marks it sent through the simulator.
- Clarifying or rejecting records the owner decision without live send proof.
- A confirmed approval adds a temporary booking marker to the calendar.
- `Reload Demo` calls `POST /api/reload-demo`, clears in-memory conversations,
  restores the snapshot, and re-syncs the selected seed request.

## Scenario Coverage

The earlier Detailed Design scenario list remains useful as QA coverage, but v2
represents those cases inside one world:

| Scenario Category | V2 Representation |
| --- | --- |
| Normal live queue | Aman, Karan, Arjun |
| Clarification needed | Neha, Meera |
| Slot conflict | Vikas, Siddharth |
| Provider/model unavailable | `/api/extract-booking` blocked response when Modal config is missing |
| Empty queue | Internal QA route only, not judge-facing demo control |

## Proof Boundary

The seed is synthetic. It proves local interaction state and backend policy
shape only. It does not prove live WhatsApp, public hosting, model quality, or
external booking writes.
