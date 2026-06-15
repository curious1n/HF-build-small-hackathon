https://huggingface.co/spaces/build-small-hackathon/
5-15th June 2026 - Hackathon days

## Main tracks:
Backyard AI - Solve a real problem for someone you actually know. Pick a person — a neighbor, a parent, a small-business owner on your street — and build something that makes their day measurably better.

An Adventure in Thousand Token Wood - Build something delightful that wouldn't exist without AI. Wander somewhere weirder. A toy, a tiny game, a strange interactive story, an art experiment that surprises you. The AI should be doing the fun thing — not just helping you build it. Strange is good. Joyful is the bar.


## Constraints:
Small Models Only - Total parameters must be ≤ 32 billion. 
Built on Gradio - Your app must be a Gradio app, hosted as a Hugging Face Space.
Show, Don't Tell - A short demo video and a social-media post 


## Extra points:
Off the Grid - No cloud APIs - model is part of Huggingface space
Llama Champion - run through llama.cpp
Off-Brand - custom FE - (use gradio server)
Sharing is Caring - share trace of the agent running (NOT Codex) to HF Hub 
Field Notes - blog post or report about what you built and what you learned
?Well-Tuned - publish on HF (on Modal credits for fine-tune)


## Useful links
https://github.com/huggingface/ml-intern
https://www.gradio.app/guides/quickstart
https://huggingface.co/blog/introducing-gradio-server
https://github.com/ggml-org/llama.cpp


## Credits
### HF
$20 in Hugging Face credits - cover ZeroGPU time beyond your free quota, hardware-upgraded Spaces, and Inference. 
Bonus: as a member of the hackathon org, you already get 40 min/day of ZeroGPU free.
Past your daily quota, ZeroGPU runs pay‑as‑you‑go at $1 per 10 minutes, straight off these credits. 

### Modal
$250 in Modal compute credits - fine-tunes, batch jobs, and serving your ≤32B models

- https://github.com/modal-labs/modal-examples/tree/main/06_gpu_and_ml/llm-serving
- https://github.com/modal-labs/modal-examples/blob/main/06_gpu_and_ml/yolo/finetune_yolo.py
- https://modal.com/docs/examples/opencode_server
- https://modal.com/blog/building-with-modal-and-the-openai-agent-sdk

### Codex
credits 

## Sponsors' Models / Prizes:

### OpenAI Codex Track
A dedicated prize track with $10,000 in cash + ChatGPT Pro subscriptions for the top 3 builds — and here's the twist: Codex itself is the judge. It reviews every entry and scores on how well you used Codex and the overall quality of your Space.
How to enter:
1. Build your Space with Codex as your coding agent.
2. Push the code to a public GitHub repo — it must contain Codex-attributed commits.
3. Add the repo link to your Space README. That's it — you're in. 


### Modal - cash
fine-tunes, batch jobs, and serving your ≤32B models

"BTW you could use modal for training/finetuning, and deploy on HF anyways, it will get you off grid, and finetuned badge (if you then upload that model to the hub). And you may be considered for modal track as well, although they'll obviously give priority to those projects which use their serverless/sandboxes at inference time."

### Special Awards
#### most merit badges (extra points) stacked
#### Off-Brand Award - best custom UI
#### Tiny titan - best app built on a tiny model — ≤4B parameters
#### Best Demo - great app, great demo video, great social post
#### Best Agentic app
#### Judges' Wildcard

### Nvidia -  win RTX 5080
(only 16GB of VRAM?!)

#### criteria : use Nemotron models
General Purpose Language Models for Reasoning, Chat, and Tool Use

NEMOTRON 3 NANO 30B-A3B
- Use Cases: General-purpose reasoning, coding, chat, RAG, agent workflows

NEMOTRON 3 NANO 4B
- Use Cases: Edge model for RTX/Jetson useful for local assistants, reasoning and tool-use agents

NEMOTRON 3 NANO OMNI 30B-A3B
Use Cases: Audio, image, text, video understanding; document intelligence; GUI agents

coding model - NEMOTRON CASCADE 2 30В-А3B
Use Cases: Advanced math/code reasoning, tool-integrated reasoning

NEMOTRON 3.5 ASR (0.6B)
Use Cases: Voice agents, live captions, multilingual transcription, meeting/audio apps, `accessibility tools`

NEMOTRON SPEECH
Use Cases: Real-time ASR/transcription, multilingual text-to-speech, speaker diarization, speech-to-speech/audio-to-audio agents, captions, voice assistants, meeting/audio apps.

NEMOTRON PARSE v1.2 (<1B)
Use Cases: Extract structured text, tables, markdown, bounding boxes, and semantic classes from PDFs, PPTs, forms, reports, screenshots.

NEMOTRON COLEMBED VL 4B V2 and 8B V2
Use Cases: High-accuracy visual document retrieval, charts/tables/ screenshots, multimodal search
Better suited for difficult retrieval over dense pages, tables, charts, screenshots, layouts, infographics.

LLAMA NEMOTRON EMBED VL 1B V2
Use Cases: Lightweight multimodal RAG, PDF/image/text retrieval

NEMOTRON 3.5 CONTENT SAFETY (4B)
Use Cases: Multimodal content moderation, input/output safety checks, custom policy enforcement

#### resources
https://github.com/NVIDIA-NeMo/Nemotron/tree/main/use-case-examples/Simple%20Nemotron-3-Nano%20Usage%20Example

https://huggingface.co/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16
  - trained on : https://huggingface.co/datasets/nvidia/Nemotron-Image-Training-v3
- Local: https://huggingface.co/unsloth/NVIDIA-Nemotron-3-Nano-Omni-30B-A3B-Reasoning-GGUF 
  - video input doesn't work with llama.cpp!

