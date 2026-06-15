# Epic Errands V2 HF Space DIY Hotfix

Checked: 2026-06-15T14:58:21Z

Superseded locally by:
`product/5-idea-epic-errands/7-v2-epic-errands-app/evidence/local-diy-growth-hotfix-2026-06-15.md`.
The later fix removes the Gradio `Blocks` iframe wrapper and returns to the
direct `gradio.Server` pattern used by v0/v1.

## Scope

Fix the private HF Space behavior where clicking the DIY tab did not open the
DIY Lab and instead appeared to keep adding content at the bottom.

Proof claimed:

- Local HF-like embedded Gradio wrapper opens DIY inline.
- Local desktop and 390px mobile checks show one DIY Lab and one iframe.
- Private HF Space config contains the embedded DIY guard and inline DIY copy.

Not claimed:

- Public release.
- Judge-ready proof.
- Hosted live-model execution.
- Full visual browser proof of the private hosted Space.

## Root Cause

The private HF Space runs the custom app inside a Gradio `srcdoc` iframe. The
old DIY tab used `window.location.assign("/diy?...")`, which is valid for the
local custom server but not for the hosted Gradio wrapper. On the hosted Space,
that absolute route could reload the Gradio app inside the iframe, creating a
recursive embedded Space appearance.

## Fix

- `space/frontend/scripts/app.js` now detects
  `window.EPIC_EMBEDDED_SPACE_MODE`.
- In embedded Space mode, the DIY tab renders the DIY Lab inline instead of
  navigating to `/diy`.
- The local custom-server `/diy` route remains available outside embedded Space
  mode.
- `space/app.py` sets `window.EPIC_EMBEDDED_SPACE_MODE = true` in the hosted
  `srcdoc` and includes the DIY CSS in the embedded page.

## Verification

Commands:

```bash
node --check product/5-idea-epic-errands/7-v2-epic-errands-app/space/frontend/scripts/app.js
PYTHONPYCACHEPREFIX=/private/tmp/epic-errands-v2-pycache python3 -m compileall -q product/5-idea-epic-errands/7-v2-epic-errands-app/space
PYTHONPYCACHEPREFIX=/private/tmp/epic-errands-v2-pycache PYTHONPATH=product/5-idea-epic-errands/7-v2-epic-errands-app/space .venv/bin/python -c "import app; print(type(app.app).__name__, type(app.server).__name__)"
python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate ux
```

Local embedded browser proof:

- Target: `http://127.0.0.1:7862/`
- Desktop: repeated DIY clicks kept URL at `/`, produced exactly one DIY Lab,
  exactly one iframe mention, and no recursive Space copy.
- Mobile 390 x 844: DIY opened inline, `V2 Preview Inputs` and `Update Preview`
  were present, and there was exactly one iframe mention.

Hosted private Space proof:

- Repo: `build-small-hackathon/epic-errands`
- URL: `https://build-small-hackathon-epic-errands.hf.space/`
- Evidence JSON:
  `product/5-idea-epic-errands/7-v2-epic-errands-app/evidence/hf-space-v2-diy-hotfix-check.json`
- Result: authenticated `/config` passed on attempt 3 with title
  `Epic Errands V2`, one Gradio component, `epic-iframe`,
  `EPIC_EMBEDDED_SPACE_MODE`, and inline DIY copy present.
