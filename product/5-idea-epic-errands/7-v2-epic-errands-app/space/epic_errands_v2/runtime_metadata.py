from __future__ import annotations

from typing import Any


QUALITY_MODE: dict[str, Any] = {
    "id": "quality",
    "label": "Quality",
    "status": "enabled",
    "text_model_id": "nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF",
    "text_runtime": "llama.cpp",
    "text_format": "GGUF",
    "text_quantization": "Q4_K_M",
    "image_model_id": "black-forest-labs/FLUX.2-klein-9B",
    "image_runtime": "Diffusers",
    "image_format": "safetensors",
    "image_precision": "bf16",
    "image_output_size_px": 1024,
    "audio_model_id": "openbmb/VoxCPM2",
    "audio_runtime": "voxcpm",
    "audio_format": "safetensors",
    "audio_precision": "bf16",
    "visible_to_user": True,
}

SPEED_MODE: dict[str, Any] = {
    "id": "speed",
    "label": "Speed",
    "status": "disabled_planned",
    "text_model_id": "nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF",
    "text_runtime": "llama.cpp",
    "text_format": "GGUF",
    "text_quantization": "Q4_K_M",
    "image_model_id": "black-forest-labs/FLUX.2-klein-4B",
    "image_runtime": "Diffusers",
    "image_format": "safetensors",
    "image_precision": "bf16",
    "image_output_size_px": 720,
    "audio_model_id": "openbmb/VoxCPM2",
    "audio_runtime": "voxcpm",
    "audio_format": "safetensors",
    "audio_precision": "bf16",
    "visible_to_user": True,
}

LOCKED_GENERATION_MODES = [QUALITY_MODE, SPEED_MODE]


def quality_provenance(*, trace_id: str | None = None, fallback_used: bool | None = True) -> dict[str, Any]:
    return {
        "text_model_id": QUALITY_MODE["text_model_id"],
        "text_runtime": QUALITY_MODE["text_runtime"],
        "text_format": QUALITY_MODE["text_format"],
        "text_quantization": QUALITY_MODE["text_quantization"],
        "image_model_id": QUALITY_MODE["image_model_id"],
        "image_runtime": QUALITY_MODE["image_runtime"],
        "image_format": QUALITY_MODE["image_format"],
        "image_precision": QUALITY_MODE["image_precision"],
        "audio_model_id": QUALITY_MODE["audio_model_id"],
        "audio_runtime": QUALITY_MODE["audio_runtime"],
        "audio_format": QUALITY_MODE["audio_format"],
        "audio_precision": QUALITY_MODE["audio_precision"],
        "fallback_used": fallback_used,
        "trace_id": trace_id,
    }
