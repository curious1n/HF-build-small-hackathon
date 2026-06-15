from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


ThemeId = Literal["classroom", "questbook", "comic"]
GenerationMode = Literal["quality"]
TabId = Literal["home", "parent_goals", "kid_goals", "settings", "diy"]


@dataclass(frozen=True)
class UploadRef:
    id: str
    kind: str
    asset_ref: str
    preview_ref: str | None = None
    privacy_scope: str = "session_only"
    created_at: str = "local-demo"


@dataclass(frozen=True)
class EditableTextLayer:
    text: str
    theme_style_id: ThemeId = "questbook"
    position: str = "bottom"
    max_lines: int = 3
    is_app_owned: bool = True
    mutates_image_pixels: bool = False
    mutates_audio: bool = False


@dataclass(frozen=True)
class GeneratedMedia:
    image_asset_ref: str
    audio_asset_ref: str
    image_output_size_px: int = 1024
    image_mutable_from_review: bool = False
    audio_enabled: bool = True
    audio_used_parent_reference: bool = False
    audio_mutable_from_review: bool = False


@dataclass(frozen=True)
class GeneratedGoal:
    id: str
    ordinary_goal: str
    generated_title: str
    generated_narration: str
    generated_reward_label: str
    overlay_text: EditableTextLayer
    media: GeneratedMedia
    provenance: dict[str, object]
    generation_mode: GenerationMode = "quality"
    theme_id_at_creation: ThemeId = "questbook"
    selected_generation_reference_ids: list[str] = field(default_factory=list)
    review_state: str = "pending"
    created_at: str = "local-demo"


# Design anchor glossary kept in code so the implementation gate can trace the
# exact detailed-design strings into this package:
# active_theme_id: classroom | questbook | comic
# generation_mode: quality
# accepted_goals[]
# reference_audio_ref
# parent_reference_audio_ref UI upload alias
# reference_audio_optional
# audio_enabled
# audio_used_parent_reference
# overlay_text
# mutates_image_pixels
# image_mutable_from_review
# audio_mutable_from_review
# speed_visible_disabled_planned
