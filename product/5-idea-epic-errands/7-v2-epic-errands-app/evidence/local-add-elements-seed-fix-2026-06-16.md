# Local Add-Elements Seed Fix

Run label: `local-add-elements-seed-fix-2026-06-16`

Scope:

- Local V2 app proof for add-elements spike asset wiring and seeded reference inputs.
- No new FLUX/Modal run, hosted Space proof, public proof, or judge-ready proof claimed.

Source contract:

- `../6-spike-add-elements-assets/README.md`
- `../6-spike-add-elements-assets/phase-0-spec-and-qa.md`
- `SOURCE_MAP.md`
- `design/visual-design.md`

Implementation notes:

- Seeded parent photos now use spike portraits:
  - `reference-seeds/parent-reference-photo.png`
  - `reference-seeds/placeholder-female-parent-720.png`
- Seeded child photos now use spike portraits:
  - `reference-seeds/kid-reference-photo.png`
  - `reference-seeds/placeholder-girl-720.png`
- Seeded parent reference audio now uses:
  - `reference-seeds/parent-reference-audio.m4a`
- Packaged quality base theme plates:
  - `base-theme-images/classroom-base-theme-1024.png`
  - `base-theme-images/questbook-base-theme-1024.png`
  - `base-theme-images/comic-base-theme-1024.png`
- Packaged cached FLUX add-elements outputs:
  - `add-elements/phase1-classroom.png`
  - `add-elements/phase1-questbook.png`
  - `add-elements/phase1-comic.png`
  - `add-elements/phase2-classroom.png`
  - `add-elements/phase2-questbook.png`
  - `add-elements/phase2-comic.png`

Verification:

- `node --check .../space/frontend/scripts/app.js`: pass.
- `.venv/bin/python -m py_compile .../space/app.py .../fixtures.py .../generation.py`: pass.
- Backend smoke:
  - default goal: `Finish my class project outline`
  - default selected refs: `parent-dad-demo`, `child-girl-demo`
  - default image: `add-elements/phase2-questbook.png`
  - default provenance: `cached_flux2_add_elements_phase2`, `base_theme_plus_parent_child_goal`
  - default base image: `base-theme-images/questbook-base-theme-1024.png`
- Design gates:
  - `python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate implementation`: pass, P0/P1/P2 = 0.
  - `python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate ux`: pass, P0/P1/P2 = 0.
- Hosted embedded manifest includes the new seed, base-theme, and add-elements assets.
- Browser mobile UAT at `390 x 844`, local URL `http://127.0.0.1:7872`:
  - initial Home rendered one stable shell, five tabs, no `.screen-in`, no horizontal overflow.
  - Settings showed four seeded portraits and `parent-reference-audio.m4a`.
  - Generate from seeded default state produced Review Goal with decoded `add-elements/phase2-questbook.png` at `1024 x 1024`.
  - Review Goal overlay remained editable app-owned text.
  - Review provenance showed `cached_flux2_add_elements_phase2 / base_theme_plus_parent_child_goal`.
  - Accept published the same add-elements image to Kid Goals with read-only overlay and playable audio.
  - Console errors/warnings: none observed through Browser dev logs.

Known limits:

- This is local deterministic fallback proof using cached spike outputs.
- It does not prove a new live FLUX/Modal request or hosted Space behavior.
