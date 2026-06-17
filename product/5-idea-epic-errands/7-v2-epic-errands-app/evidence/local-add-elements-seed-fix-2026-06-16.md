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

Additional UI correction pass:

- Local URL: `http://127.0.0.1:7873`.
- Settings:
  - Removed Settings-side `Generation References`.
  - Parent and child photos render as circular photo tokens using decoded `720 x 720` seeded images.
  - Parent reference audio renders through the app-owned circular play/pause button, with no visible stock audio player.
  - App Styling renders three image tiles using decoded `1024 x 1024` base theme images.
  - Tapping Classroom selects it; tapping Classroom again returns to Questbook.
- Parent:
  - `Generation References` renders actual circular parent/child photos.
  - Tapping a selected photo deselects it; tapping an unselected photo selects it.
  - Review Goal uses one custom circular audio button and no `audio[controls]`.
  - Generated review image decoded from `add-elements/phase2-questbook.png` at `1024 x 1024`.
- Kid:
  - Goal thumbnails render two per row.
  - Tapping a thumbnail switches the selected thumbnail and keeps the full goal card open.
  - Full goal card uses a custom circular audio button and no stock audio player.
- Approval:
  - Parent approval button changes to `Approved` after approval.
  - Removed visible `approved reward given` text from the approval row.
- Mobile/browser checks:
  - `390 x 844` viewport had no horizontal overflow in checked states.
  - One `.v2-shell` remained mounted and `.screen-in` stayed absent.
  - Console errors/warnings: none observed through Browser dev logs.
  - Audio files decode in browser; automated play click did not keep playback active, so this pass claims custom control rendering/state wiring and media decode, not audible playback proof.

Second UI correction pass:

- Local URL: `http://127.0.0.1:7873`.
- Static checks:
  - `node --check product/5-idea-epic-errands/7-v2-epic-errands-app/space/frontend/scripts/app.js`: pass.
  - `python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate implementation`: pass, P0/P1/P2 = 0.
  - `python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate ux`: pass, P0/P1/P2 = 0.
  - `git diff --check -- product/5-idea-epic-errands/7-v2-epic-errands-app`: pass.
- Mobile Browser UAT at `390 x 844`:
  - Theme switching no longer changes the measured shell width: Classroom, Questbook, and Comic each measured `appWidth=344`, `cardWidth=344`, `overflowX=0` on the Settings tab.
  - Comic selected theme tile measured cream background with dark text (`rgb(241, 236, 221)` / `rgb(26, 26, 26)`), matching the V1 comic token direction for high-contrast ink on cream panels.
  - Kid tab initially rendered thumbnail grid only: `inlineKidCards=0`, `modals=0`, `thumbGridColumns="139.406px 139.406px"`.
  - Tapping a goal thumbnail opened one dialog-style full goal card modal: `role="dialog"`, `aria-modal="true"`, one custom audio button, no `audio[controls]`.
  - Kid modal centered on mobile after CSS correction: left/right inset `18px / 18px`, width `354px`, `overflowX=0`.
  - Closing the modal returned the Kid tab to thumbnail-only state: `kidCardCount=0`, `modalCount=0`.
  - DIY tab rendered only one embedded workflow iframe with `src="/diy-workflow/"`.
  - DIY tab removed old placeholder/copy and preview stack: beta text absent, `V2 Preview Inputs` absent, `Pipeline` absent, `Trace` absent.
  - DIY iframe was centered in its wrapper (`frameLeftDelta=1`, `frameRightDelta=1`) and the iframe body loaded `Epic Errands DIY Modal Dry Run` with workflow nodes/edges.
  - Console errors/warnings: none observed through Browser dev logs.

Fixed-height tab pass:

- Local URL: `http://127.0.0.1:7873`.
- Static checks:
  - `node --check product/5-idea-epic-errands/7-v2-epic-errands-app/space/frontend/scripts/app.js`: pass.
  - `python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate implementation`: pass, P0/P1/P2 = 0.
  - `python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate ux`: pass, P0/P1/P2 = 0.
  - `git diff --check -- product/5-idea-epic-errands/7-v2-epic-errands-app`: pass.
- Mobile Browser UAT at `390 x 844`:
  - All tabs measured the same shell size: `shellHeight=724`, `shellWidth=359`.
  - All tabs measured no document overflow: `pageOverflowX=0`, `pageOverflowY=0`.
  - `.app-screen` held the scrollable tab content at `screenClientHeight=548`.
  - Tall tabs scroll internally instead of resizing the app frame:
    - Parent: `screenScrollHeight=606`.
    - Settings: `screenScrollHeight=1100`.
    - DIY: `screenScrollHeight=685`, with one embedded workflow iframe.
  - Home and Kid fit without internal scroll growth: `screenScrollHeight=548`.
- Console caveat:
  - The embedded `/diy-workflow/` Gradio workflow iframe logs `AbortError: BodyStreamBuffer was aborted` / `Unexpected error Connection errored out` when loaded in Browser UAT.
  - The fixed-height shell proof still passed; this pass does not claim the DIY workflow iframe is console-clean.

Fixed-height bump pass:

