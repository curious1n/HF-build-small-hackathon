# Epic Errands V2 Thread Prompts

Use these prompts to start fresh Codex threads without relying on prior chat
context. Each prompt includes the repo startup contract, active lanes, excluded
lanes, proof boundary, and files to read first.

Recommended order:

1. `01-feature-first-local-build.md`
2. `02-implementation-trace-check.md`
3. `03-local-browser-mobile-uat.md`
4. `04-shipping-decision-gate.md`

Do not skip ahead to hosted, model, public release, or judge-ready claims until
the earlier local implementation and UAT proof exists.

## Proof Ladder

| Prompt | Claim it can make |
| --- | --- |
| `01-feature-first-local-build.md` | Local implementation exists and focused checks pass. |
| `02-implementation-trace-check.md` | Detailed Design handoff anchors survived into code. |
| `03-local-browser-mobile-uat.md` | Local browser/mobile UX behavior and V1-style visual parity were exercised. |
| `04-shipping-decision-gate.md` | A shipping/model-proof path is chosen, or an approval-gated next prompt is prepared. |

Never claim hosted Space proof, sponsor/model proof, public release, submission
readiness, or judge-ready status from these prompts unless the matching lane is
explicitly added and evidence is produced in that thread.
