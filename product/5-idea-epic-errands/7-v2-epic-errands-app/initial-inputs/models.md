| Capability | Quality mode | Speed mode |
| - | - | - |
| Text / quest JSON | [`nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF`](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF), `llama.cpp`, GGUF, `Q4_K_M` | [`nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF`](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF), `llama.cpp`, GGUF, `Q4_K_M` |
| ASR / speech-to-text | [`nvidia/nemotron-3.5-asr-streaming-0.6b`](https://huggingface.co/nvidia/nemotron-3.5-asr-streaming-0.6b), NeMo / PyTorch, `.nemo`, not labelled | [`onnx-community/nemotron-3.5-asr-streaming-0.6b-onnx-int4`](https://huggingface.co/onnx-community/nemotron-3.5-asr-streaming-0.6b-onnx-int4), ONNX Runtime, ONNX encoder/decoder/joint + VAD, `int4` |
| Voice generation | [`openbmb/VoxCPM2`](https://huggingface.co/openbmb/VoxCPM2), `voxcpm`, `safetensors`, `bf16` | Same model and engine. Speed mode may use lower generation settings, shorter timeout, or cached voice assets, but not a different model. |
| Image generation | [`black-forest-labs/FLUX.2-klein-9B`](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B), `diffusers`, `safetensors`, `bf16` | [`black-forest-labs/FLUX.2-klein-4B`](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B), `diffusers`, `safetensors`, `bf16`; GGUF serving path remains open. |

## V2 Override Notes

- V2 intentionally uses the GGUF Nemotron path for Quality text generation.
  This supersedes the older V1 planning table where BF16/vLLM was labelled as
  quality and GGUF was labelled as speed.
- In the text spike, the same V2-selected GGUF path is named `speed_gguf_q4`.
  Do not switch V2 back to BF16 because of that old label.
- ASR is listed for pipeline/eval context. It is not required in the fast V2
  parent/kid UX unless transcript or audio-QA proof becomes in scope.
- Speed mode is visible/planned but disabled for the hackathon app.
- Generation mode owns output size policy: Quality image outputs are
  1024 x 1024; planned Speed image outputs are 720 x 720.
- App UI styling is independent from generation mode and should not mutate
  already accepted generated assets.

## Evidence And Runtime Links

Text:

- [Text generation spike README](../../6-spike-text-gen-check/README.md)
- [Model access preflight](../../6-spike-text-gen-check/evidence/model_access_preflight.json)
- [Text run summary](../../6-spike-text-gen-check/evidence/summary.json)
- [Text cost/time](../../6-spike-text-gen-check/evidence/cost_time.md)
- [GGUF raw text](../../6-spike-text-gen-check/evidence/speed_gguf_q4_raw_text.txt)
- [Text Modal script](../../6-spike-text-gen-check/modal_nemotron_text_compare.py)

Image:

- [Add-elements README](../../6-spike-add-elements-assets/README.md)
- [Image phase spec and QA](../../6-spike-add-elements-assets/phase-0-spec-and-qa.md)
- [FLUX visual QA](../../6-spike-add-elements-assets/evidence/flux2-klein-quality-phases-20260615-060104/qa/visual_qa.md)
- [FLUX runtime summary](../../6-spike-add-elements-assets/evidence/flux2-klein-quality-phases-20260615-060104/metadata/summary.json)

Audio:

- [VoxCPM2 voice script](../../6-spike-voice-change/modal_voxcpm2_voice_clone.py)
- [VoxCPM2 voice evidence](../../6-spike-voice-change/outputs/voxcpm2-voice-clone-evidence.json)
- [V1 generated-media UAT](../../5-v1-epic-errands-app/evidence/v1-generated-media-uat.md)

Reusable runtime status:

- [Local runtime status](../../../4-poc-sponsor-model-runtime-matrix/LOCAL_RUNTIME_STATUS.md)
- [Runtime matrix](../../../4-poc-sponsor-model-runtime-matrix/MODEL_MATRIX.md)
- [Download and quantization plan](../../../4-poc-sponsor-model-runtime-matrix/DOWNLOAD_QUANTIZATION_PLAN.md)
- [Model manifest](../../../4-poc-sponsor-model-runtime-matrix/model_manifest.json)

Broader source map:

- [V2 source map](../SOURCE_MAP.md)
