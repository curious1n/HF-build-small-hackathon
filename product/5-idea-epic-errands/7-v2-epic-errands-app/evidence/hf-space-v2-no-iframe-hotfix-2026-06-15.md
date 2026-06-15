# Epic Errands V2 HF Space No-Iframe Hotfix

Checked: 2026-06-15T15:30:00Z

## Scope

Hotfix the private HF Space after the DIY tab/bottom-growth issue.

Proof claimed:

- Private HF Space is running a Gradio `Blocks` shell with one HTML component.
- The hosted shell no longer uses an app iframe or `srcdoc`.
- The hosted HTML contains the direct app mount.
- The hosted `js_on_load` contains embedded mode, the app start guard, and
  inline DIY rendering.

Not claimed:

- Full hosted browser UAT, because the Space is private and browser auth was
  not exercised here.
- Public release.
- Judge-ready proof.
- Hosted live-model execution.

## Debug Result

A local direct `gradio.Server` fix removed the growth issue locally, but HF
Gradio SDK hosting did not expose the custom `Server` routes when `app` was a
`Server` object. The deployed HF-compatible fix keeps `app` as a Gradio
`Blocks` object while removing the previous `srcdoc` iframe wrapper.

## Deployed Shape

- `app = build_hosted_demo()` for HF Gradio SDK import.
- `server = build_server()` remains available for local custom route testing.
- `build_hosted_demo()` renders `<div id="app"></div>` in a normal Gradio HTML
  component, not an iframe.
- `js_on_load` injects the existing V2 app JS, asset manifest, embedded mode,
  and the start guard.
- DIY opens inline in hosted mode instead of navigating to `/diy`.

## Hosted Proof

Evidence JSON:

`product/5-idea-epic-errands/7-v2-epic-errands-app/evidence/hf-space-v2-no-iframe-hotfix-check.json`

Result:

- Space repo: `build-small-hackathon/epic-errands`
- Space URL: `https://build-small-hackathon-epic-errands.hf.space/`
- Observed SHA: `28fdbcc1368a59dc098d5c92b33352e10ca9400b`
- Runtime stage: `RUNNING`
- Hardware: `cpu-basic`
- Visibility: private
- Gradio mode: `blocks`
- Component count: `1`
- Component id: `epic-hosted-shell`
- `html_has_epic_iframe=false`
- `html_has_srcdoc=false`
- `js_on_load_has_embedded_mode=true`
- `js_on_load_has_start_guard=true`
- `js_on_load_has_inline_diy=true`

