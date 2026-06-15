# Epic Errands V2 Local Browser/Mobile UAT

Date: 2026-06-15

## Scope

Proof claim: local browser/mobile UAT only.

Not claimed: hosted HF Space proof, live model proof, sponsor proof, public
release, submission readiness, or judge-ready status.

The app used deterministic/local fallback media and provenance labels. This is
valid UX proof, not model proof.

## Workflow

Lanes used:

- UX/UAT Evidence: `product/workflow/UX_UAT_EVIDENCE.md`
- Feature-First: only for scoped UAT blockers
- Product Design: design handoff trace gate only

Prompt cards used:

- `product/workflow/prompts/browser-mobile-uat-proof.md`
- `product/workflow/prompts/design-to-code-trace-gate.md`

## Target

Local URL: `http://127.0.0.1:7860`

Start command:

```bash
PORT=7860 .venv/bin/python product/5-idea-epic-errands/7-v2-epic-errands-app/space/app.py
```

Browser runner:

- The in-app Browser connector became unavailable during UAT.
- A temporary Playwright/Chromium runner was installed under `/private/tmp` and
  used to exercise the local app.
- Raw evidence: `browser-uat-raw.json`

## Viewports

- `390 x 900`: full primary UAT flow
- `360 x 900`: Home and Settings mobile minimum smoke

No horizontal overflow was recorded in the summarized 390px or 360px states.
No browser console errors were recorded.

## Pass/Fail Checklist

| Area | Result | Evidence |
| --- | --- | --- |
| Local app starts | Pass | `/health` returned `status=ok`; local URL loaded. |
| V1 visual styling preserved | Pass | Questbook default loaded as `atelier`; Classroom loaded as `storybook`; Comic loaded as `comic`. Screenshots 01-03. |
| Mobile-first layout | Pass | 390px and 360px screenshots recorded with no overflow in raw summary. |
| Settings upload/remove controls | Pass | Four upload inputs rendered; parent/child/custom image uploads decoded previews; optional parent audio upload/remove updated state. Screenshot 04. |
| Theme independence from generation | Pass | Switching to Comic after accepting a goal did not mutate accepted image/audio URLs. |
| Quality mode enabled | Pass | Quality selected, `1024 x 1024` label visible. |
| Speed mode planned/disabled | Pass | Speed disabled with `720 x 720 planned` label. |
| Provenance contract | Pass | Review/DIY exposed Nemotron GGUF text, FLUX.2-klein-9B image, VoxCPM2 audio, and fallback labels where parent/DIY-facing. |
| Audio without parent reference | Pass | Parent reference audio was removed; generated/review/kid audio controls still rendered. |
| Generate to Review Goal | Pass | Parent drafted a goal, selected parent/child/custom references, generated, and reached Review Goal. Screenshot 05. |
| Editable text overlay | Pass | Review Goal overlay was edited; Kid card showed the edited app-owned text. Screenshots 05-06. |
| Stable square media frame | Pass | Generated images decoded at `768 x 768` local asset dimensions inside square frames. |
| Image text not baked into pixels | Pass | App-owned overlay is separate HTML state; media URL stayed stable after overlay edit and accept. |
| Review actions | Pass | Review Goal exposed only `cancel-goal` and `accept-goal` actions. |
| Cancel behavior | Pass | Cancel closed Review Goal and did not publish the canceled goal. |
| Accept behavior | Pass | Accept published the generated goal to Kid Goals. Screenshot 06. |
| Kid card privacy | Pass | Kid card leaked no raw model IDs, prompt text, raw JSON, generated steps, completion-check internals, or fallback flags. |
| Kid completion | Pass | Kid completed the goal; state changed to waiting for parent. Screenshot 07. |
| Parent approval | Pass | Parent approved reward; reward state updated to `approved_reward_given`. Screenshots 08-09. |
| DIY isolated surface | Pass | DIY opened at `/diy`, separate from main tabs. Screenshot 10. |
| DIY mirrored pipeline | Pass | DIY showed text, image, audio, composed card, trace/model details, and fallback labels. |
| DIY edits local only | Pass | Editing DIY draft updated preview/trace and did not save back to main app. Screenshot 11. |
| DIY save-back label | Pass | Save-back control was disabled and labelled `Coming soon`. |

## Screenshots

- `screenshots/01-home-390.png`
- `screenshots/02-settings-questbook-390.png`
- `screenshots/03-settings-comic-390.png`
- `screenshots/04-settings-uploads-390.png`
- `screenshots/05-review-generated-cancel-path-390.png`
- `screenshots/06-kid-goal-accepted-390.png`
- `screenshots/07-kid-waiting-parent-390.png`
- `screenshots/08-parent-approval-queue-390.png`
- `screenshots/09-parent-approved-390.png`
- `screenshots/10-diy-isolated-390.png`
- `screenshots/11-diy-updated-preview-390.png`
- `screenshots/12-home-360.png`
- `screenshots/13-settings-360.png`

## Design Gates

Implementation gate:

```bash
python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate implementation
```

Result: pass, P0/P1/P2 = 0.

UX gate:

```bash
python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate ux
```

Result: pass, P0/P1/P2 = 0.

## Known Notes

- App startup emits the expected Gradio `gr.Workflow` beta warning for the DIY
  workflow surface.
- The local app reports `live_generation=disabled`; generated media in this UAT
  is deterministic fallback/cached local media.
- The in-app Browser connector failed during UAT, so the final browser proof
  used temporary Playwright Chromium from `/private/tmp`.

## Next Lane Needed

Before any hosted, live model, sponsor, submission, or judge-ready claim, add
the corresponding lane: HF Space Shipping, Runtime Feasibility, Sponsor Model
Proof, Submission Readiness, or Judge-Ready Space Check.
