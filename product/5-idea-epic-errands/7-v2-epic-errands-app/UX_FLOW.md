# Epic Errands V2 UX Flow

Status: final UX contract for the fast V2 build.

Visual source: preserve V1 styling from `../5-v1-epic-errands-app/`.
Use [SOURCE_MAP.md](SOURCE_MAP.md) for links to the V1 implementation anchors,
spike evidence, and do-not-redo notes behind this flow.

## Primary Navigation

V2 has five user-facing tabs:

1. Home
2. Parent Goals
3. Kid Goals
4. Settings
5. DIY

The app remains mobile-first around the V1 390px target.

## 1. Home

Purpose: give the parent and child a quick status view.

Visible behavior:

- Shows the active theme styling: Classroom, Questbook, or Comic.
- Shows active goals, goals waiting for approval, and rewards approved.
- Gives quick access to the current kid goal card.
- Uses the V1 parent/kid language and reward tone for the selected theme.

No model controls live on Home.

## 2. Settings

Purpose: configure app styling and generation inputs before creating goals.

Sections:

- App styling:
  - Classroom
  - Questbook
  - Comic
  - app styling changes the UI shell and overlay styling, not the generation
    mode, model choice, or already-accepted image/audio assets.
- Parent details:
  - upload/remove parent photos;
  - upload/remove parent reference audio;
  - parent reference audio is optional.
- Children details:
  - upload/remove child photos.
- Generation references:
  - choose parent photo, child photo, or uploaded image/reference for goal
    image generation.
- Generation mode:
  - Quality: enabled and selected for hackathon;
  - Speed: visible as planned/disabled;
  - Quality image size: 1024 x 1024;
  - planned Speed image size: 720 x 720.

Audio behavior:

- Audio generation is enabled.
- If parent reference audio exists, the generation path can use it for
  parent-voice audio.
- If parent reference audio is missing, audio still generates using the default
  configured voice behavior.

## 3. Parent Goals

Purpose: create and review generated goals.

Create Goal flow:

1. Parent enters an ordinary goal.
2. Parent chooses which image references to use:
   - parent photo;
   - child photo;
   - uploaded custom image/reference.
   These are generation inputs and are independent from the current app UI
   styling.
3. Parent starts generation in Quality mode.
4. The app runs the hardcoded V2 generation pipeline:
   - text/quest JSON;
   - personalized image;
   - audio.
5. Parent lands on Review Goal.

Runtime labels shown in the product can be concise, but the app contract should
keep the model details available for provenance:

| Step | Quality model/runtime |
| --- | --- |
| Text / quest JSON | `nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF`, `llama.cpp`, GGUF, `Q4_K_M` |
| Image | `black-forest-labs/FLUX.2-klein-9B`, Diffusers, safetensors, `bf16`, 1024 x 1024 |
| Audio | `openbmb/VoxCPM2`, `voxcpm`, safetensors, `bf16` |

## 4. Review Goal

Purpose: approve or discard the generated goal before it reaches the kid.

Visible content:

- Generated image.
- Editable goal text layer over the generated image.
- Generated title/narration/reward text.
- Generated audio preview.
- Model/provenance summary in compact form.

Allowed actions:

- Edit the app-owned text layer over the generated image.
- Accept the generated goal.
- Cancel the generated goal.

Locked fast-build constraints:

- The generated image cannot be changed from Review Goal.
- The generated audio cannot be changed from Review Goal.
- Editing the text layer updates only app-owned text/copy, not the generated
  image pixels or audio file.
- The overlay behavior should follow the prior text-overlay prototype linked
  from [SOURCE_MAP.md](SOURCE_MAP.md): generated images should not contain goal
  text or text containers.
- Cancel discards the generated goal and returns the parent to Parent Goals.
- Accept publishes the generated goal to Kid Goals.

## 5. Kid Goals

Purpose: let the child use the approved generated goals.

Flow:

1. Kid sees thumbnail cards only.
2. Kid taps a thumbnail.
3. Kid sees a goal card with:
   - generated image;
   - app-owned text overlay;
   - generated title/narration/reward;
   - generated audio;
   - completion action.
4. Kid taps completion.
5. Goal moves to waiting-for-parent approval with theme-specific copy.

## 6. Parent Approval

Purpose: close the parent/kid reward loop from V1.

Flow:

1. Parent opens Parent Goals.
2. Parent sees completed goals waiting for review.
3. Parent approves the reward.
4. Kid Goals shows the reward as granted.

No reject/edit/send-back path is required for fast V2.

## 7. DIY

Purpose: inspect and customize the same generation flow the main app follows.

Implementation boundary:

- DIY is a separate isolated app/folder inside the same V2 app package.
- The main app's DIY tab routes to the isolated DIY surface.
- DIY uses hardcoded V2 flow data for the fast build.

DIY mirrors the main app flow:

```text
plain goal
-> text / quest JSON
-> image request/result
-> audio request/result
-> composed goal card
-> trace/provenance details
```

DIY shows:

- selected theme;
- ordinary goal;
- selected parent/child/custom image references;
- generated text step;
- generated image step;
- generated audio step;
- model IDs, runtimes, formats, quantization, and fallback labels;
- composed preview;
- JSON trace.

DIY edit behavior:

- Parent can edit the hardcoded workflow draft fields in DIY.
- DIY can update the local preview/trace inside the DIY surface.
- Saving the DIY edits back into the main app is labelled coming soon.
- DIY should inherit the prior five-node dry-run pipeline and beta
  `gr.Workflow` caveat linked from [SOURCE_MAP.md](SOURCE_MAP.md).

DIY is not the kid-facing flow.

## Verification Checklist

For the fast V2 build, local browser verification should cover:

- Settings upload/remove controls render and update session state.
- Quality mode is enabled; Speed mode is visibly disabled/planned.
- Audio generation appears enabled even with no parent reference audio.
- Parent can generate a goal and reach Review Goal.
- Review Goal supports text-layer editing, Accept, and Cancel.
- Review Goal does not offer image or audio editing.
- Accept sends the goal to Kid Goals.
- Cancel does not publish the goal.
- Kid can complete a goal.
- Parent can approve the reward.
- DIY opens in an isolated surface and mirrors the hardcoded pipeline.
- DIY edit controls update only the DIY preview/trace and show saving to app as
  coming soon.
