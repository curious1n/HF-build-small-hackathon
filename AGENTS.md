This project is for Huggingface (HF) Build Small Hackathon - https://huggingface.co/spaces/build-small-hackathon/.

Read COAGENTS.md for responsibilities and tasks shared between Codex (AI agent) and @cu (Human).
Read TRIBAL.md for tribal knowledge.

Refer product/HACKATHON_PRODUCT_WORKFLOW.md for the product/design/tech workflow dispatcher.

For any meaningful new thread, goal, resumed goal, or multi-step task, Codex must identify the workflow lanes and prompt cards it is taking and tell @cu before substantial work starts. Point to lane files under product/workflow/ and prompt cards under product/workflow/prompts/, state what proof will and will not be claimed, and update the declaration if scope expands.

Use product/workflow/LANE_ROUTER.md or `python3 scripts/workflow_lane_router.py --task "<task>"` for deterministic lane suggestions. Default to product/workflow/FEATURE_FIRST.md for narrow V0 feature builds, bug fixes, UI parity fixes, and small runtime bring-up passes.
