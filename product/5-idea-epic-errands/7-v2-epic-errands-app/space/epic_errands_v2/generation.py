from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import os
import time
from typing import Any

from .contracts import EditableTextLayer, GeneratedGoal, GeneratedMedia
from .fixtures import (
    ADD_ELEMENTS_BASE_THEME_IMAGES,
    ADD_ELEMENTS_PHASE1_VARIANTS,
    ADD_ELEMENTS_PHASE2_VARIANTS,
    ASSET_VARIANTS,
    DEFAULT_GENERATION_REFERENCE_IDS,
    SEEDED_UPLOADS,
    SEED_GOALS,
    THEMES,
)
from .runtime_metadata import LOCKED_GENERATION_MODES, QUALITY_MODE, quality_provenance


DEFAULT_DIY_REFERENCE_IDS = DEFAULT_GENERATION_REFERENCE_IDS


def build_app_bootstrap() -> dict[str, Any]:
    accepted = [
        build_generated_goal(
            seed["ordinary_goal"],
            seed["theme_id_at_creation"],
            seed["id"],
            selected_generation_reference_ids=seed.get("selected_generation_reference_ids", DEFAULT_GENERATION_REFERENCE_IDS),
            audio_used_parent_reference=bool(seed.get("audio_used_parent_reference", True)),
        )
        for seed in SEED_GOALS
    ]
    for goal, seed in zip(accepted, SEED_GOALS):
        goal["review_state"] = "accepted"
        goal["kid_completion_state"] = seed.get("kid_completion_state", "not_started")
        goal["parent_reward_state"] = seed.get("parent_reward_state", "not_reviewed")
    seeded_uploads = deepcopy(SEEDED_UPLOADS)
    parent_profile = {
        "display_name": "Parent",
        "photo_refs": seeded_uploads["parent_photo_refs"],
        "reference_audio_ref": seeded_uploads["parent_reference_audio_ref"],
        "reference_audio_optional": True,
    }
    children = [
        {
            "id": "child-1",
            "display_name": "Kid",
            "photo_refs": seeded_uploads["child_photo_refs"],
        }
    ]
    generation_references = [
        {
            "id": f"gen-{ref['id']}",
            "source": ref["kind"],
            "upload_ref_id": ref["id"],
            "selected": ref["id"] in DEFAULT_GENERATION_REFERENCE_IDS,
        }
        for ref in [*seeded_uploads["parent_photo_refs"], *seeded_uploads["child_photo_refs"]]
    ]
    return {
        "active_tab": "home",
        "active_theme_id": "questbook",
        "generation_mode": "quality",
        "available_generation_modes": LOCKED_GENERATION_MODES,
        "themes": THEMES,
        "parent_profile": parent_profile,
        "children": children,
        "custom_image_reference_refs": seeded_uploads["custom_image_reference_refs"],
        "uploads": seeded_uploads,
        "generation_references": generation_references,
        "goal_draft": {
            "ordinary_goal": "Finish my class project outline",
            "selected_generation_reference_ids": DEFAULT_GENERATION_REFERENCE_IDS,
            "generation_mode": "quality",
        },
        "pending_review_goal": None,
        "goals": accepted,
        "accepted_goals": accepted,
        "selected_goal_id": accepted[0]["id"],
        "diy": build_diy_state("questbook", accepted[0]["ordinary_goal"], DEFAULT_GENERATION_REFERENCE_IDS),
        "proof_boundary": "local deterministic fallback only; no hosted/model/judge-ready proof",
    }


def build_generated_goal(
    ordinary_goal: str,
    ui_theme_id: str = "questbook",
    seed_id: str | None = None,
    selected_generation_reference_ids: list[str] | None = None,
    *,
    audio_used_parent_reference: bool = False,
) -> dict[str, Any]:
    theme = _theme(ui_theme_id)
    goal_text = ordinary_goal.strip() or "Finish a helpful errand"
    asset_key = _asset_key(goal_text)
    selected_refs = selected_generation_reference_ids or []
    assets, image_provenance = _media_assets(asset_key, theme, selected_refs)
    reference_signature = ",".join(selected_refs)
    goal_id = seed_id or f"goal-{hashlib.sha1(f'{goal_text}:{reference_signature}'.encode('utf-8')).hexdigest()[:10]}"
    now = datetime.now(timezone.utc).isoformat()
    card = _card_copy(goal_text, theme)
    generated = GeneratedGoal(
        id=goal_id,
        ordinary_goal=goal_text,
        theme_id_at_creation=theme,
        selected_generation_reference_ids=selected_generation_reference_ids or [],
        generated_title=card["title"],
        generated_narration=card["narration"],
        generated_reward_label=card["reward_label"],
        overlay_text=EditableTextLayer(text=card["overlay"], theme_style_id=theme),
        media=GeneratedMedia(
            image_asset_ref=assets["image"],
            audio_asset_ref=assets["audio"],
            audio_used_parent_reference=audio_used_parent_reference,
        ),
        provenance={
            **quality_provenance(trace_id=f"local-v2-{asset_key}-{theme}-quality-media", fallback_used=True),
            **image_provenance,
        },
        created_at=now,
    )
    return {
        **generated.__dict__,
        "overlay_text": generated.overlay_text.__dict__,
        "media": generated.media.__dict__,
        "kid_completion_state": "not_started",
        "parent_reward_state": "not_reviewed",
        "updated_at": now,
    }


