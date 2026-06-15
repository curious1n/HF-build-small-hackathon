from __future__ import annotations

from epic_errands_v2.generation import build_diy_state


def preview_workflow(ordinary_goal: str = "Clean up my room before dinner", theme_id: str = "questbook") -> dict[str, object]:
    return build_diy_state(theme_id, ordinary_goal)


if __name__ == "__main__":
    import json

    print(json.dumps(preview_workflow(), indent=2))
