# Hackathon Jam Board

Source: `~/.codex/session_index.jsonl`, `~/.codex/history.jsonl`, and matching session JSONL files under `~/.codex/sessions/2026/06/`. Timestamps below show IST first, with source UTC noted where useful.

Updated: 2026-06-10.

## Board Snapshot

| Idea | First logged Codex thread | Current stage | Main evidence in repo | Next decision |
| - | - | - | - | - |
| Mushroom Courtroom | 2026-06-07 13:29 IST (`019ea0f6-f950-7943-b786-c27e3db97b90`) | v0 built, v1 sponsor branch/spec in progress | `2-spike/`, `4-v0/`, `5-v1-sponsor-models/` | Is it primary or supporting experiment after real MiniCPM/OpenBMB smoke and mobile UAT? |
| The Giggling Wardrobe / Riddikulus Fear Flip | 2026-06-07 19:43 IST (`019ea26e-887c-7900-b48e-c681ccbdc704`) | deepest iteration, v2 image UX in progress | `4-v0/`, `5-v1-sponsor-models/`, `6-v2-add-image/`, RCA doc | Can it prove sponsor text plus credible image route fast enough for the final demo? |
| Wicked Playgrounds | 2026-06-08 00:31 IST (`019ea376-88e7-75f3-a2ef-6032bdb8b810`) | v0 built, v1 sponsor narration branch | `7-v0/`, `8-v1-sponsor-models/` | Does deterministic gameplay plus sponsor narration make a clearer hackathon story than the more whimsical apps? |
| Cricket Ground Agent / PitchDesk | 2026-06-08 00:40 IST (`019ea37e-54f5-7cd3-aeee-e55d637f9350`) | expanded from booking demo to venue-ops agent | `2-v0-plan.md`, `3-v0/`, `4-v1-venue-ops-agent/` | Keep demo scope tight: booking assistant, venue ops cockpit, or marketing/booking hybrid? |
| Coding Agent idea | 2026-06-09 08:28 IST (`019eaa4d-99fa-7da1-83fe-790ca230b2ae`) | brainstorming only | `2-idea-coding-agent/0-jam.md` | Decide whether to plan/prototype or leave as parked concept. |

## Cross-Board Timeline

| Time | Board event |
| - | - |
| 2026-06-07 12:53-13:22 IST | Initial repo/hackathon exploration, theme lookup, broad web-assisted idea search, and idea capture into `product/2-idea-brainstorm.md`. |
| 2026-06-07 13:29-17:41 IST | Mushroom Courtroom was explored, saved as a jam, turned into a capability spike plan, set up with local `llama.cpp`/media smoke tests, and expanded into spike takeaways plus design directions. |
| 2026-06-07 19:43-2026-06-08 09:49 IST | Riddikulus/Fear Flip was explored, narrowed into The Giggling Wardrobe, designed, planned, implemented as v0, and QA'd. |
| 2026-06-08 00:31-10:08 IST | Wicked Playgrounds was researched, clarified away from Mushroom Courtroom, planned as v0, built, and QA'd. |
| 2026-06-08 00:40-08:52 IST | Cricket Ground Agent was explored around CricHeroes/WhatsApp/Twilio/Gupshup, planned as v0, and given first UX/UI architecture for a simulated booking ops cockpit. |
| 2026-06-08 11:51-12:28 IST | Board audit found sponsor models had been skipped in v0 plans. @cu directed new sponsor-model folders/specs and long-running goal prompts for each candidate app. |
| 2026-06-08 12:28-13:03 IST | Sponsor-model work began for Cricket, Riddikulus, and Wicked, with explicit requirements that deterministic fallback is necessary but not sufficient. |
| 2026-06-09 08:24-10:34 IST | Mushroom v0 was built and then prepared for v1 sponsor-model routing using OpenBMB/MiniCPM terminology. |
| 2026-06-09 08:28-08:43 IST | Coding-agent idea was brainstormed around Nemotron Cascade 2 and JetBrains Mellum 2, but no implementation plan was created. |
| 2026-06-09 10:20-12:21 IST | OpenBMB/MiniCPM API-first rule was pushed across sponsor-model specs; `.env`/HF Space secrets handling became the preferred path before spending HF compute credits. |
| 2026-06-09 10:44-18:41 IST | The Giggling Wardrobe v2 image UX work exposed missed UX/default-image/local-FLUX setup gaps, leading to user-story docs, local FLUX goal prompt, IAB/UAT checks, and RCA. |
| 2026-06-09 11:10-12:08 IST | Cricket/PitchDesk scope expanded from booking assistant to venue ops, marketing, always-on laptop worker, mistake review, brand direction, and system architecture. |
| 2026-06-10 09:37 IST onward | This tracking pass updated/created idea-level `0-jam.md` files and this cross-board tracker from Codex session timestamps. |

## Current Board Risks

| Risk | Where it shows up | Handling rule |
| - | - | - |
| Sponsor models become invisible or skipped | All v1 branches | Every candidate needs wired model config, adapter code, model-mode display, fallback behavior, tests, and at least one documented real-smoke path. |
| Too many ideas, not enough submission focus | All folders | Pick one primary by comparing UAT delight, sponsor proof, HF Space feasibility, mobile usability, and video clarity. |
| HF compute spend drifts | Riddikulus image, Wicked narration, any Space deployment | Use OpenBMB/MiniCPM API from `.env` first where specified; use HF credits sparingly and record when paid GPU/ZeroGPU is actually needed. |
| UX gaps discovered by @cu late | Riddikulus and Cricket especially | Convert expectations into user stories/UAT before implementation, then verify in IAB or a browser-visible path before claiming done. |
| Local model feasibility unclear | Mushroom spike, Riddikulus FLUX | Keep deterministic fallbacks honest, document actual device limits, and avoid presenting fallback as sponsor/model success. |

## Immediate Next Moves

1. Pick a primary candidate for submission.
2. For that candidate, run and document one real sponsor-model smoke with `fallback_used=false`.
3. Run mobile/IAB UAT on the exact demo script.
4. Package only the chosen app for Hugging Face Spaces; keep other ideas as supporting experiments unless they directly strengthen the story.
5. Update `COAGENTS.md` after the primary decision so the todo list stops pulling in five directions at once.
