# Epic Errands V2 Local DIY Growth Hotfix

Checked: 2026-06-15T15:16:04Z

## Scope

Debug and fix the issue where the HF Space-style V2 app appeared to keep adding
content at the bottom after opening DIY.

Proof claimed:

- Local HF-like run uses the direct custom `gradio.Server` app, matching the
  v0/v1 pattern.
- Desktop browser growth sampling is stable on Home and DIY.
- 390px mobile browser growth sampling is stable on Home and DIY.

Not claimed:

- Redeployed HF Space proof.
- Public release.
- Judge-ready proof.
- Hosted live-model execution.

## Root Cause

The previous V2 Space package wrapped the custom app in a Gradio `Blocks`
`gr.HTML` component containing a `srcdoc` iframe. That nested iframe shape was
not used by v0/v1 and can interact badly with hosted Space layout/resize
behavior, creating the appearance that more content is continuously being added
at the bottom.

The local direct-server route did not show an application-level append loop.
The measured issue class was the wrapper architecture, not repeated app state
mutation.

## Fix

`space/app.py` now launches the same custom `gradio.Server` surface in local and
Space-like mode:

- `server = build_server()`
- `app = server`
- `__main__` launches `app`

The unused Gradio `Blocks` iframe fallback and embedded `srcdoc` helpers were
removed from `space/app.py`.

## Verification

Commands:

```bash
node --check product/5-idea-epic-errands/7-v2-epic-errands-app/space/frontend/scripts/app.js
PYTHONPYCACHEPREFIX=/private/tmp/epic-errands-v2-pycache python3 -m compileall -q product/5-idea-epic-errands/7-v2-epic-errands-app/space
PYTHONPYCACHEPREFIX=/private/tmp/epic-errands-v2-pycache PYTHONPATH=product/5-idea-epic-errands/7-v2-epic-errands-app/space SPACE_ID=local-test .venv/bin/python -c "import app; print(type(app.app).__name__, type(app.server).__name__)"
python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate ux
```

Import result:

```text
Server Server
```

Local target:

```bash
SPACE_ID=local-test PYTHONPATH=product/5-idea-epic-errands/7-v2-epic-errands-app/space PORT=7865 .venv/bin/python product/5-idea-epic-errands/7-v2-epic-errands-app/space/app.py
```

Desktop browser sampling:

- Home: `iframeCount=0`, `scrollHeight=720`, `elementCount=85`,
  stable across 4 samples.
- DIY route: `iframeCount=0`, `diyLabMentions=1`, `previewMentions=1`,
  `scrollHeight=2766`, `elementCount=89`, stable across 6 samples.

Mobile 390 x 844 browser sampling:

- Home: `iframeCount=0`, `scrollHeight=844`, `elementCount=85`,
  stable across 3 samples.
- DIY route: `iframeCount=0`, `diyLabMentions=1`, `previewMentions=1`,
  `scrollHeight=2221`, `elementCount=89`, stable across 4 samples.

