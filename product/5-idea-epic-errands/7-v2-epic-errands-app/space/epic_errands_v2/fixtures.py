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

SEED_GOALS: list[dict[str, Any]] = [
    {
        "id": "goal-seed-clean-room",
        "asset_key": "clean-room",
        "ordinary_goal": "Clean up my room before dinner",
        "theme_id_at_creation": "questbook",
        "generated_title": "Quest: Room Cleanup",
        "generated_narration": "A tidy room is the first little victory before dinner.",
        "generated_reward_label": "Dinner-time Crest",
    },
]
