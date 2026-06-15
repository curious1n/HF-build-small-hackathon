from __future__ import annotations

from typing import Any


THEMES: dict[str, dict[str, str]] = {
    "classroom": {
        "label": "Classroom",
        "token": "storybook",
        "goal_noun": "Quest",
        "parent_title": "Classroom Captain",
        "kid_title": "Star Student",
        "reward_noun": "Badge",
        "waiting_copy": "Waiting for Classroom Captain approval.",
    },
    "questbook": {
        "label": "Questbook",
        "token": "atelier",
        "goal_noun": "Quest",
        "parent_title": "Quest Keeper",
        "kid_title": "Young Adventurer",
        "reward_noun": "Crest",
        "waiting_copy": "Waiting for Quest Keeper approval.",
    },
    "comic": {
        "label": "Comic",
        "token": "comic",
        "goal_noun": "Mission",
        "parent_title": "Comic Editor",
        "kid_title": "Panel Hero",
        "reward_noun": "Starburst",
        "waiting_copy": "Waiting for Comic Editor approval.",
    },
}

ASSET_VARIANTS: dict[str, dict[str, dict[str, str]]] = {
    "clean-room": {
        "questbook": {
            "image": "generated-v2/clean-room-questbook-d35e6ee10c.png",
            "audio": "generated-v2/clean-room-questbook-01493f395c.wav",
        },
        "classroom": {
            "image": "generated-v2/clean-room-classroom-c5cb506427.png",
            "audio": "generated-v2/clean-room-classroom-cf6f43d6ce.wav",
        },
        "comic": {
            "image": "generated-v2/clean-room-comic-9bce2b2b21.png",
            "audio": "generated-v2/clean-room-comic-88b770a8dc.wav",
        },
    },
    "project-outline": {
        "questbook": {
            "image": "generated-v2/project-outline-questbook-e1d5ced2e8.png",
            "audio": "generated-v2/project-outline-questbook-bddf03af1a.wav",
        },
        "classroom": {
            "image": "generated-v2/project-outline-classroom-3783f10bae.png",
            "audio": "generated-v2/project-outline-classroom-70a886be5a.wav",
        },
        "comic": {
            "image": "generated-v2/project-outline-comic-4f9eaa443a.png",
            "audio": "generated-v2/project-outline-comic-ef3f180846.wav",
        },
    },
    "read-20": {
        "questbook": {
            "image": "generated-v2/read-20-questbook-39aac8ba25.png",
            "audio": "generated-v2/read-20-questbook-5805518930.wav",
        },
        "classroom": {
            "image": "generated-v2/read-20-classroom-7c13f43782.png",
            "audio": "generated-v2/read-20-classroom-cca67b8288.wav",
        },
        "comic": {
            "image": "generated-v2/read-20-comic-b5ae2d561a.png",
            "audio": "generated-v2/read-20-comic-7ec8c91bf8.wav",
        },
    },
}

ADD_ELEMENTS_BASE_THEME_IMAGES: dict[str, str] = {
    "classroom": "base-theme-images/classroom-base-theme-1024.png",
    "questbook": "base-theme-images/questbook-base-theme-1024.png",
    "comic": "base-theme-images/comic-base-theme-1024.png",
}

ADD_ELEMENTS_PHASE1_VARIANTS: dict[str, dict[str, dict[str, str]]] = {
    "clean-room": {
        "classroom": {
            "image": "add-elements/phase1-classroom.png",
            "source_goal": "Clean up my room before dinner",
        },
    },
    "project-outline": {
        "questbook": {
            "image": "add-elements/phase1-questbook.png",
            "source_goal": "Finish my class project outline",
        },
    },
    "read-20": {
        "comic": {
            "image": "add-elements/phase1-comic.png",
            "source_goal": "Read for 20 minutes",
        },
    },
}

ADD_ELEMENTS_PHASE2_VARIANTS: dict[str, dict[str, dict[str, str]]] = {
    "clean-room": {
        "classroom": {
            "image": "add-elements/phase2-classroom.png",
            "source_goal": "Clean up my room before dinner",
            "parent_reference_id": "parent-mom-demo",
            "child_reference_id": "child-boy-demo",
        },
    },
    "project-outline": {
        "questbook": {
            "image": "add-elements/phase2-questbook.png",
            "source_goal": "Finish my class project outline",
            "parent_reference_id": "parent-dad-demo",
            "child_reference_id": "child-girl-demo",
        },
    },
    "read-20": {
        "comic": {
            "image": "add-elements/phase2-comic.png",
            "source_goal": "Read for 20 minutes",
            "parent_reference_id": "parent-dad-demo",
            "child_reference_id": "child-boy-demo",
        },
    },
}

SEEDED_UPLOADS: dict[str, Any] = {
    "parent_photo_refs": [
        {
            "id": "parent-dad-demo",
            "kind": "parent_photo",
            "asset_ref": "Dad reference portrait",
            "preview_ref": "reference-seeds/parent-reference-photo.png",
            "privacy_scope": "session_only",
            "created_at": "local-demo",
        },
        {
            "id": "parent-mom-demo",
            "kind": "parent_photo",
            "asset_ref": "Mom reference portrait",
            "preview_ref": "reference-seeds/placeholder-female-parent-720.png",
            "privacy_scope": "session_only",
            "created_at": "local-demo",
        }
    ],
    "child_photo_refs": [
        {
            "id": "child-boy-demo",
            "kind": "child_photo",
            "asset_ref": "Boy reference portrait",
            "preview_ref": "reference-seeds/kid-reference-photo.png",
            "privacy_scope": "session_only",
            "created_at": "local-demo",
        },
        {
            "id": "child-girl-demo",
            "kind": "child_photo",
            "asset_ref": "Girl reference portrait",
            "preview_ref": "reference-seeds/placeholder-girl-720.png",
            "privacy_scope": "session_only",
            "created_at": "local-demo",
        }
    ],
    "custom_image_reference_refs": [],
    "parent_reference_audio_ref": {
        "id": "parent-audio-demo",
        "kind": "parent_reference_audio",
        "asset_ref": "Parent reference audio sample",
        "preview_ref": "reference-seeds/parent-reference-audio.m4a",
        "privacy_scope": "session_only",
        "created_at": "local-demo",
    },
}

DEFAULT_GENERATION_REFERENCE_IDS = ["parent-dad-demo", "child-girl-demo"]

SEED_GOALS: list[dict[str, Any]] = [
    {
        "id": "goal-seed-project-outline",
        "asset_key": "clean-room",
        "ordinary_goal": "Finish my class project outline",
        "theme_id_at_creation": "questbook",
        "generated_title": "Quest: Project Outline",
        "generated_narration": "A clear outline turns a big class project into a brave first step.",
        "generated_reward_label": "Planning Crest",
    },
]
