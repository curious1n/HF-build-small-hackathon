# Product Brief

Date: 2026-06-15

## Idea

Floodlight Venue Manager is an owner-facing venue operations console. It helps a
venue operator review WhatsApp-style booking requests, inspect extracted booking
details, compare availability, approve safe replies, and keep future integration
claims honest.

## Primary User

A small sports venue owner or operator who is juggling customer chats, partial
slot demand, repeat teams, prices, and operational constraints during the day.

## Moment

The owner opens the console while several conversations are already in flight:
some are new, some need clarification, some conflict with existing demand, and
one was already confirmed through the simulator.

## Smallest Successful Outcome

The operator can select a request, see the raw chat and detected booking detail,
review availability, approve/clarify/reject the outgoing reply, and reload the
demo world back to a known clean state.

## Demo Promise

One stable demo world, not artificial scenario modes:

- a reasonable calendar and two-venue inventory;
- booked and pending slots;
- repeat players and teams;
- new chats;
- mid-process clarification/conflict chats;
- temporary owner actions that reset with `Reload Demo`.

## Model Role

The model extracts a candidate booking JSON from messy customer text. Backend
rules own inventory truth, conflict checks, owner-review state, and send policy.
The local UI uses fixture-shaped extraction for demo reliability unless Modal is
configured for a model smoke.

## Non-Goals

- Live WhatsApp send.
- Public HF Space release in this pass.
- CricHeroes/external scoring or video telecast integration.
- Model-quality or sponsor-model proof without a fresh `fallback_used=false`
  run.