def build_generated_goal_with_live_fallback(
    ordinary_goal: str,
    ui_theme_id: str = "questbook",
    selected_generation_reference_ids: list[str] | None = None,
    *,
    audio_used_parent_reference: bool = False,
) -> dict[str, Any]:
    if not _live_generation_enabled():
        return build_generated_goal(
            ordinary_goal,
            ui_theme_id,
            selected_generation_reference_ids=selected_generation_reference_ids,
            audio_used_parent_reference=audio_used_parent_reference,
        )

    try:
        return _build_modal_generated_goal(
            ordinary_goal,
            ui_theme_id,
            selected_generation_reference_ids=selected_generation_reference_ids,
            audio_used_parent_reference=audio_used_parent_reference,
        )
    except Exception as exc:  # noqa: BLE001 - user-facing fallback keeps hosted app usable.
        fallback = build_generated_goal(
            ordinary_goal,
            ui_theme_id,
            selected_generation_reference_ids=selected_generation_reference_ids,
            audio_used_parent_reference=audio_used_parent_reference,
        )
        fallback["provenance"] = {
            **fallback.get("provenance", {}),
            "backend_transport": "modal_http",
            "fallback_reason": f"{exc.__class__.__name__}: {exc}",
            "fallback_used": True,
        }
        return fallback


def _build_modal_generated_goal(
    ordinary_goal: str,
    ui_theme_id: str,
    selected_generation_reference_ids: list[str] | None = None,
    *,
    audio_used_parent_reference: bool = False,
) -> dict[str, Any]:
    from diy_lab.epic_errands_diy_workflow.contracts import AudioRequest, ImageRequest, PlainGoalInput
    from diy_lab.epic_errands_diy_workflow.modal_client import ModalClient

    theme = _theme(ui_theme_id)
    goal_text = ordinary_goal.strip() or "Finish a helpful errand"
    reference_signature = ",".join(selected_generation_reference_ids or [])
    goal_id = f"goal-{hashlib.sha1(f'{goal_text}:{reference_signature}'.encode('utf-8')).hexdigest()[:10]}"
    started = time.monotonic()
    client = ModalClient()
    if client.config.dry_run:
        raise RuntimeError("Live generation is enabled, but Modal client is still in dry-run mode.")

    goal = PlainGoalInput(goal_id=goal_id, ordinary_goal=goal_text, theme=theme)
    text = client.generate_text(goal)
    card_text = {
        "title": text.title,
        "narration": text.narration,
        "reward_label": text.reward_label,
    }
    image = client.generate_image(
        ImageRequest(
            goal_id=goal_id,
            ordinary_goal=goal_text,
            theme=theme,
            card_text=card_text,
            prompt="",
            width=768,
            height=768,
            seed=26000 + len(goal_text),
        )
    )
    fallback_goal = build_generated_goal(
        goal_text,
        theme,
        seed_id=goal_id,
        selected_generation_reference_ids=selected_generation_reference_ids,
        audio_used_parent_reference=audio_used_parent_reference,
    )
    audio = None
    if _live_audio_enabled():
        audio = client.generate_audio(
            AudioRequest(
                goal_id=goal_id,
                ordinary_goal=goal_text,
                theme=theme,
                card_text=card_text,
                spoken_text=f"{text.title}. {text.narration}",
                audio_prompt="",
            )
        )

    if not image.artifact_uri.startswith("data:image/"):
        raise RuntimeError("Modal image response did not include image data.")
    if audio is not None and not audio.artifact_uri.startswith("data:audio/"):
        raise RuntimeError("Modal audio response did not include audio data.")

    now = datetime.now(timezone.utc).isoformat()
    runtime_steps = {
        "text": asdict(text.runtime_metadata),
        "image": asdict(image.runtime_metadata),
        "audio": asdict(audio.runtime_metadata)
        if audio is not None
        else {
            "lifecycle_stage": "testing",
            "app_host": "hf_space" if os.environ.get("SPACE_ID") else "local",
            "model_runtime": "none",
            "model_backend": "static_review_asset",
            "inference_engine": "none",
            "model_artifact_format": "none",
            "quantization": "none",
            "model_id": QUALITY_MODE["audio_model_id"],
            "latency_ms": 0,
            "fallback_used": True,
            "fallback_reason": "live_audio_disabled",
        },
    }
    fallback_used = any(bool(step.get("fallback_used")) for step in runtime_steps.values())
    generated = GeneratedGoal(
        id=goal_id,
        ordinary_goal=goal_text,
        theme_id_at_creation=theme,
        selected_generation_reference_ids=selected_generation_reference_ids or [],
        generated_title=text.title,
        generated_narration=text.narration,
        generated_reward_label=text.reward_label,
        overlay_text=EditableTextLayer(text=goal_text, theme_style_id=theme),
        media=GeneratedMedia(
            image_asset_ref=image.artifact_uri,
            audio_asset_ref=audio.artifact_uri if audio is not None else fallback_goal["media"]["audio_asset_ref"],
            audio_used_parent_reference=audio_used_parent_reference,
        ),
        provenance={
            **quality_provenance(trace_id=f"hosted-v2-modal-{goal_id}", fallback_used=fallback_used),
            "app_host": "hf_space" if os.environ.get("SPACE_ID") else "local",
            "model_runtime": "modal",
            "model_backend": "modal_http",
            "backend_transport": "modal_http",
            "api_name": "epic_generate_goal",
            "latency_ms": round((time.monotonic() - started) * 1000),
            "modal_runtime_steps": runtime_steps,
        },
        created_at=now,
    )
    return {
        **generated.__dict__,
        "overlay_text": generated.overlay_text.__dict__,
        "media": generated.media.__dict__,
        "kid_completion_state": "not_started",
        "parent_reward_state": "not_reviewed",
        "updated_at": now,
    }