### OpenBMB : cash
Use MiniCPM models. $5K for each track.

Eligible models:

MiniCPM5-1B — lightweight text/local 
-  agentic tool use, code generation, and difficult reasoning / coding workflows, function calling, tool usage, and analyzing long documents 
- https://huggingface.co/openbmb/MiniCPM5-1B-GGUF (1B)

MiniCPM-V 4.6 — image/OCR/multimodal 
- MLLM for Ultra-Efficient Image and Video Understanding on Your Phone 
- https://huggingface.co/openbmb/MiniCPM-V-4.6-gguf / https://huggingface.co/openbmb/MiniCPM-V-4.6-Thinking-gguf ?? (0.8B)

MiniCPM-o 4.5 — omni-modal
- MLLM for Vision, Speech, and Full-Duplex Mulitmodal Live Streaming on Your Phone
- https://huggingface.co/openbmb/MiniCPM-o-4_5-gguf
- seems to support MLX?

MiniCPM4.1-8B — reasoning 
- https://huggingface.co/openbmb/MiniCPM4.1-8B-GGUF

VoxCPM2 — voice/TTS

#### Free APls
API address:
MiniCPM4.1-8B: http://35.203.155.71:8001
MiniCPM-V-4.5: http://35.203.155.71:8002
MiniCPM-V-4.6: http://35.203.155.71:8003
MiniCPM-V-4.6-Thinking: http://35.203.155.71:8004
Authorization:
Bearer <set in local .env or HF Space secret>

Example usage:
```
export API_KEY='<set in local .env or HF Space secret>'
% curl http://35.203.155.71:8001/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniCPM4.1-8B",
    "messages": [
      {
        "role": "user",
        "content": "Hello"
      }
    ]
  }'
```

#### Deploy
vLLM
llama.cpp - needs GGUF format
Transformers


#### resources
Useful Resouces:
OpenBMB Model Collections: https://huggingface.co/openbmb/collections
OpenBMB GitHub : https://github.com/OpenBMB
OpenBMB X: https://x.com/OpenBMB
OpenBMB YouTube: https://www.youtube.com/channel/UCyDtv4OTmeZ1OYrCHymYGow


#### FYI, Agents
AgentCPM - AgentCPM-Explore / AgentCPM-Report / AgentCPM-GUI
UltraRAG - UltraRAG 3.0 / UltraRAG 2.1 / UltraRAG 2.0
ChatDev - ChatDev 2.0 / ChatDev

#### FYI, Tools
Evaluation - UltraEval-Audio v1.1, UltraEval-Audio
Training - BMTrain / BMinf / BMCook, OpenPrompt / OpenDelta
Data - UltraData-Math-LO-Parser , Ultra-FineWeb-L2-Selector



`#TODO` Cookbooks:
https://github.com/OpenSQZ/MiniCPM-V-CookBook
https://opensqz.github.io/MiniCPM-V-CookBook/site/en/index.html
https://github.com/OpenBMB/MiniCPM-V-Apps


### Black Forest Labs - common prize pool
#### resources
http://hf.co/blog/black-forest-labs/flux-2-klein-lora

Trainer: github.com/ostris/ai-toolkit

Fine-tune FLUX.2 [klein] with a LoRA under 60 minutes.
- https://huggingface.co/blog/black-forest-labs/flux-2-klein-lora
- The full loop: dataset → trainer → train → load in diffusers → Gradio Space.
- Covers both style LoRAs and edit LoRAs.
- ~1 hour on an RTX 4090, roughly $0.50 if you rent the

- They have hosted 4B distilled duplicate at https://huggingface.co/spaces/stephenbtl/klein-build-small-starter
- can duplicate Space if needed


### JetBrains - common prize pool

coding model - Mellum 2

#### resources
https://huggingface.co/collections/JetBrains/mellum2-gguf

https://huggingface.co/JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M

- Thinking model - reasoning with <think> complex debugging, multi-step planning, agentic workflows, and math- or reasoning-heavy tasks
- Instruct model - direct, low-latency answers without reasoning traces

Apache 2.0 license 


### Cohere - common prize pool

Cohore-transcribe - 2B - audio -> text multilingual / ASR model
- CohereLabs/cohere-transcribe-03-2026

tiny-aya - 3.3B - multilingual text generation, conversational Al, summarization, translation and cross-lingual tasks
- models: base, global, earth (West Asian, African), fire (South Asia) , water (European, Asia Pacific)
- collections/CohereLabs/tiny-aya



## finetuning
https://modal.com/docs/examples/unsloth_finetune

NVIDIA A100 (80GB): ~$0.000694 / sec (~$2.50 / hour)  NVIDIA H100: ~$0.001097 / sec (~$3.95 / hour)  
standard fine-tuning run (e.g., training on ~5,000 to 10,000 conversational examples), it typically takes about 2 to 4 hours on a single H100 or A100 80GB using Unsloth.
Total run cost: Roughly $5.00 to $15.00 total.
(Note: Modal doesn't charge for data egress or cold starts, so your compute time is strictly what you pay for).  


can fine-tune MoE models locally using Apple's MLX framework
64GB+ is highly recommended to load the 30B model in 4-bit quantization alongside the optimizer states.
Mac-native ecosystem uses mlx-lm and community tools like mlx-tune.
Prepare your dataset in a .jsonl file using standard ChatML format.
MLX has a built-in LoRA training script optimized for Apple's Metal backend.
Once training finishes, you fuse the new LoRA adapters back into a quantized base model:
https://gemini.google.com/u/6/app/c1ab575fc1f47788
