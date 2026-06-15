from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any

from .contracts import EditableTextLayer, GeneratedGoal, GeneratedMedia
from .fixtures import ASSET_VARIANTS, SEED_GOALS, THEMES
from .runtime_metadata import LOCKED_GENERATION_MODES, QUALITY_MODE, quality_provenance


QUALITY_MEDIA_VARIANT_ID = "questbook"
DEFAULT_DIY_REFERENCE_IDS = ["parent-photo-demo", "child-photo-demo", "custom-image-reference-demo"]


def build_app_bootstrap() -> dict[str, Any]:
    accepted = [build_generated_goal(seed["ordinary_goal"], seed["theme_id_at_creation"], seed["id"]) for seed in SEED_GOALS]
    accepted[0]["review_state"] = "accepted"
    accepted[0]["kid_completion_state"] = "not_started"
    accepted[0]["parent_reward_state"] = "not_reviewed"
    parent_profile = {
        "display_name": "Parent",
        "photo_refs": [],
        "reference_audio_ref": None,
        "reference_audio_optional": True,
    }
    return {
        "active_tab": "home",
        "active_theme_id": "questbook",
        "generation_mode": "quality",
        "available_generation_modes": LOCKED_GENERATION_MODES,
        "themes": THEMES,
        "parent_profile": parent_profile,
        "children": [{"id": "child-1", "display_name": "Kid", "photo_refs": []}],
        "custom_image_reference_refs": [],
        "generation_references": [],
        "goal_draft": {
            "ordinary_goal": "Read for 20 minutes",
            "selected_generation_reference_ids": [],
            "generation_mode": "quality",
        },
        "pending_review_goal": None,
        "goals": accepted,
        "accepted_goals": accepted,
        "selected_goal_id": accepted[0]["id"],
        "diy": build_diy_state("questbook", "Clean up my room before dinner"),
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
    assets = ASSET_VARIANTS[asset_key][QUALITY_MEDIA_VARIANT_ID]
    reference_signature = ",".join(selected_generation_reference_ids or [])
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
        provenance=quality_provenance(trace_id=f"local-v2-{asset_key}-quality-media", fallback_used=True),
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


def _theme(value: str) -> str:
    return {"magical": "questbook"}.get(str(value or "questbook").lower(), str(value or "questbook").lower()) if str(value or "").lower() in THEMES or str(value or "").lower() == "magical" else "questbook"


def _asset_key(goal_text: str) -> str:
    lowered = goal_text.lower()
    if "read" in lowered:
        return "read-20"
    if "project" in lowered or "outline" in lowered:
        return "project-outline"
    return "clean-room"


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