- Requested change: increase the fixed shell height because the `724px` pass felt too low.
- CSS update:
  - Mobile shell height now uses the earlier taller fixed value: `clamp(560px, calc(100dvh - 96px), 748px)`.
  - Mobile stage top/bottom padding is set to `48px` so the taller shell has more room.
- Static checks:
  - `node --check product/5-idea-epic-errands/7-v2-epic-errands-app/space/frontend/scripts/app.js`: pass.
  - `python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate implementation`: pass, P0/P1/P2 = 0.
  - `python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate ux`: pass, P0/P1/P2 = 0.
  - `git diff --check -- product/5-idea-epic-errands/7-v2-epic-errands-app`: pass.
- Browser UAT:
  - Fresh Browser recheck was blocked because the in-app Browser connector returned no available browsers after reconnect.
  - This pass therefore claims static code/gate proof only, not fresh rendered Browser proof.

Three-goal preload pass:

- Source requirement read: `../5-v1-epic-errands-app/README.md`.
- V1 requirement carried forward: the demo starts loaded with three generated-media goals:
  - `Clean up my room before dinner`.
  - `Finish my class project outline`.
  - `Read for 20 minutes`.
- Implementation:
  - Backend `SEED_GOALS` now lists all three demo goals with per-goal state.
  - Browser fallback seed state now mirrors the same three goals.
  - Default selected goal is `goal-seed-clean-room`.
  - Clean-room starts `completed / waiting_for_approval` so the parent approval queue is preloaded.
  - Project-outline and read-20 start `not_started / not_reviewed`.
- Static checks:
  - `node --check product/5-idea-epic-errands/7-v2-epic-errands-app/space/frontend/scripts/app.js`: pass.
  - `PYTHONPYCACHEPREFIX=/private/tmp/epic-errands-pycache python3 -m py_compile .../fixtures.py .../generation.py`: pass.
  - `python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate implementation`: pass, P0/P1/P2 = 0.
  - `python3 scripts/check_design_handoff.py --idea product/5-idea-epic-errands/7-v2-epic-errands-app --gate ux`: pass, P0/P1/P2 = 0.
  - `git diff --check -- product/5-idea-epic-errands/7-v2-epic-errands-app`: pass.
- Bootstrap smoke:
  - Fresh local server: `http://127.0.0.1:7874`.
  - `/api/bootstrap` returned `goal_count=3`.
  - Referenced images/audio all exist on disk:
    - `generated-v2/clean-room-questbook-d35e6ee10c.png` / `generated-v2/clean-room-questbook-01493f395c.wav`.
    - `add-elements/phase2-questbook.png` / `generated-v2/project-outline-questbook-bddf03af1a.wav`.
    - `generated-v2/read-20-questbook-39aac8ba25.png` / `generated-v2/read-20-questbook-5805518930.wav`.
- Browser UAT:
  - Not rerun in this pass because the in-app Browser connector still reported no available browsers after reconnect.
  - This pass claims backend/static seed proof plus fresh local bootstrap proof, not rendered mobile Browser proof.

DIY frame height bump pass:

- Requested change: increase the embedded `/diy-workflow/` frame height by 20%.
- CSS update:
  - `.diy-workflow-frame` height cap increased from `640px` to `768px`.
  - Viewport-relative frame height increased from `72dvh` to `86.4dvh`.
  - Minimum frame height increased from `480px` to `576px`.
- Static checks:
  - `git diff --check -- product/5-idea-epic-errands/7-v2-epic-errands-app/space/frontend/styles/app.css`: pass.
- Browser UAT:
  - Not rerun in this pass; this claims static CSS proof only.

Hosted goal latency hotfix:

- User-observed hosted symptom: after clicking Goal, the app showed
  `Fallback Hosted backend was unavailable, so this preview used browser fallback`
  after about `98375ms`.
- Root cause:
  - The hosted Gradio `epic_generate_goal` endpoint was still calling
    `build_generated_goal_with_live_fallback()`.
  - When hosted env vars enabled live generation, the endpoint waited on the
    Modal path before returning deterministic fallback.
- Implementation:
  - HF-hosted Gradio endpoint `_hosted_generate_goal()` now calls
    `build_generated_goal()` directly.
  - This keeps the HF-only hosted app on packaged deterministic assets and does
    not call Modal for Goal preview.
- Upload:
  - Repo: `build-small-hackathon/epic-errands`.
  - URL: `https://build-small-hackathon-epic-errands.hf.space/`.
  - Commit: `d04b36e3d73de5794a4dc65d12faa6180e4232ec`.
  - Commit message: `Hotfix hosted goal generation latency`.
- Hosted smoke:
  - Endpoint: `/gradio_api/call/epic_generate_goal`.
  - Payload goal: `Read for 20 minutes`, theme `questbook`.
  - `post_ms=1243`, `total_ms=3020`.
  - Response provenance:
    - `backend_transport=gradio_blocks_named_api`.
    - `model_runtime=none`.
    - `model_backend=static_review_asset`.
    - `fallback_used=true`.
    - `fallback_reason=deterministic hosted dry-run; Modal/live generation disabled or unavailable`.

Known limits:

- This is local deterministic fallback proof using cached spike outputs.
- It does not prove a new live FLUX/Modal request or hosted Space behavior.
