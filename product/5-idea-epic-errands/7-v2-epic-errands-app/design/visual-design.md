# Epic Errands V2 Visual Design

Status: Detailed Design artifact for fast implementation handoff. This file
does not claim implementation, browser UAT, hosted proof, model proof, or
judge-ready status.

## Source Of Truth

V2 preserves the V1 visual system. Do not create a new visual direction.

Primary V1 sources:

- `../5-v1-epic-errands-app/design/visual-design.md`
- `../5-v1-epic-errands-app/design/style-modes.md`
- `../5-v1-epic-errands-app/design/handoff.json`
- `../5-v1-epic-errands-app/static/styles/tokens.css`
- `../5-v1-epic-errands-app/static/styles/components.css`
- `../5-v1-epic-errands-app/static/styles/app.css`

Supporting visual concepts:

- `../3-design-explorations-img-first/01-questbook-atelier/concept.png`
- `../3-design-explorations-img-first/03-cozy-classroom-adventure/concept.png`
- `../3-design-explorations-img-first/05-comic-mission-control/concept.png`

## Visual Direction

The default theme is Questbook: warm parchment, ink dividers, serif titles,
green-and-gold quest actions, premium family-app restraint, and generated goal
cards that feel like pages from a family questbook.

Classroom and Comic remain selectable app UI themes:

- Classroom: readable school-adventure UI with notebook surfaces, stickers,
  pencils, soft rounded controls, and calm parent-safe copy.
- Comic: bold kid reward/completion energy with panel blocks, speech-bubble
  moments, bright action accents, and scanable parent controls.

App UI theme is independent from generation mode and accepted media. Changing
Classroom, Questbook, or Comic changes shell styling, copy tone, and app-owned
overlay treatment only. It must not regenerate or mutate accepted generated
image or audio assets.

## Token Mapping

Use V1 token names and CSS first. Product theme ids stay
`classroom | questbook | comic`.

Implementation may map them to the existing V1 CSS theme attributes:

| Product theme id | User label | V1 CSS token skin |
| --- | --- | --- |
| `classroom` | Classroom | `storybook` |
| `questbook` | Questbook | `atelier` |
| `comic` | Comic | `comic` |

`questbook` is the canonical internal id. Legacy `magical` input may normalize
to `questbook` for compatibility, but V2 UI should show `Questbook`.

## Layout Rhythm

- Mobile-first target: 390px; minimum verification target: 360px.
- Keep the V1 phone/app-shell feeling: dense enough for repeated parent use,
  but still playful and legible for a child.
- Use five user-facing tabs: Home, Parent Goals, Kid Goals, Settings, DIY.
- Do not put model controls on Home.
- Use compact provenance chips only where parent-facing review or DIY needs
  them.
- Goal cards should prioritize image, editable text overlay, title/narration,
  audio preview, and reward status.

## Review Goal Card

Review Goal is the most important V2 visual delta.

Required treatment:

- Show the generated 1024 x 1024 image in a stable square media frame.
- Render goal text as an app-owned editable text layer over the image.
- Do not bake the goal text into generated image pixels.
- Do not expose image or audio editing actions from Review Goal.
- Show Accept and Cancel as the only terminal actions.
- Show generated audio preview as playable/listenable but immutable.
- Show compact parent-facing model/provenance summary.

Overlay direction:

- Reuse the approach from
  `../6-spike-add-elements-assets/text-overlay-prototype/index.html`.
- Overlay styling should adapt by app theme but remain readable on busy image
  backgrounds.
- Text edits update app-owned copy only; they do not regenerate image or audio.

## Settings Visual Requirements

Settings must feel like a practical parent setup panel, not a model lab.

Sections:

- App styling: Classroom, Questbook, Comic.
- Parent details: parent photos and optional parent reference audio.
- Children details: child photos.
- Generation references: parent photo, child photo, custom uploaded image.
- Generation mode: Quality enabled/selected; Speed visible but disabled/planned.

Quality mode copy should be concise. Keep full model identifiers available in
contracts/provenance, not as heavy visible UI.

## DIY Visual Requirements

DIY is a separate isolated surface inside the same package. It mirrors the main
generation flow while looking like a parent-facing inspector.

DIY should show:

- selected app theme;
- ordinary goal;
- selected parent/child/custom image references;
- text, image, audio, composed-card steps;
- model/runtime/format/quantization/fallback labels;
- editable hardcoded workflow draft;
- local preview and JSON trace;
- save-back-to-main-app labelled `Coming soon`.

DIY is not the kid-facing flow and should not share kid completion controls.

## Must Preserve

- `visual_quest_default`: Questbook remains the default visible app theme.
- `visual_theme_switching`: Classroom, Questbook, and Comic remain app UI
  themes.
- `visual_theme_independent_from_generation`: app UI theme changes must not
  mutate generation mode or accepted media.
- `review_text_overlay`: visible goal text is editable app-owned overlay text,
  not image pixels.
- `review_media_immutable`: generated image and audio cannot be edited from
  Review Goal.
- `playable_goal_audio`: accepted kid goal cards include playable generated
  audio without exposing raw model controls.
- `quality_only_hackathon`: Quality is enabled; Speed is disabled/planned.
- `isolated_diy_same_package`: DIY is isolated inside the same app package.

## Proof Boundary

This is a design artifact readiness claim only. Future threads must run the
matching implementation, browser/mobile UAT, runtime/model, Space, and
submission lanes before making those claims.
