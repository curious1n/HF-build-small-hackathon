# Epic Errands Running Notes

Epic Errands turns ordinary child goals into illustrated, themed goal cards
with kid-sized steps, rewards, images, and read-aloud audio.

## Artifacts

- App: https://build-small-hackathon-epic-errands.hf.space/
- Space: https://huggingface.co/spaces/build-small-hackathon/epic-errands
- Source repo: https://github.com/curious1n/HF-build-small-hackathon
- Agent traces: https://huggingface.co/datasets/build-small-hackathon/epic-errands-v1-agent-traces
- Public Article: https://huggingface.co/blog/build-small-hackathon/epic-errands-running-notes

## Current State

This file is the single running-notes source for Epic Errands Article updates.
The V1 quick-eval trace note content is folded below instead of being kept as a
separate article source.

The current V2 hosted Space is a private hosted testing package. It serves the
mobile review shell and DIY Lab with deterministic/cached assets and labels
that behavior as fallback. Live model proof exists in recorded evidence outside
the hosted Space package; this running note does not claim hosted live model
execution or judge-ready status.

## Notes

### 2026-06-15 - Text-First Agent Trace Quick Eval

This quick eval checks whether the asset pipeline stays coupled: the text model
creates the canonical goal card first, and image/audio prompts use that
generated card text instead of drifting into unrelated prompts.

What ran:

| Plain goal | Themes |
| --- | --- |
| Clean up my room before dinner | Questbook, Classroom, Comic |
| Finish my class project outline | Questbook, Classroom, Comic |
| Read for 20 minutes | Questbook, Classroom, Comic |

Pipeline:

```text
plain_goal + theme
  -> MiniCPM4.1-8B and Nemotron 3 Nano 4B text attempts
  -> card_text
  -> FLUX image prompt using card_text
  -> VoxCPM2 audio prompt and spoken_text using card_text
  -> Nemotron Speech ASR, when run
```

Result snapshot:

| Surface | Result |
| --- | --- |
| Text prompts | 9/9 rows sent to MiniCPM4.1-8B and Nemotron 3 Nano 4B |
| Card text used | 9/9 rows used schema-valid Nemotron 3 Nano 4B JSON |
| MiniCPM4.1-8B | Ran for all 9 rows, but returned schema-invalid output |
| FLUX | 9/9 generated images |
| VoxCPM2 | 9/9 generated audio clips |
| Nemotron Speech | 9/9 transcripts over the generated audio clips |

The first VoxCPM2 read-goal batch overran, so the runner retried those rows one
at a time through the direct Modal function path. All three read-goal audio
files then persisted, and Nemotron Speech transcribed the completed read batch.

Evidence:

- Dataset commit: https://huggingface.co/datasets/build-small-hackathon/epic-errands-v1-agent-traces/commit/085afdffb7a94d6f068104bcb4e27604582fbe76
- Dataset package source: `product/5-idea-epic-errands/5-v1-epic-errands-app/evidence/demo-full-assets/`
- Human table: `goal-theme-live-asset-table.md`
- Live trace rows: `agent_traces/codex/2026-06-14/live_agent_traces.jsonl`
- Model access preflight: `model_access_preflight.json`

What this proves:

- The trace rows store `text_prompt`, `card_text`,
  `resolved_image_prompt`, `resolved_audio_prompt`, and `spoken_text`.
- FLUX image prompts are resolved from generated card text.
- VoxCPM2 audio prompts are resolved from generated card text.
- Generated assets and ASR transcripts are linked per goal/theme row.

What this does not prove:

- Judge-ready quality.
- Public release readiness.
- Hosted Space live model execution.
- MiniCPM4.1-8B as the default text generator, because its outputs failed the
  current strict JSON schema check.
