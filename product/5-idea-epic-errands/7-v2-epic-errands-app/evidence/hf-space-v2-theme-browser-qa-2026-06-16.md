# Epic Errands V2 Theme Browser QA

Date: 2026-06-16

## Scope

- Quick browser QA of Classroom, Questbook, and Comic themes.
- Target the HF-parity Gradio `build_hosted_demo()` path.
- Fix obvious color/font/control styling regressions caused by Gradio dark-mode
  CSS leaking into the custom HTML island.

Not claimed:

- public release;
- judge-ready proof;
- hosted live-model proof.

## Local Browser Findings

Run label: Local App Dry Run

URL: `http://127.0.0.1:7868/`

Initial failures:

- Classroom and Questbook had nearly white text on pale panels.
- Theme and nav buttons were taking Gradio gray button styling instead of Epic
  Errands theme tokens.
- Primary Generate Goal button was Gradio-gray instead of the theme primary
  action color.

Root cause:

- HF/Gradio sets `body.className = "dark"` in the Blocks runtime.
- Gradio dark-mode styles were winning over lower-specificity custom app
  selectors inside the fully custom `gr.HTML` island.

Fix:

- Added high-specificity `#epic-hosted-shell ...` boundary rules in
  `space/app.py`.
- Reasserted theme token foregrounds, fonts, nav/theme button colors, child
  span/icon colors, ghost buttons, fields, upload chips, and primary CTA style.

## Local Retest

Screens tested:

- Settings
- Parent/Create Goal

Themes tested:

- Classroom / `storybook`
- Questbook / `atelier`
- Comic / `comic`

Observed after fix:

- Theme fonts loaded:
  - `Baloo 2`
  - `Nunito`
  - `Bangers`
  - `Hanken Grotesk`
  - `Playfair Display`
  - `Lora`
- `overflowX = 0` on Settings and Parent screens.
- Classroom headings/buttons use readable navy/green/red tokens.
- Questbook headings/buttons use readable serif/green/parchment tokens.
- Comic remains intentionally dark with readable gold/blue/yellow tokens.
- Generate Goal reached review state.
- Browser console errors/warnings: none.

Representative final parent checks:

```json
[
  {
    "themeButton": "Classroom",
    "token": "storybook",
    "generateBackground": "linear-gradient(rgb(233, 56, 45) 0%, rgb(197, 43, 34) 100%)",
    "generateFont": "\"Baloo 2\", cursive",
    "overflowX": 0
  },
  {
    "themeButton": "Questbook",
    "token": "atelier",
    "generateBackground": "linear-gradient(rgb(78, 96, 56) 0%, rgb(67, 84, 47) 100%)",
    "generateFont": "\"Playfair Display\", Georgia, serif",
    "overflowX": 0
  },
  {
    "themeButton": "Comic",
    "token": "comic",
    "generateBackground": "rgb(246, 168, 29)",
    "generateFont": "Bangers, system-ui, sans-serif",
    "overflowX": 0
  }
]
```

## Hosted Proof

Run label: Hosted Space Dry Run

- Space repo: `build-small-hackathon/epic-errands`
- Space URL: `https://build-small-hackathon-epic-errands.hf.space/`
- namespace env: `HF_HACKATHON`
- upload actor/token env: `HF_2` / `HF_TOKEN_2`
- lifecycle stage: `testing`
- SDK: Gradio
- hardware: `cpu-basic`
- visibility: private
- deployed SHA: `f443226def4c19b999f36c0db9ee6f468973f796`

Hosted `/config` proof:

```json
{
  "api_names": ["epic_bootstrap", "epic_generate_goal", "epic_diy_preview"],
  "has_btn_primary_override": true,
  "has_child_span_override": true,
  "has_old_black": false,
  "runtime_stage": "RUNNING"
}
```

Hosted named API smoke:

```json
{
  "backend_transport": "gradio_blocks_named_api",
  "event_id_present": true,
  "fallback_used": true,
  "model_backend": "static_review_asset",
  "model_runtime": "none",
  "theme": "comic",
  "title": "Mission: Everyday Hero"
}
```

## Boundary

This proves the private hosted deterministic Gradio app has the theme styling
boundary fix. It does not prove hosted live-model execution.
