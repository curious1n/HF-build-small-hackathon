# Epic Errands V2 Style Modes

Status: V2 delta from V1. V2 keeps the V1 style modes and adds clearer
boundaries between app UI theme, generation mode, and generated media.

## Shared Rules

- Style mode is app UI styling, not model selection.
- Style mode affects shell tokens, copy tone, parent/kid titles, reward nouns,
  goal-text overlay styling, and composed-card treatment.
- Style mode does not change Quality vs Speed mode.
- Style mode does not regenerate, replace, or mutate accepted generated image
  or audio assets.
- Style changes must remain readable at 390px and 360px.
- Copy stays age-8 friendly and avoids scary stakes.

## Classroom

| Field | Value |
| --- | --- |
| Label | Classroom |
| Product id | `classroom` |
| Existing CSS skin | `storybook` |
| Goal noun | Quest |
| Parent title | Classroom Captain |
| Kid title | Star Student |
| Reward noun | Badge |
| Copy tone | Warm, clear, encouraging school-adventure language. |
| Visual language | Notebook paper, stickers, pencils, bright classroom supplies, soft rounded controls. |
| Overlay direction | High-readability label plate with notebook/sticker energy. |
| Generated audio direction | Friendly teacher-like narrator, calm and clear. |
| Waiting copy | Waiting for Classroom Captain approval. |

## Questbook

| Field | Value |
| --- | --- |
| Label | Questbook |
| Product id | `questbook`; legacy `magical` normalizes to `questbook` |
| Existing CSS skin | `atelier` |
| Goal noun | Quest |
| Parent title | Quest Keeper |
| Kid title | Young Adventurer |
| Reward noun | Crest |
| Copy tone | Premium storybook adventure, warm, practical, never scary. |
| Visual language | Warm parchment, ink dividers, green-and-gold quest actions, serif titles, restrained ornament, clear modern controls. |
| Overlay direction | Parchment caption ribbon or inked title plate, readable over detailed art. |
| Generated audio direction | Calm questbook narrator with clear pacing. |
| Waiting copy | Waiting for Quest Keeper approval. |

Questbook remains the default visible app theme.

## Comic

| Field | Value |
| --- | --- |
| Label | Comic |
| Product id | `comic` |
| Existing CSS skin | `comic` |
| Goal noun | Mission |
| Parent title | Comic Editor |
| Kid title | Panel Hero |
| Reward noun | Starburst |
| Copy tone | Punchy action-comic language with short sentences and positive energy. |
| Visual language | Bright panel blocks, speech bubbles, halftone accents, bold labels without cramped text. |
| Overlay direction | Speech-bubble or panel-caption energy, but with restrained text length and strong contrast. |
| Generated audio direction | Energetic narrator, but not loud, frantic, or overstimulating. |
| Waiting copy | Waiting for Comic Editor approval. |

## Generation Mode Boundary

| Mode | V2 status | Text | Image | Audio |
| --- | --- | --- | --- | --- |
| Quality | Enabled and selected | `nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF`, `llama.cpp`, GGUF, `Q4_K_M` | `black-forest-labs/FLUX.2-klein-9B`, Diffusers, safetensors, `bf16`, 1024 x 1024 | `openbmb/VoxCPM2`, `voxcpm`, safetensors, `bf16` |
| Speed | Visible/planned/disabled | Same planned text path unless changed later | `black-forest-labs/FLUX.2-klein-4B`, 720 x 720 planned | Same model, lower settings or cached assets possible later |

Do not label the selected V2 Quality text path as Speed just because older
spike files used the `speed_gguf_q4` name.