def build_diy_state(
    theme_id: str,
    ordinary_goal: str,
    selected_generation_reference_ids: list[str] | None = None,
) -> dict[str, Any]:
    theme = _theme(theme_id)
    selected_refs = selected_generation_reference_ids or DEFAULT_DIY_REFERENCE_IDS
    preview = build_generated_goal(ordinary_goal, theme, selected_generation_reference_ids=selected_refs)
    trace = {
        "pipeline": ["plain_goal", "text_step", "image_step", "audio_step", "composed_card"],
        "plain_goal": ordinary_goal,
        "selected_theme_id": theme,
        "selected_generation_reference_ids": selected_refs,
        "generation_mode": "quality",
        "text_step": {"model": QUALITY_MODE["text_model_id"], "runtime": QUALITY_MODE["text_runtime"], "fallback_used": True},
        "image_step": {
            "model": QUALITY_MODE["image_model_id"],
            "runtime": QUALITY_MODE["image_runtime"],
            "output_size_px": QUALITY_MODE["image_output_size_px"],
            "result_asset_ref": preview["media"]["image_asset_ref"],
            "image_fallback_source": preview["provenance"].get("image_fallback_source"),
            "add_elements_cache_hit": preview["provenance"].get("add_elements_cache_hit"),
            "add_elements_contract": preview["provenance"].get("add_elements_contract"),
            "base_theme_image_ref": preview["provenance"].get("base_theme_image_ref"),
        },
        "audio_step": {
            "model": QUALITY_MODE["audio_model_id"],
            "runtime": QUALITY_MODE["audio_runtime"],
            "result_asset_ref": preview["media"]["audio_asset_ref"],
        },
        "composed_card_step": {"overlay_text": preview["overlay_text"]["text"], "mutates_image_pixels": False},
        "quality_mode": QUALITY_MODE,
        "fallback_used": True,
        "save_to_app_status": "coming_soon",
    }
    return {
        "isolated_surface": True,
        "workflow_draft": {
            "ordinary_goal": ordinary_goal,
            "selected_theme_id": theme,
            "selected_generation_reference_ids": selected_refs,
            "text_step": {"model": QUALITY_MODE["text_model_id"], "runtime": QUALITY_MODE["text_runtime"]},
            "image_step": {"model": QUALITY_MODE["image_model_id"], "output_size_px": QUALITY_MODE["image_output_size_px"]},
            "audio_step": {"model": QUALITY_MODE["audio_model_id"], "runtime": QUALITY_MODE["audio_runtime"]},
            "composed_card_step": {"overlay_text": preview["overlay_text"]["text"]},
        },
        "preview": preview,
        "trace_json": trace,
        "save_to_app_status": "coming_soon",
    }


