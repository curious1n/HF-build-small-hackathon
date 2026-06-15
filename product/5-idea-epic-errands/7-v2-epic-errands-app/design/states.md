# Epic Errands V2 States

Status: state contract for fast implementation. This file does not claim the
states are implemented or browser-tested.

## Global App States

| State | Meaning | Design obligation |
| --- | --- | --- |
| `first_run` | No uploads or created goals yet. | Home and Settings show clear setup affordances. |
| `theme_selected` | Classroom, Questbook, or Comic is active. | App shell, copy tone, and overlay style update without changing accepted media. |
| `settings_ready` | Parent/child details and generation refs are sufficient for a run. | Parent Goals can start Quality generation. |
| `quality_selected` | Quality mode selected and enabled. | Show 1024 x 1024 image policy and compact provenance. |
| `speed_planned_disabled` | Speed mode visible but unavailable. | Keep disabled state and planned 720 x 720 label. |
| `has_pending_review` | Generated goal is awaiting parent Accept/Cancel. | Review Goal is reachable and blocks kid publication. |
| `has_active_goals` | One or more accepted goals are visible to kid. | Home and Kid Goals counts update. |
| `has_awaiting_approval` | Kid completed one or more goals. | Home and Parent Goals surface the awaiting count. |

## Navigation States

| Component | States |
| --- | --- |
| Home tab | `selected`, `idle`, `focus_visible` |
| Parent Goals tab | `selected`, `idle`, `badge_pending_review`, `badge_awaiting_approval`, `focus_visible` |
| Kid Goals tab | `selected`, `idle`, `badge_active_goals`, `focus_visible` |
| Settings tab | `selected`, `idle`, `needs_details`, `ready`, `focus_visible` |
| DIY tab | `selected`, `idle`, `opens_isolated_surface`, `focus_visible` |

## Settings States

| Component | States |
| --- | --- |
| App theme picker | `classroom_selected`, `questbook_selected`, `comic_selected` |
| Parent photos | `empty`, `uploaded`, `preview_visible`, `remove_ready`, `upload_error` |
| Parent reference audio | `empty_optional`, `uploaded`, `preview_ready`, `remove_ready`, `upload_error` |
| Child photos | `empty`, `uploaded`, `preview_visible`, `remove_ready`, `upload_error` |
| Generation reference picker | `none_selected`, `parent_photo_selected`, `child_photo_selected`, `custom_image_selected`, `missing_reference_warning` |
| Quality mode | `selected`, `enabled`, `image_1024_label_visible` |
| Speed mode | `disabled`, `planned`, `image_720_label_visible` |

Audio is always enabled. If parent reference audio is missing, generation still
uses the configured default voice behavior.

## Parent Goals States

| Component | States |
| --- | --- |
| Goal draft input | `empty`, `draft_ready`, `invalid_empty`, `editing` |
| Reference selector | `uses_parent_photo`, `uses_child_photo`, `uses_custom_image`, `needs_reference` |
| Generate action | `disabled_until_ready`, `ready_quality`, `generating_text`, `generating_image`, `generating_audio`, `generation_error`, `review_ready` |
| Parent goal list | `empty`, `has_goals`, `awaiting_kid`, `kid_completed`, `awaiting_approval`, `approved_reward_given` |
| Parent approval action | `disabled_until_kid_complete`, `ready`, `approving`, `approved` |

## Review Goal States

| Component | States |
| --- | --- |
| Generated image frame | `loading`, `ready`, `error_fallback`, `immutable` |
| Editable text overlay | `ready`, `focused`, `editing`, `saved_to_app_state`, `wraps_on_mobile`, `contrast_guard_visible` |
| Generated title/narration/reward | `ready`, `local_fallback_copy`, `copy_error` |
| Audio preview | `loading`, `ready`, `playing`, `failed`, `immutable` |
| Provenance summary | `collapsed`, `expanded`, `quality_mode_visible`, `fallback_label_visible_when_applicable` |
| Accept action | `ready`, `accepting`, `accepted_published_to_kid_goals` |
| Cancel action | `ready`, `canceling`, `canceled_discarded` |

Locked Review Goal constraints:

- Accept publishes the goal to Kid Goals.
- Cancel discards the generated goal and returns to Parent Goals.
- Image cannot be changed from Review Goal.
- Audio cannot be changed from Review Goal.
- Text overlay edits update app-owned text only.

## Kid Goals States

| Component | States |
| --- | --- |
| Thumbnail grid | `empty`, `has_goals`, `thumbnail_only`, `opens_goal_card`, `completed`, `awaiting_approval`, `reward_given` |
| Kid goal card | `closed`, `open`, `image_ready`, `overlay_text_ready`, `audio_ready`, `kid_can_complete`, `kid_completed`, `waiting_for_parent`, `reward_given` |
| Audio player | `ready`, `playing`, `failed` |
| Completion action | `ready`, `completed`, `waiting_for_parent`, `reward_given` |

Kid-facing goal cards must not show prompt text, raw JSON, arbitrary model IDs,
generated steps, or completion-check fields.

## DIY States

| Component | States |
| --- | --- |
| DIY shell | `isolated_loaded`, `inherits_theme`, `main_app_state_readonly` |
| Workflow draft editor | `hardcoded_draft_loaded`, `editing`, `local_preview_dirty`, `local_preview_updated` |
| Flow steps | `plain_goal`, `text_step`, `image_step`, `audio_step`, `composed_card`, `trace_visible` |
| Model details | `quality_text_visible`, `quality_image_visible`, `audio_visible`, `fallback_label_visible_when_applicable` |
| Save to app | `coming_soon_disabled`, `focus_visible` |

DIY edits stay inside DIY until save-back-to-main-app exists.

## Future Verification Seeds

- At 390px and 360px, tab labels and disabled/planned labels remain readable.
- Theme changes update app shell and overlay style, not accepted image/audio.
- Speed mode is visible and disabled.
- Audio generation remains enabled when parent reference audio is absent.
- Review Goal exposes Accept and Cancel only.
- Review Goal has no image-edit or audio-edit affordance.
- Accepted goals appear in Kid Goals; canceled goals do not.
- DIY opens as isolated surface and labels save-back as coming soon.
