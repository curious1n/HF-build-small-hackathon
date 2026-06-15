# agent roster

COAGENTS tracks active human/AI coordination for this project. Keep detailed
workflow rules, proof recipes, and idea history in the workflow docs or idea
folders instead of repeating them here.

| Agent | Type | Role |
| - | - | - |
| @cu | Human | Hackathon participant, product owner, and approval gate for public release, paid runs, credit-spending actions, reopening parked scope, and final submission decisions. |
| Codex | AI agent | Coding, product, design, runtime, HF Space, Modal, and evidence collaborator operating under repo and workflow constraints. |

# approval gates and hard responsibilities

| Area | Gate |
| - | - |
| Workflow scope | Codex declares active workflow lanes, prompt cards, excluded lanes, and proof claim before substantial work in new or resumed threads. Source: `product/HACKATHON_PRODUCT_WORKFLOW.md`. |
| Public release or final submission | Requires explicit @cu approval. |
| GitHub open repo upload | Use `product/workflow/GITHUB_OPEN_REPO_UPLOAD.md`. Codex selects the exact files from active ideas plus root agent docs and writes the exact `rsync` command for `z-github-repo-consolidation/`; @cu must review and explicitly approve that command before Codex runs the copy. Repo creation, commits, pushes, or visibility changes require separate explicit @cu approval unless named in the same approval. |
| Paid runtime or credit spend | Requires explicit @cu approval, budget, max duration, and stop condition. No paid GPU, paid Space hardware, warm pool, always-on runtime, or credit spend by default. |
| Gated Hugging Face models | Before paid GPU, Modal, ZeroGPU, or paid Space work, Codex runs a token-backed no-GPU check against an actual required model file such as `model_index.json`; if blocked, @cu must accept/ungate terms before retry. |
| Model/sponsor claims | Deterministic fallback is allowed, but it is not sponsor/model proof. Real model proof must identify runtime axes and `fallback_used=false`, or record a blocker. |

# standing bounded approvals

These approvals count as explicit @cu approval only when the current run matches
the listed scope exactly. Codex should cite the matching approval and proceed
without asking again. If any scope, budget, duration, hardware, product, or stop
condition changes, ask @cu before spending.

| Scope | Standing approval |
| - | - |

# active non-parked surfaces

These are the only product surfaces COAGENTS should steer future work toward
unless @cu explicitly changes priorities.

| Work | Path | Status | Next coordination decision |
| - | - | - | - |
| Voice Contact Widget | `product/5-idea-voice-contact-widget/v1` | Active candidate | - |
| Epic Errands | `product/5-idea-epic-errands/7-v2-epic-errands-app` | Active candidate | - |
| Venue Manager v2 | `product/5-idea-venue-manager/3-v2-venue-manager` | Active candidate | Use this clean folder for Venue Manager work. Old `2-sport-agnostic-venue-agent` remains provenance and should not be edited unless @cu explicitly asks. |

# parked scope

| Scope | Rule |
| - | - |
| `product/2-idea-*` | Parked. Do not resume or prioritize any `product/2-idea-*` folder, including Small Model Agent Arcade, unless @cu explicitly reopens it. |
| Older retros | Use `product/5-mid-way-retro-2` and `product/workflow/THREAD_LEARNING_LEDGER.md` for current process learning. Treat `product/3-mid-way-retro` as historical evidence only. |

# current cross-project decisions

| Priority | Decision | How to proceed |
| - | - | - |