def _live_generation_enabled() -> bool:
    return (
        os.environ.get("EPIC_ENABLE_LIVE_GENERATION", "").strip().lower() in {"1", "true", "yes"}
        or os.environ.get("APP_DRY_RUN", "true").strip().lower() in {"0", "false", "no"}
    )


def _live_audio_enabled() -> bool:
    return os.environ.get("EPIC_ENABLE_LIVE_AUDIO", "").strip().lower() in {"1", "true", "yes"}


def _theme(value: str) -> str:
    return {"magical": "questbook"}.get(str(value or "questbook").lower(), str(value or "questbook").lower()) if str(value or "").lower() in THEMES or str(value or "").lower() == "magical" else "questbook"


def _asset_key(goal_text: str) -> str:
    lowered = goal_text.lower()
    if "read" in lowered:
        return "read-20"
    if "project" in lowered or "outline" in lowered:
        return "project-outline"
    return "clean-room"


def _media_assets(asset_key: str, theme: str, selected_reference_ids: list[str]) -> tuple[dict[str, str], dict[str, Any]]:
    media = dict(ASSET_VARIANTS[asset_key].get(theme, ASSET_VARIANTS[asset_key]["questbook"]))
    provenance: dict[str, Any] = {
        "image_fallback_source": "generated_v2_fixture",
        "add_elements_cache_hit": False,
        "add_elements_contract": "not_applied",
        "base_theme_image_ref": ADD_ELEMENTS_BASE_THEME_IMAGES.get(theme),
    }
    has_people_refs = _has_parent_child_refs(selected_reference_ids)
    if has_people_refs:
        variant = ADD_ELEMENTS_PHASE2_VARIANTS.get(asset_key, {}).get(theme)
        if variant:
            media["image"] = variant["image"]
            provenance.update(
                {
                    "image_fallback_source": "cached_flux2_add_elements_phase2",
                    "add_elements_cache_hit": True,
                    "add_elements_phase": "phase2",
                    "add_elements_contract": "base_theme_plus_parent_child_goal",
                    "add_elements_source_goal": variant["source_goal"],
                    "add_elements_reference_ids": [
                        variant["parent_reference_id"],
                        variant["child_reference_id"],
                    ],
                }
            )
        else:
            provenance.update(
                {
                    "add_elements_contract": "base_theme_plus_parent_child_goal",
                    "add_elements_cache_miss_reason": "no_exact_cached_phase2_theme_goal_match",
                }
            )
        return media, provenance

    if not selected_reference_ids:
        variant = ADD_ELEMENTS_PHASE1_VARIANTS.get(asset_key, {}).get(theme)
        if variant:
            media["image"] = variant["image"]
            provenance.update(
                {
                    "image_fallback_source": "cached_flux2_add_elements_phase1",
                    "add_elements_cache_hit": True,
                    "add_elements_phase": "phase1",
                    "add_elements_contract": "base_theme_plus_goal_no_people",
                    "add_elements_source_goal": variant["source_goal"],
                }
            )
    return media, provenance


def _has_parent_child_refs(selected_reference_ids: list[str]) -> bool:
    kinds = {_reference_kind(ref_id) for ref_id in selected_reference_ids}
    return "parent_photo" in kinds and "child_photo" in kinds


def _reference_kind(ref_id: str) -> str:
    lowered = str(ref_id or "").lower()
    if any(token in lowered for token in ("parent", "dad", "mom")):
        return "parent_photo"
    if any(token in lowered for token in ("child", "kid", "boy", "girl")):
        return "child_photo"
    return "custom_image_reference"


def _card_copy(goal_text: str, theme: str) -> dict[str, str]:
    if theme == "comic":
        return {
            "title": "Mission: Everyday Hero",
            "narration": f"Zoom in on the next win: {goal_text}. Finish it, then call in your victory.",
            "reward_label": "Starburst",
            "overlay": goal_text,
        }
    if theme == "classroom":
        return {
            "title": "Quest: Ready to Shine",
            "narration": f"Take one clear school-day step and finish: {goal_text}.",
            "reward_label": "Badge",
            "overlay": goal_text,
        }
    return {
        "title": "Quest: Small Brave Step",
        "narration": f"The questbook opens to today's errand: {goal_text}.",
        "reward_label": "Crest",
        "overlay": goal_text,
    }
