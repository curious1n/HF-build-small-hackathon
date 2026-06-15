(function () {
  if (window.__EPIC_ERRANDS_V2_APP_STARTED__) return;
  window.__EPIC_ERRANDS_V2_APP_STARTED__ = true;

  const ASSET_BASE = window.EPIC_ASSET_BASE || "assets/";
  const ASSET_MANIFEST = window.EPIC_ASSET_MANIFEST || {};
  const API_BASE = window.EPIC_API_BASE || "";
  const EMBEDDED_SPACE_MODE = Boolean(window.EPIC_EMBEDDED_SPACE_MODE);
  const GRADIO_API_PREFIX = window.EPIC_GRADIO_API_PREFIX || "/gradio_api";
  const root = document.getElementById("app");

  const themeToToken = {
    classroom: "storybook",
    questbook: "atelier",
    comic: "comic",
  };

  const themes = {
    classroom: {
      label: "Classroom",
      token: "storybook",
      parentTitle: "Classroom Captain",
      kidTitle: "Star Student",
      goalNoun: "Quest",
      rewardNoun: "Badge",
      waitingCopy: "Waiting for Classroom Captain approval.",
    },
    questbook: {
      label: "Questbook",
      token: "atelier",
      parentTitle: "Quest Keeper",
      kidTitle: "Young Adventurer",
      goalNoun: "Quest",
      rewardNoun: "Crest",
      waitingCopy: "Waiting for Quest Keeper approval.",
    },
    comic: {
      label: "Comic",
      token: "comic",
      parentTitle: "Comic Editor",
      kidTitle: "Panel Hero",
      goalNoun: "Mission",
      rewardNoun: "Starburst",
      waitingCopy: "Waiting for Comic Editor approval.",
    },
  };

  const assets = {
    "clean-room": {
      questbook: {
        image: "generated-v2/clean-room-questbook-d35e6ee10c.png",
        audio: "generated-v2/clean-room-questbook-01493f395c.wav",
      },
      classroom: {
        image: "generated-v2/clean-room-classroom-c5cb506427.png",
        audio: "generated-v2/clean-room-classroom-cf6f43d6ce.wav",
      },
      comic: {
        image: "generated-v2/clean-room-comic-9bce2b2b21.png",
        audio: "generated-v2/clean-room-comic-88b770a8dc.wav",
      },
    },
    "project-outline": {
      questbook: {
        image: "generated-v2/project-outline-questbook-e1d5ced2e8.png",
        audio: "generated-v2/project-outline-questbook-bddf03af1a.wav",
      },
      classroom: {
        image: "generated-v2/project-outline-classroom-3783f10bae.png",
        audio: "generated-v2/project-outline-classroom-70a886be5a.wav",
      },
      comic: {
        image: "generated-v2/project-outline-comic-4f9eaa443a.png",
        audio: "generated-v2/project-outline-comic-ef3f180846.wav",
      },
    },
    "read-20": {
      questbook: {
        image: "generated-v2/read-20-questbook-39aac8ba25.png",
        audio: "generated-v2/read-20-questbook-5805518930.wav",
      },
      classroom: {
        image: "generated-v2/read-20-classroom-7c13f43782.png",
        audio: "generated-v2/read-20-classroom-cca67b8288.wav",
      },
      comic: {
        image: "generated-v2/read-20-comic-b5ae2d561a.png",
        audio: "generated-v2/read-20-comic-7ec8c91bf8.wav",
      },
    },
  };

  const addElementsBaseThemeImages = {
    classroom: "base-theme-images/classroom-base-theme-1024.png",
    questbook: "base-theme-images/questbook-base-theme-1024.png",
    comic: "base-theme-images/comic-base-theme-1024.png",
  };

  const addElementsPhase1Variants = {
    "clean-room": {
      classroom: {
        image: "add-elements/phase1-classroom.png",
        source_goal: "Clean up my room before dinner",
      },
    },
    "project-outline": {
      questbook: {
        image: "add-elements/phase1-questbook.png",
        source_goal: "Finish my class project outline",
      },
    },
    "read-20": {
      comic: {
        image: "add-elements/phase1-comic.png",
        source_goal: "Read for 20 minutes",
      },
    },
  };

  const addElementsPhase2Variants = {
    "clean-room": {
      classroom: {
        image: "add-elements/phase2-classroom.png",
        source_goal: "Clean up my room before dinner",
        parent_reference_id: "parent-mom-demo",
        child_reference_id: "child-boy-demo",
      },
    },
    "project-outline": {
      questbook: {
        image: "add-elements/phase2-questbook.png",
        source_goal: "Finish my class project outline",
        parent_reference_id: "parent-dad-demo",
        child_reference_id: "child-girl-demo",
      },
    },
    "read-20": {
      comic: {
        image: "add-elements/phase2-comic.png",
        source_goal: "Read for 20 minutes",
        parent_reference_id: "parent-dad-demo",
        child_reference_id: "child-boy-demo",
      },
    },
  };

  const seededUploads = {
    parent_photo_refs: [
      {
        id: "parent-dad-demo",
        kind: "parent_photo",
        asset_ref: "Dad reference portrait",
        preview_ref: "reference-seeds/parent-reference-photo.png",
        privacy_scope: "session_only",
        created_at: "local-demo",
      },
      {
        id: "parent-mom-demo",
        kind: "parent_photo",
        asset_ref: "Mom reference portrait",
        preview_ref: "reference-seeds/placeholder-female-parent-720.png",
        privacy_scope: "session_only",
        created_at: "local-demo",
      },
    ],
    child_photo_refs: [
      {
        id: "child-boy-demo",
        kind: "child_photo",
        asset_ref: "Boy reference portrait",
        preview_ref: "reference-seeds/kid-reference-photo.png",
        privacy_scope: "session_only",
        created_at: "local-demo",
      },
      {
        id: "child-girl-demo",
        kind: "child_photo",
        asset_ref: "Girl reference portrait",
        preview_ref: "reference-seeds/placeholder-girl-720.png",
        privacy_scope: "session_only",
        created_at: "local-demo",
      },
    ],
    custom_image_reference_refs: [],
    parent_reference_audio_ref: {
      id: "parent-audio-demo",
      kind: "parent_reference_audio",
      asset_ref: "Parent reference audio sample",
      preview_ref: "reference-seeds/parent-reference-audio.m4a",
      privacy_scope: "session_only",
      created_at: "local-demo",
    },
  };

  const defaultGenerationReferenceIds = ["parent-dad-demo", "child-girl-demo"];

  const qualityMode = {
    id: "quality",
    label: "Quality",
    status: "enabled",
    text_model_id: "nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF",
    text_runtime: "llama.cpp",
    text_format: "GGUF",
    text_quantization: "Q4_K_M",
    image_model_id: "black-forest-labs/FLUX.2-klein-9B",
    image_runtime: "Diffusers",
    image_format: "safetensors",
    image_precision: "bf16",
    image_output_size_px: 1024,
    audio_model_id: "openbmb/VoxCPM2",
    audio_runtime: "voxcpm",
    audio_format: "safetensors",
    audio_precision: "bf16",
  };

  const speedMode = {
    id: "speed",
    label: "Speed",
    status: "disabled_planned",
    image_output_size_px: 720,
  };

  const icons = {
    home: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6h-4v6H5a1 1 0 0 1-1-1v-9.5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
    wand: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m14 4 6 6M3 21 17 7l-3-3L3 15v6Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M5 3v3M3.5 4.5h3M20 16v3M18.5 17.5h3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    kid: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 12a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7ZM5.5 20c.7-3.8 2.9-5.8 6.5-5.8s5.8 2 6.5 5.8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    settings: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 15.2a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4Z" stroke="currentColor" stroke-width="2"/><path d="M19 12a7.1 7.1 0 0 0-.1-1l2-1.5-2-3.5-2.4 1a7 7 0 0 0-1.7-1L14.5 3h-5l-.3 3a7 7 0 0 0-1.7 1L5.1 6l-2 3.5 2 1.5a7.1 7.1 0 0 0 0 2l-2 1.5 2 3.5 2.4-1a7 7 0 0 0 1.7 1l.3 3h5l.3-3a7 7 0 0 0 1.7-1l2.4 1 2-3.5-2-1.5c.1-.3.1-.7.1-1Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
    lab: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M9 3h6M10 3v5l-5 9a3 3 0 0 0 2.6 4.5h8.8A3 3 0 0 0 19 17l-5-9V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M7.5 16h9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    check: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m5 12.5 4.2 4L19 7" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    x: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M7 7l10 10M17 7 7 17" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>',
    sound: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 10v4h4l5 4V6l-5 4H4Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M16 9.5c.8.7 1.2 1.5 1.2 2.5s-.4 1.8-1.2 2.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    plus: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>',
  };

  let state = makeFallbackState();

  function makeFallbackState() {
    const seedGoal = createGoal(
      "Finish my class project outline",
      "questbook",
      "goal-seed-project-outline",
      defaultGenerationReferenceIds,
      true
    );
    seedGoal.review_state = "accepted";
    const fallback = {
      active_tab: "home",
      active_theme_id: "questbook",
      generation_mode: "quality",
      available_generation_modes: [qualityMode, speedMode],
      parent_profile: {
        display_name: "Parent",
        photo_refs: seededUploads.parent_photo_refs,
        reference_audio_ref: seededUploads.parent_reference_audio_ref,
        reference_audio_optional: true,
      },
      children: [{ id: "child-1", display_name: "Kid", photo_refs: seededUploads.child_photo_refs }],
      custom_image_reference_refs: [],
      uploads: {
        parent_photo_refs: seededUploads.parent_photo_refs,
        child_photo_refs: seededUploads.child_photo_refs,
        custom_image_reference_refs: [],
        parent_reference_audio_ref: seededUploads.parent_reference_audio_ref,
      },
      generation_references: [],
      goal_draft: {
        ordinary_goal: "Finish my class project outline",
        selected_generation_reference_ids: defaultGenerationReferenceIds,
        generation_mode: "quality",
      },
      pending_review_goal: null,
      goals: [seedGoal],
      accepted_goals: [seedGoal],
      selected_goal_id: "goal-seed-clean-room",
      diy: buildLocalDiyState("questbook", "Finish my class project outline", defaultGenerationReferenceIds),
      generation_status: {
        state: "ready",
        message: "Hosted deterministic generation is ready.",
        backend_transport: "browser_fallback",
        fallback_used: true,
      },
    };
    syncGenerationReferences(fallback);
    return fallback;
  }

  function asset(path) {
    if (/^(data:|https?:|blob:)/.test(String(path || ""))) return path;
    if (ASSET_MANIFEST[path]) return ASSET_MANIFEST[path];
    return `${ASSET_BASE}${path}`;
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function theme() {
    return themes[state.active_theme_id] || themes.questbook;
  }

  function assetKey(goalText) {
    const text = String(goalText || "").toLowerCase();
    if (text.includes("read")) return "read-20";
    if (text.includes("project") || text.includes("outline")) return "project-outline";
    return "clean-room";
  }

  function referenceKind(refId) {
    const lowered = String(refId || "").toLowerCase();
    if (["parent", "dad", "mom"].some((token) => lowered.includes(token))) return "parent_photo";
    if (["child", "kid", "boy", "girl"].some((token) => lowered.includes(token))) return "child_photo";
    return "custom_image_reference";
  }

  function hasParentChildRefs(referenceIds) {
    const kinds = new Set((referenceIds || []).map(referenceKind));
    return kinds.has("parent_photo") && kinds.has("child_photo");
  }

  function mediaAssetsFor(key, themeId, referenceIds) {
    const variant = { ...(assets[key][themeId] || assets[key].questbook) };
    const imageProvenance = {
      image_fallback_source: "generated_v2_fixture",
      add_elements_cache_hit: false,
      add_elements_contract: "not_applied",
      base_theme_image_ref: addElementsBaseThemeImages[themeId],
    };
    if (hasParentChildRefs(referenceIds)) {
      const addElements = addElementsPhase2Variants[key]?.[themeId];
      if (addElements) {
        variant.image = addElements.image;
        Object.assign(imageProvenance, {
          image_fallback_source: "cached_flux2_add_elements_phase2",
          add_elements_cache_hit: true,
          add_elements_phase: "phase2",
          add_elements_contract: "base_theme_plus_parent_child_goal",
          add_elements_source_goal: addElements.source_goal,
          add_elements_reference_ids: [addElements.parent_reference_id, addElements.child_reference_id],
        });
      } else {
        Object.assign(imageProvenance, {
          add_elements_contract: "base_theme_plus_parent_child_goal",
          add_elements_cache_miss_reason: "no_exact_cached_phase2_theme_goal_match",
        });
      }
      return { variant, imageProvenance };
    }
    if (!(referenceIds || []).length) {
      const addElements = addElementsPhase1Variants[key]?.[themeId];
      if (addElements) {
        variant.image = addElements.image;
        Object.assign(imageProvenance, {
          image_fallback_source: "cached_flux2_add_elements_phase1",
          add_elements_cache_hit: true,
          add_elements_phase: "phase1",
          add_elements_contract: "base_theme_plus_goal_no_people",
          add_elements_source_goal: addElements.source_goal,
        });
      }
    }
    return { variant, imageProvenance };
  }

  function titleFor(goalText, themeId) {
    if (themeId === "comic") return "Mission: Everyday Hero";
    if (themeId === "classroom") return "Quest: Ready to Shine";
    return "Quest: Small Brave Step";
  }

  function rewardFor(themeId) {
    if (themeId === "comic") return "Starburst";
    if (themeId === "classroom") return "Badge";
    return "Crest";
  }

  function narrationFor(goalText, themeId) {
    if (themeId === "comic") return `Zoom in on the next win: ${goalText}. Finish it, then call in your victory.`;
    if (themeId === "classroom") return `Take one clear school-day step and finish: ${goalText}.`;
    return `The questbook opens to today's errand: ${goalText}.`;
  }

  function createGoal(ordinaryGoal, themeId, id, referenceIds, audioUsedParentReference) {
    const normalizedTheme = themes[themeId] ? themeId : "questbook";
    const key = assetKey(ordinaryGoal);
    const selectedRefs = referenceIds || [];
    const { variant, imageProvenance } = mediaAssetsFor(key, normalizedTheme, selectedRefs);
    const referenceSignature = (referenceIds || []).join(",");
    return {
      id: id || `goal-${Date.now()}`,
      ordinary_goal: ordinaryGoal,
      generation_mode: "quality",
      theme_id_at_creation: normalizedTheme,
      selected_generation_reference_ids: selectedRefs,
      generated_title: titleFor(ordinaryGoal, normalizedTheme),
      generated_narration: narrationFor(ordinaryGoal, normalizedTheme),
      generated_reward_label: rewardFor(normalizedTheme),
      overlay_text: {
        text: ordinaryGoal,
        theme_style_id: normalizedTheme,
        position: "bottom",
        max_lines: 3,
        is_app_owned: true,
        mutates_image_pixels: false,
        mutates_audio: false,
      },
      media: {
        image_asset_ref: variant.image,
        image_output_size_px: 1024,
        image_mutable_from_review: false,
        audio_asset_ref: variant.audio,
        audio_enabled: true,
        audio_used_parent_reference: Boolean(audioUsedParentReference),
        audio_mutable_from_review: false,
      },
      provenance: {
        text_model_id: qualityMode.text_model_id,
        text_runtime: qualityMode.text_runtime,
        text_format: qualityMode.text_format,
        text_quantization: qualityMode.text_quantization,
        image_model_id: qualityMode.image_model_id,
        image_runtime: qualityMode.image_runtime,
        image_format: qualityMode.image_format,
        image_precision: qualityMode.image_precision,
        audio_model_id: qualityMode.audio_model_id,
        audio_runtime: qualityMode.audio_runtime,
        audio_format: qualityMode.audio_format,
        audio_precision: qualityMode.audio_precision,
        fallback_used: true,
        trace_id: `local-v2-${key}-${normalizedTheme}-quality-media-${referenceSignature || "no-refs"}`,
        ...imageProvenance,
      },
      review_state: "pending",
      kid_completion_state: "not_started",
      parent_reward_state: "not_reviewed",
    };
  }

  function buildTrace(goal) {
    return {
      pipeline: ["plain_goal", "text_step", "image_step", "audio_step", "composed_card"],
      plain_goal: goal.ordinary_goal,
      selected_theme_id: goal.theme_id_at_creation,
      selected_generation_reference_ids: goal.selected_generation_reference_ids,
      generation_mode: "quality",
      text_step: {
        model: qualityMode.text_model_id,
        runtime: qualityMode.text_runtime,
        fallback_used: true,
      },
      image_step: {
        model: qualityMode.image_model_id,
        runtime: qualityMode.image_runtime,
        output_size_px: qualityMode.image_output_size_px,
        result_asset_ref: goal.media.image_asset_ref,
        image_fallback_source: goal.provenance.image_fallback_source,
        add_elements_cache_hit: goal.provenance.add_elements_cache_hit,
        add_elements_contract: goal.provenance.add_elements_contract,
        base_theme_image_ref: goal.provenance.base_theme_image_ref,
      },
      audio_step: {
        model: qualityMode.audio_model_id,
        runtime: qualityMode.audio_runtime,
        result_asset_ref: goal.media.audio_asset_ref,
      },
      composed_card_step: {
        overlay_text: goal.overlay_text.text,
        mutates_image_pixels: false,
      },
      quality_model_contract: qualityMode,
      image_output_size_px: 1024,
      fallback_used: true,
      save_to_app_status: "coming_soon",
    };
  }

  function buildLocalDiyState(themeId, ordinaryGoal, referenceIds) {
    const selectedRefs = referenceIds && referenceIds.length
      ? referenceIds
      : defaultGenerationReferenceIds;
    const preview = createGoal(ordinaryGoal, themeId, "diy-preview", selectedRefs);
    return {
      isolated_surface: true,
      workflow_draft: {
        ordinary_goal: ordinaryGoal,
        selected_theme_id: themes[themeId] ? themeId : "questbook",
        selected_generation_reference_ids: selectedRefs,
        text_step: { model: qualityMode.text_model_id, runtime: qualityMode.text_runtime },
        image_step: { model: qualityMode.image_model_id, output_size_px: qualityMode.image_output_size_px },
        audio_step: { model: qualityMode.audio_model_id, runtime: qualityMode.audio_runtime },
        composed_card_step: { overlay_text: preview.overlay_text.text },
      },
      preview,
      trace_json: buildTrace(preview),
      save_to_app_status: "coming_soon",
    };
  }

  function normalizeGoal(goal) {
    return {
      ...goal,
      selected_generation_reference_ids: goal.selected_generation_reference_ids || [],
      overlay_text: {
        text: goal.overlay_text?.text || goal.ordinary_goal || "",
        theme_style_id: goal.overlay_text?.theme_style_id || goal.theme_id_at_creation || "questbook",
        position: goal.overlay_text?.position || "bottom",
        max_lines: goal.overlay_text?.max_lines || 3,
        is_app_owned: true,
        mutates_image_pixels: false,
        mutates_audio: false,
      },
      media: {
        image_asset_ref: goal.media?.image_asset_ref || assets["clean-room"].questbook.image,
        image_output_size_px: goal.media?.image_output_size_px || 1024,
        image_mutable_from_review: false,
        audio_asset_ref: goal.media?.audio_asset_ref || assets["clean-room"].questbook.audio,
        audio_enabled: true,
        audio_used_parent_reference: Boolean(goal.media?.audio_used_parent_reference),
        audio_mutable_from_review: false,
      },
      provenance: goal.provenance || { ...qualityMode, fallback_used: true },
      review_state: goal.review_state || "pending",
      kid_completion_state: goal.kid_completion_state || "not_started",
      parent_reward_state: goal.parent_reward_state || "not_reviewed",
    };
  }

  function syncStateAliases(targetState = state) {
    const parent = targetState.parent_profile || {};
    const child = (targetState.children || [])[0] || { photo_refs: [] };
    const existingUploads = targetState.uploads || {};
    const hasAudioUpload = Object.prototype.hasOwnProperty.call(existingUploads, "parent_reference_audio_ref");
    targetState.uploads = {
      parent_photo_refs: existingUploads.parent_photo_refs?.length ? existingUploads.parent_photo_refs : parent.photo_refs || [],
      child_photo_refs: existingUploads.child_photo_refs?.length ? existingUploads.child_photo_refs : child.photo_refs || [],
      custom_image_reference_refs: existingUploads.custom_image_reference_refs || targetState.custom_image_reference_refs || [],
      parent_reference_audio_ref: hasAudioUpload
        ? existingUploads.parent_reference_audio_ref
        : parent.reference_audio_ref || parent.parent_reference_audio_ref || null,
    };
    targetState.parent_profile = {
      display_name: parent.display_name || "Parent",
      photo_refs: targetState.uploads.parent_photo_refs,
      reference_audio_ref: targetState.uploads.parent_reference_audio_ref,
      reference_audio_optional: true,
    };
    targetState.children = [
      {
        id: child.id || "child-1",
        display_name: child.display_name || "Kid",
        photo_refs: targetState.uploads.child_photo_refs,
      },
    ];
    targetState.custom_image_reference_refs = targetState.uploads.custom_image_reference_refs;
    targetState.accepted_goals = (targetState.accepted_goals || targetState.goals || []).map(normalizeGoal);
    targetState.goals = targetState.accepted_goals;
    if (!targetState.selected_goal_id && targetState.accepted_goals[0]) targetState.selected_goal_id = targetState.accepted_goals[0].id;
    syncGenerationReferences(targetState);
  }

  function normalizeBootstrap(payload) {
    const fallback = makeFallbackState();
    const nextState = {
      ...fallback,
      ...payload,
      active_tab: "home",
      active_theme_id: themes[payload.active_theme_id] ? payload.active_theme_id : fallback.active_theme_id,
      goal_draft: {
        ...fallback.goal_draft,
        ...(payload.goal_draft || {}),
      },
      diy: payload.diy || fallback.diy,
      generation_status: payload.generation_status || fallback.generation_status,
    };
    syncStateAliases(nextState);
    return nextState;
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function gradioEndpointFor(path) {
    if (path === "/api/bootstrap") return "epic_bootstrap";
    if (path === "/api/generate-goal") return "epic_generate_goal";
    if (path === "/api/diy-preview") return "epic_diy_preview";
    return "";
  }

  function parseSseData(text) {
    const lines = String(text || "").split(/\r?\n/);
    const eventLine = lines.find((line) => line.startsWith("event: error"));
    const dataLine = lines.find((line) => line.startsWith("data: "));
    if (!dataLine) throw new Error("Gradio response did not include data.");
    const parsed = JSON.parse(dataLine.slice(6));
    if (eventLine) throw new Error(Array.isArray(parsed) ? parsed.join(" ") : String(parsed));
    const value = Array.isArray(parsed) ? parsed[0] : parsed;
    return typeof value === "string" ? JSON.parse(value) : value;
  }

  async function gradioApiJson(apiName, payload = {}) {
    const callResponse = await fetch(`${GRADIO_API_PREFIX}/call/${apiName}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ data: [JSON.stringify(payload || {})] }),
    });
    if (!callResponse.ok) throw new Error(`Gradio call failed: ${callResponse.status}`);
    const callBody = await callResponse.json();
    if (!callBody.event_id) throw new Error("Gradio call did not return an event id.");
    const eventResponse = await fetch(`${GRADIO_API_PREFIX}/call/${apiName}/${callBody.event_id}`);
    if (!eventResponse.ok) throw new Error(`Gradio event failed: ${eventResponse.status}`);
    return parseSseData(await eventResponse.text());
  }

  async function apiJson(path, options = {}) {
    const gradioEndpoint = EMBEDDED_SPACE_MODE ? gradioEndpointFor(path) : "";
    if (gradioEndpoint) {
      const payload = options.body ? JSON.parse(options.body) : {};
      return gradioApiJson(gradioEndpoint, payload);
    }
    const response = await fetch(`${API_BASE}${path}`, options);
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return response.json();
  }

  function counts() {
    const pendingReview = state.pending_review_goal ? 1 : 0;
    const activeGoals = state.accepted_goals.filter((goal) => goal.parent_reward_state !== "approved_reward_given").length;
    const awaiting = state.accepted_goals.filter((goal) => goal.parent_reward_state === "waiting_for_approval").length;
    const approved = state.accepted_goals.filter((goal) => goal.parent_reward_state === "approved_reward_given").length;
    return { pendingReview, activeGoals, awaiting, approved };
  }

  function selectedGoal() {
    return state.accepted_goals.find((goal) => goal.id === state.selected_goal_id) || state.accepted_goals[0] || null;
  }

  function setTheme(themeId) {
    if (!themes[themeId]) return;
    state.active_theme_id = themeId;
    document.documentElement.dataset.theme = themeToToken[themeId];
    render();
  }

  function selectTab(tabId) {
    if (tabId === "diy") {
      openDiySurface();
      return;
    }
    state.active_tab = tabId;
    render();
  }

  function openDiySurface() {
    if (EMBEDDED_SPACE_MODE) {
      state.diy = state.diy || buildLocalDiyState(state.active_theme_id, state.goal_draft.ordinary_goal, state.goal_draft.selected_generation_reference_ids);
      state.active_tab = "diy";
      render();
      return;
    }
    const params = new URLSearchParams({
      theme: state.active_theme_id,
      goal: state.goal_draft.ordinary_goal || "Clean up my room before dinner",
    });
    state.goal_draft.selected_generation_reference_ids.forEach((refId) => params.append("ref", refId));
    window.location.assign(`/diy?${params.toString()}`);
  }

  async function updateDiyPreview() {
    const draft = state.diy?.workflow_draft || {
      ordinary_goal: state.goal_draft.ordinary_goal || "Clean up my room before dinner",
      selected_theme_id: state.active_theme_id,
      selected_generation_reference_ids: state.goal_draft.selected_generation_reference_ids,
    };
    try {
      state.diy = await apiJson("/api/diy-preview", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          ordinary_goal: draft.ordinary_goal,
          selected_theme_id: draft.selected_theme_id,
          selected_generation_reference_ids: draft.selected_generation_reference_ids,
        }),
      });
    } catch (error) {
      state.diy = buildLocalDiyState(
        draft.selected_theme_id,
        draft.ordinary_goal,
        draft.selected_generation_reference_ids
      );
      state.diy.trace_json.local_preview_api = "unavailable_using_embedded_fallback";
    }
    render();
  }

  function setDiyTheme(themeId) {
    if (!themes[themeId]) return;
    state.diy = state.diy || buildLocalDiyState(state.active_theme_id, state.goal_draft.ordinary_goal, state.goal_draft.selected_generation_reference_ids);
    state.diy.workflow_draft.selected_theme_id = themeId;
    updateDiyPreview();
  }

  const uploadActions = {
    parent_photo: "upload-parent-photo",
    child_photo: "upload-child-photo",
    parent_reference_audio: "upload-parent-audio",
    custom_image_reference: "upload-custom-image-reference",
  };

  const removeActions = {
    parent_photo: "remove-parent-photo",
    child_photo: "remove-child-photo",
    parent_reference_audio: "remove-parent-audio",
    custom_image_reference: "remove-custom-image-reference",
  };

  function uploadLabel(kind) {
    if (kind === "parent_photo") return "Parent photo";
    if (kind === "child_photo") return "Child photo";
    if (kind === "parent_reference_audio") return "Parent audio";
    return "Custom reference";
  }

  function fileToUploadRef(kind, file) {
    const ref = {
      id: `${kind}-${Date.now()}-${Math.random().toString(16).slice(2, 7)}`,
      kind,
      asset_ref: file?.name || `${kind}-session-demo`,
      preview_ref: file ? URL.createObjectURL(file) : null,
      privacy_scope: "session_only",
      created_at: new Date().toISOString(),
    };
    return ref;
  }

  function addUpload(kind, file) {
    const ref = fileToUploadRef(kind, file);
    if (kind === "parent_photo") state.uploads.parent_photo_refs.push(ref);
    if (kind === "child_photo") state.uploads.child_photo_refs.push(ref);
    if (kind === "custom_image_reference") state.uploads.custom_image_reference_refs.push(ref);
    if (kind === "parent_reference_audio") state.uploads.parent_reference_audio_ref = ref;
    syncStateAliases();
    render();
  }

  function removeUpload(kind, id) {
    const refs = [
      ...state.uploads.parent_photo_refs,
      ...state.uploads.child_photo_refs,
      ...state.uploads.custom_image_reference_refs,
      state.uploads.parent_reference_audio_ref,
    ].filter(Boolean);
    const removed = refs.find((ref) => ref.kind === kind && (!id || ref.id === id));
    if (removed?.preview_ref?.startsWith("blob:")) URL.revokeObjectURL(removed.preview_ref);
    if (kind === "parent_photo") state.uploads.parent_photo_refs = state.uploads.parent_photo_refs.filter((ref) => ref.id !== id);
    if (kind === "child_photo") state.uploads.child_photo_refs = state.uploads.child_photo_refs.filter((ref) => ref.id !== id);
    if (kind === "custom_image_reference") state.uploads.custom_image_reference_refs = state.uploads.custom_image_reference_refs.filter((ref) => ref.id !== id);
    if (kind === "parent_reference_audio") state.uploads.parent_reference_audio_ref = null;
    syncStateAliases();
    render();
  }

  function syncGenerationReferences(targetState = state) {
    const refs = [
      ...targetState.uploads.parent_photo_refs,
      ...targetState.uploads.child_photo_refs,
      ...targetState.uploads.custom_image_reference_refs,
    ];
    targetState.generation_references = refs.map((ref) => ({
      id: `gen-${ref.id}`,
      source: ref.kind,
      upload_ref_id: ref.id,
      selected: targetState.goal_draft.selected_generation_reference_ids.includes(ref.id),
    }));
  }

  function toggleGenerationReference(refId) {
    const selected = state.goal_draft.selected_generation_reference_ids;
    state.goal_draft.selected_generation_reference_ids = selected.includes(refId)
      ? selected.filter((item) => item !== refId)
      : [...selected, refId];
    syncGenerationReferences();
    render();
  }

  async function generateGoal() {
    const goalText = state.goal_draft.ordinary_goal.trim();
    if (!goalText) return;
    const started = performance.now();
    state.generation_status = {
      state: "generating",
      message: EMBEDDED_SPACE_MODE
        ? "Generating through the hosted Gradio backend..."
        : "Generating through the local app backend...",
      backend_transport: EMBEDDED_SPACE_MODE ? "gradio_blocks_named_api" : "fastapi_route",
      fallback_used: null,
    };
    render();
    try {
      const [generated] = await Promise.all([
        apiJson("/api/generate-goal", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          ordinary_goal: goalText,
          ui_theme_id: state.active_theme_id,
          selected_generation_reference_ids: state.goal_draft.selected_generation_reference_ids,
          audio_used_parent_reference: Boolean(state.uploads.parent_reference_audio_ref),
        }),
        }),
        sleep(500),
      ]);
      state.pending_review_goal = normalizeGoal(generated);
      state.generation_status = {
        state: "success",
        message: `Generated through ${state.pending_review_goal.provenance.backend_transport || "app backend"}; fallback_used=${String(Boolean(state.pending_review_goal.provenance.fallback_used))}.`,
        backend_transport: state.pending_review_goal.provenance.backend_transport || "app_backend",
        fallback_used: Boolean(state.pending_review_goal.provenance.fallback_used),
        latency_ms: Math.round(performance.now() - started),
      };
    } catch (error) {
      state.pending_review_goal = createGoal(
        goalText,
        state.active_theme_id,
        `goal-review-${Date.now()}`,
        state.goal_draft.selected_generation_reference_ids,
        Boolean(state.uploads.parent_reference_audio_ref)
      );
      state.pending_review_goal.provenance.backend_transport = "browser_fallback";
      state.pending_review_goal.provenance.fallback_reason = String(error?.message || error || "backend unavailable");
      state.generation_status = {
        state: "fallback",
        message: "Hosted backend was unavailable, so this preview used browser fallback.",
        backend_transport: "browser_fallback",
        fallback_used: true,
        latency_ms: Math.round(performance.now() - started),
      };
    }
    state.active_tab = "parent_goals";
    render();
  }

  function acceptGoal() {
    if (!state.pending_review_goal) return;
    const accepted = {
      ...state.pending_review_goal,
      review_state: "accepted",
      kid_completion_state: "not_started",
      parent_reward_state: "not_reviewed",
    };
    state.accepted_goals.unshift(accepted);
    state.goals = state.accepted_goals;
    state.selected_goal_id = accepted.id;
    state.pending_review_goal = null;
    state.active_tab = "kid_goals";
    render();
  }

  function cancelGoal() {
    state.pending_review_goal = null;
    state.active_tab = "parent_goals";
    render();
  }

  function updateOverlay(text) {
    if (!state.pending_review_goal) return;
    state.pending_review_goal.overlay_text.text = text;
  }

  function completeGoal(goalId) {
    const goal = state.accepted_goals.find((item) => item.id === goalId);
    if (!goal) return;
    goal.kid_completion_state = "completed";
    goal.parent_reward_state = "waiting_for_approval";
    render();
  }

  function approveGoal(goalId) {
    const goal = state.accepted_goals.find((item) => item.id === goalId);
    if (!goal) return;
    goal.kid_completion_state = "completed";
    goal.parent_reward_state = "approved_reward_given";
    render();
  }

  function flourishCorners() {
    const flourish = '<svg viewBox="0 0 60 60" fill="none"><path d="M8 52c16-3 19-10 20-22 1 12 5 19 24 22M8 8c16 3 19 10 20 22 1-12 5-19 24-22" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>';
    return `
      <span class="corner-flourish tl">${flourish}</span>
      <span class="corner-flourish tr">${flourish}</span>
      <span class="corner-flourish bl">${flourish}</span>
      <span class="corner-flourish br">${flourish}</span>
    `;
  }

  function shellHeader() {
    return `
      <div class="app-head">
        <div class="wordmark" aria-label="Epic Errands">
          <span class="display">Epic Errands</span>
          <span class="sub">${escapeHtml(theme().parentTitle)} / ${escapeHtml(theme().kidTitle)}</span>
        </div>
      </div>
    `;
  }

  function navHtml() {
    const c = counts();
    const tabs = [
      ["home", "Home", icons.home, ""],
      ["parent_goals", "Parent", icons.wand, c.pendingReview + c.awaiting ? c.pendingReview + c.awaiting : ""],
      ["kid_goals", "Kid", icons.kid, c.activeGoals || ""],
      ["settings", "Settings", icons.settings, ""],
      ["diy", "DIY", icons.lab, ""],
    ];
    return `
      <nav class="mobile-tabs" data-design-id="mobile-tab-nav" aria-label="Primary">
        ${tabs
          .map(([id, label, icon, badge]) => `
            <button class="tab-btn" type="button" data-action="select-tab" data-tab="${id}" aria-pressed="${state.active_tab === id}">
              ${icon}<span>${escapeHtml(label)}</span>${badge ? `<b>${escapeHtml(badge)}</b>` : ""}
            </button>
          `)
          .join("")}
      </nav>
    `;
  }

  function themePickerHtml() {
    return `
      <section class="panel" data-design-id="app-theme-picker">
        <div class="panel-head">
          <h2>App Styling</h2>
          <span>${escapeHtml(theme().label)}</span>
        </div>
        <div class="segmented">
          ${Object.entries(themes)
            .map(([id, item]) => `
              <button class="seg-btn" type="button" data-action="select-theme" data-theme="${id}" aria-pressed="${state.active_theme_id === id}">
                <span class="swatch swatch-${id}"></span>
                <span>${escapeHtml(item.label)}</span>
              </button>
            `)
            .join("")}
        </div>
      </section>
    `;
  }

  function uploadPanel(title, designId, kind, refs, accept) {
    const items = refs.length
      ? refs
          .map((ref, index) => `
            <div class="upload-chip${kind === "parent_reference_audio" ? " upload-chip--stack" : ""}">
              <div class="upload-chip__row">
                <span class="upload-chip__main">
                  ${ref.preview_ref && kind !== "parent_reference_audio" ? `<img class="upload-thumb" src="${escapeHtml(asset(ref.preview_ref))}" alt="">` : ""}
                  <span>${escapeHtml(ref.asset_ref || `${title} ${index + 1}`)}</span>
                </span>
                <button class="icon-mini" type="button" data-action="${removeActions[kind]}" data-kind="${kind}" data-id="${ref.id}" aria-label="Remove ${escapeHtml(title)}">${icons.x}</button>
              </div>
              ${ref.preview_ref && kind === "parent_reference_audio" ? `<audio class="upload-audio" controls preload="metadata" src="${escapeHtml(asset(ref.preview_ref))}"></audio>` : ""}
            </div>
          `)
          .join("")
      : `<p class="empty-line">Session only</p>`;
    return `
      <section class="panel" data-design-id="${designId}">
        <div class="panel-head">
          <h2>${escapeHtml(title)}</h2>
          <label class="btn-ghost compact upload-trigger" data-action="${uploadActions[kind]}">
            ${icons.plus}<span>Add</span>
            <input class="visually-hidden-file" type="file" data-upload-kind="${kind}" accept="${escapeHtml(accept)}">
          </label>
        </div>
        <div class="upload-list">${items}</div>
      </section>
    `;
  }

  function generationReferencesHtml() {
    const refs = [
      ...state.uploads.parent_photo_refs,
      ...state.uploads.child_photo_refs,
      ...state.uploads.custom_image_reference_refs,
    ];
    return `
      <section class="panel" data-design-id="generation-reference-picker">
        <div class="panel-head">
          <h2>Generation References</h2>
          <span>${refs.length ? `${refs.length} available` : "Optional"}</span>
        </div>
        <div class="ref-grid">
          ${refs.length
            ? refs
                .map((ref) => `
                  <button class="ref-chip" type="button" data-action="select-generation-reference" data-ref-id="${ref.id}" aria-pressed="${state.goal_draft.selected_generation_reference_ids.includes(ref.id)}">
                    <span>${escapeHtml(ref.kind.replaceAll("_", " "))}</span>
                    <small>${state.goal_draft.selected_generation_reference_ids.includes(ref.id) ? "Selected" : "Tap to use"}</small>
                  </button>
                `)
                .join("")
            : `<p class="empty-line">Parent photo, child photo, or custom image can be added above.</p>`}
        </div>
      </section>
    `;
  }

  function generationModeHtml() {
    return `
      <section class="panel" data-design-id="generation-mode-control">
        <div class="panel-head">
          <h2>Generation Mode</h2>
          <span>Quality selected</span>
        </div>
        <div class="mode-row">
          <button class="mode-btn" type="button" data-mode="quality" aria-pressed="true">
            <b>Quality</b>
            <span>1024 x 1024</span>
          </button>
          <button class="mode-btn" type="button" data-mode="speed" disabled aria-disabled="true">
            <b>Speed</b>
            <span>720 x 720 planned</span>
          </button>
        </div>
      </section>
    `;
  }

  function generationStatusHtml() {
    const status = state.generation_status;
    if (!status || status.state === "ready") return "";
    const label = status.state === "fallback" ? "Fallback" : "Backend";
    return `
      <div class="statusbar generation-status" data-generation-status="${escapeHtml(status.state)}">
        <span class="statusbar__dot"></span>
        <div class="statusbar__info">
          <b>${escapeHtml(label)}</b>
          ${escapeHtml(status.message)}
          ${status.latency_ms ? `<small>${escapeHtml(status.latency_ms)}ms</small>` : ""}
        </div>
      </div>
    `;
  }

  function homeHtml() {
    const c = counts();
    const current = selectedGoal();
    return `
      <section class="lead compact-lead">
        <h1>${escapeHtml(theme().goalNoun)} Board</h1>
        <p>${escapeHtml(theme().kidTitle)} has ${c.activeGoals} active ${c.activeGoals === 1 ? "card" : "cards"}.</p>
      </section>
      <section class="summary-grid" data-design-id="home-status-summary">
        <div class="summary-tile"><b>${c.pendingReview}</b><span>Review</span></div>
        <div class="summary-tile"><b>${c.awaiting}</b><span>Waiting</span></div>
        <div class="summary-tile"><b>${c.approved}</b><span>Rewards</span></div>
      </section>
      <section class="panel current-goal" data-design-id="current-kid-goal-shortcut">
        <div class="panel-head">
          <h2>Current Kid Card</h2>
          <button class="btn-ghost compact" type="button" data-action="open-kid-goal">${icons.kid}<span>Open</span></button>
        </div>
        ${current ? goalMiniHtml(current) : `<p class="empty-line">No active kid card yet.</p>`}
      </section>
    `;
  }

  function settingsHtml() {
    const audioRefs = state.uploads.parent_reference_audio_ref ? [state.uploads.parent_reference_audio_ref] : [];
    return `
      ${themePickerHtml()}
      ${uploadPanel("Parent Photos", "parent-details-panel", "parent_photo", state.uploads.parent_photo_refs, "image/*")}
      ${uploadPanel("Parent Reference Audio", "parent-details-panel", "parent_reference_audio", audioRefs, "audio/*")}
      ${uploadPanel("Child Photos", "children-details-panel", "child_photo", state.uploads.child_photo_refs, "image/*")}
      ${uploadPanel("Custom Image Reference", "custom-image-reference-panel", "custom_image_reference", state.uploads.custom_image_reference_refs, "image/*")}
      ${generationReferencesHtml()}
      ${generationModeHtml()}
      <div class="statusbar">
        <span class="statusbar__dot"></span>
        <div class="statusbar__info"><b>Audio enabled.</b> Parent reference audio is optional.</div>
      </div>
    `;
  }

  function parentGoalsHtml() {
    const isGenerating = state.generation_status?.state === "generating";
    return `
      <section class="panel" data-design-id="create-goal-form">
        <div class="panel-head">
          <h2>Create ${escapeHtml(theme().goalNoun)}</h2>
          <span>Quality</span>
        </div>
        <label class="field">
          <span class="lab">Ordinary goal</span>
          <textarea class="field__input goal-textarea" data-field="goal-draft">${escapeHtml(state.goal_draft.ordinary_goal)}</textarea>
        </label>
        ${generationReferencesHtml()}
        <button class="btn-primary" type="button" data-action="generate-goal" ${isGenerating ? "disabled" : ""}>
          ${icons.wand}<span>${isGenerating ? "Generating..." : "Generate Goal"}</span>
        </button>
        ${generationStatusHtml()}
      </section>
      ${state.pending_review_goal ? reviewGoalHtml(state.pending_review_goal) : ""}
      ${approvalQueueHtml()}
    `;
  }

  function reviewGoalHtml(goal) {
    return `
      <section class="review-panel" data-design-id="review-goal-panel">
        <div class="panel-head">
          <h2>Review Goal</h2>
          <span>${escapeHtml(goal.media.image_output_size_px)} x ${escapeHtml(goal.media.image_output_size_px)}</span>
        </div>
        <div class="media-square">
          <img src="${asset(goal.media.image_asset_ref)}" alt="${escapeHtml(goal.generated_title)} generated image">
          <div class="goal-overlay editable" data-design-id="editable-goal-overlay" contenteditable="true" role="textbox" aria-label="Editable goal overlay">${escapeHtml(goal.overlay_text.text)}</div>
        </div>
        <div class="copy-block">
          <h3>${escapeHtml(goal.generated_title)}</h3>
          <p>${escapeHtml(goal.generated_narration)}</p>
          <b>${escapeHtml(goal.generated_reward_label)}</b>
        </div>
        <div class="audio-shell" data-design-id="audio-play-hook">
          <audio controls preload="metadata" src="${asset(goal.media.audio_asset_ref)}"></audio>
        </div>
        <details class="provenance">
          <summary>Provenance</summary>
          <p>${escapeHtml(goal.provenance.text_model_id)} / ${escapeHtml(goal.provenance.image_model_id)} / ${escapeHtml(goal.provenance.audio_model_id)}</p>
          <p>${escapeHtml(goal.provenance.image_fallback_source || "generated_v2_fixture")} / ${escapeHtml(goal.provenance.add_elements_contract || "not_applied")}</p>
          <p>fallback_used=${escapeHtml(String(goal.provenance.fallback_used))}</p>
        </details>
        <div class="review-actions">
          <button class="btn-ghost" type="button" data-action="cancel-goal">${icons.x}<span>Cancel</span></button>
          <button class="btn-primary" type="button" data-action="accept-goal">${icons.check}<span>Accept</span></button>
        </div>
      </section>
    `;
  }

  function approvalQueueHtml() {
    const rows = state.accepted_goals;
    return `
      <section class="panel" data-design-id="parent-approval-queue">
        <div class="panel-head">
          <h2>Reward Queue</h2>
          <span>${counts().awaiting} waiting</span>
        </div>
        <div class="parent-list">
          ${rows
            .map((goal) => {
              const waiting = goal.parent_reward_state === "waiting_for_approval";
              return `
                <article class="parent-row">
                  <div>
                    <div class="parent-row__title">${escapeHtml(goal.generated_title)}</div>
                    <div class="parent-row__meta">${escapeHtml(goal.ordinary_goal)} - ${escapeHtml(goal.generated_reward_label)}</div>
                  </div>
                  <div class="parent-actions">
                    <span class="parent-row__status">${escapeHtml(goal.parent_reward_state.replaceAll("_", " "))}</span>
                    <button class="btn-ghost" type="button" data-action="approve-goal" data-goal-id="${goal.id}" ${waiting ? "" : "disabled"}>
                      ${icons.check}<span>Approve</span>
                    </button>
                  </div>
                </article>
              `;
            })
            .join("")}
        </div>
      </section>
    `;
  }

  function goalMiniHtml(goal) {
    return `
      <button class="mini-goal" type="button" data-action="open-goal-card" data-goal-id="${goal.id}">
        <img src="${asset(goal.media.image_asset_ref)}" alt="${escapeHtml(goal.generated_title)} thumbnail">
        <span>
          <b>${escapeHtml(goal.generated_title)}</b>
          <small>${escapeHtml(goal.ordinary_goal)}</small>
        </span>
      </button>
    `;
  }

  function kidGoalsHtml() {
    const selected = selectedGoal();
    return `
      <section class="panel" data-design-id="kid-goal-thumbnail-grid">
        <div class="panel-head">
          <h2>${escapeHtml(theme().kidTitle)}</h2>
          <span>${state.accepted_goals.length} cards</span>
        </div>
        <div class="thumb-grid">
          ${state.accepted_goals.length ? state.accepted_goals.map(goalMiniHtml).join("") : `<p class="empty-line">No accepted goals yet.</p>`}
        </div>
      </section>
      ${selected ? kidGoalCardHtml(selected) : ""}
    `;
  }

  function kidGoalCardHtml(goal) {
    const waiting = goal.parent_reward_state === "waiting_for_approval";
    const approved = goal.parent_reward_state === "approved_reward_given";
    return `
      <section class="kid-card no-generated-steps" data-design-id="kid-goal-card">
        <div class="media-square">
          <img src="${asset(goal.media.image_asset_ref)}" alt="${escapeHtml(goal.generated_title)} generated image">
          <div class="goal-overlay readonly" data-design-id="read-only-goal-overlay">${escapeHtml(goal.overlay_text.text)}</div>
        </div>
        <div class="copy-block">
          <h3>${escapeHtml(goal.generated_title)}</h3>
          <p>${escapeHtml(goal.generated_narration)}</p>
          <b>${escapeHtml(goal.generated_reward_label)}</b>
        </div>
        <div class="audio-shell" data-design-id="audio-play-hook">
          <audio controls preload="metadata" src="${asset(goal.media.audio_asset_ref)}"></audio>
        </div>
        <button class="btn-primary" type="button" data-action="complete-goal" data-goal-id="${goal.id}" ${waiting || approved ? "disabled" : ""}>
          ${icons.check}<span>${approved ? "Reward Given" : waiting ? "Waiting" : "I Did It"}</span>
        </button>
        ${waiting ? `<p class="state-note"><strong>${escapeHtml(themes[goal.theme_id_at_creation].parentTitle)}:</strong> ${escapeHtml(themes[goal.theme_id_at_creation].waitingCopy)}</p>` : ""}
        ${approved ? `<p class="state-note"><strong>${escapeHtml(goal.generated_reward_label)} granted.</strong></p>` : ""}
      </section>
    `;
  }

  function diyRedirectHtml() {
    if (EMBEDDED_SPACE_MODE) return diyInlineHtml();
    return `
      <section class="panel diy-route-panel">
        <div class="panel-head">
          <h2>DIY Lab</h2>
          <span>Separate surface</span>
        </div>
        <p class="empty-line">Opening the isolated DIY workflow mirror.</p>
        <button class="btn-primary" type="button" data-action="open-diy-surface">${icons.lab}<span>Open DIY</span></button>
      </section>
    `;
  }

  function stepHtml(label, step) {
    return `
      <div class="diy-step">
        <b>${escapeHtml(label)}</b>
        <span>${escapeHtml(step.model || step.result_asset_ref || step.overlay_text || "Ready")}</span>
        <small>${escapeHtml(step.runtime || step.output_size_px || step.fallback_used || "")}</small>
      </div>
    `;
  }

  function diyInlineHtml() {
    state.diy = state.diy || buildLocalDiyState(state.active_theme_id, state.goal_draft.ordinary_goal, state.goal_draft.selected_generation_reference_ids);
    const draft = state.diy.workflow_draft;
    const preview = state.diy.preview;
    const trace = state.diy.trace_json || {};
    return `
      <div class="diy-topline">
        <button class="btn-ghost compact" type="button" data-action="back-main-app">${icons.home}<span>Main App</span></button>
        <span class="empty-line">Isolated surface</span>
      </div>
      <section class="panel diy-native-panel" data-design-id="diy-workflow-native-link">
        <div class="panel-head">
          <h1>DIY Lab</h1>
          <span>Embedded Space mode</span>
        </div>
        <p class="empty-line diy-native-note">
          The workflow mirror opens inside this Space so the private hosted app does not navigate into a recursive Gradio frame.
        </p>
      </section>
      <section class="panel" data-design-id="diy-workflow-mirror">
        <div class="panel-head">
          <h2>V2 Preview Inputs</h2>
          <span>${escapeHtml(themes[draft.selected_theme_id]?.label || themes.questbook.label)}</span>
        </div>
        <label class="field">
          <span class="lab">Workflow draft</span>
          <textarea class="field__input goal-textarea" data-field="diy-goal">${escapeHtml(draft.ordinary_goal)}</textarea>
        </label>
        <div class="segmented small">
          ${Object.entries(themes)
            .map(([id, item]) => `
              <button class="seg-btn" type="button" data-action="diy-theme" data-theme="${id}" aria-pressed="${draft.selected_theme_id === id}">
                <span>${escapeHtml(item.label)}</span>
              </button>
            `)
            .join("")}
        </div>
        <div class="diy-ref-list" aria-label="Selected generation references">
          ${draft.selected_generation_reference_ids.map((ref) => `<span>${escapeHtml(ref)}</span>`).join("")}
        </div>
        <button class="btn-ghost" type="button" data-action="update-diy-preview">${icons.wand}<span>Update Preview</span></button>
      </section>
      <section class="panel">
        <div class="panel-head">
          <h2>Pipeline</h2>
          <span>Quality</span>
        </div>
        <div class="diy-step-grid">
          ${stepHtml("Text / Quest JSON", trace.text_step || {})}
          ${stepHtml("Image Request / Result", trace.image_step || {})}
          ${stepHtml("Audio Request / Result", trace.audio_step || {})}
          ${stepHtml("Composed Card", trace.composed_card_step || {})}
        </div>
      </section>
      ${preview ? `
        <section class="kid-card diy-preview">
          <div class="media-square">
            <img src="${asset(preview.media.image_asset_ref)}" alt="${escapeHtml(preview.generated_title)} DIY preview">
            <div class="goal-overlay readonly">${escapeHtml(preview.overlay_text.text)}</div>
          </div>
          <div class="copy-block">
            <h3>${escapeHtml(preview.generated_title)}</h3>
            <p>${escapeHtml(preview.generated_narration)}</p>
            <b>${escapeHtml(preview.generated_reward_label)}</b>
          </div>
          <div class="audio-shell" data-design-id="audio-play-hook">
            <audio controls preload="metadata" src="${asset(preview.media.audio_asset_ref)}"></audio>
          </div>
        </section>
      ` : ""}
      <section class="panel" data-design-id="diy-save-back-notice">
        <div class="panel-head">
          <h2>Trace</h2>
          <button class="btn-ghost compact" type="button" data-action="save-to-app" disabled>Coming soon</button>
        </div>
        <details class="provenance" open>
          <summary>Model details</summary>
          <p>${escapeHtml(JSON.stringify(trace.quality_mode || trace.quality_model_contract || {}, null, 2))}</p>
        </details>
        <pre class="trace-json">${escapeHtml(JSON.stringify(trace, null, 2))}</pre>
      </section>
    `;
  }

  function currentScreenHtml() {
    if (state.active_tab === "settings") return settingsHtml();
    if (state.active_tab === "parent_goals") return parentGoalsHtml();
    if (state.active_tab === "kid_goals") return kidGoalsHtml();
    if (state.active_tab === "diy") return diyRedirectHtml();
    return homeHtml();
  }

  function renderShell() {
    root.innerHTML = `
      <article class="card ornate v2-shell">
        ${flourishCorners()}
        <div class="card-inner app-shell">
          <div data-shell-region="header"></div>
          <div data-shell-region="nav"></div>
          <main class="app-screen" data-shell-region="screen" data-active-tab="${escapeHtml(state.active_tab)}"></main>
        </div>
      </article>
    `;
  }

  function render() {
    if (!root) return;
    document.documentElement.dataset.theme = themeToToken[state.active_theme_id];
    if (!root.querySelector('[data-shell-region="screen"]')) renderShell();
    root.querySelector('[data-shell-region="header"]').innerHTML = shellHeader();
    root.querySelector('[data-shell-region="nav"]').innerHTML = navHtml();
    const screen = root.querySelector('[data-shell-region="screen"]');
    screen.dataset.activeTab = state.active_tab;
    screen.innerHTML = currentScreenHtml();
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button || button.disabled) return;
    const action = button.dataset.action;
    if (action === "select-tab") selectTab(button.dataset.tab);
    if (action === "select-theme") setTheme(button.dataset.theme);
    if (Object.values(removeActions).includes(action)) removeUpload(button.dataset.kind, button.dataset.id);
    if (action === "select-generation-reference") toggleGenerationReference(button.dataset.refId);
    if (action === "generate-goal") generateGoal();
    if (action === "accept-goal") acceptGoal();
    if (action === "cancel-goal") cancelGoal();
    if (action === "open-diy-surface") openDiySurface();
    if (action === "back-main-app") selectTab("home");
    if (action === "diy-theme") setDiyTheme(button.dataset.theme);
    if (action === "update-diy-preview") updateDiyPreview();
    if (action === "open-kid-goal") selectTab("kid_goals");
    if (action === "open-goal-card") {
      state.selected_goal_id = button.dataset.goalId;
      selectTab("kid_goals");
    }
    if (action === "complete-goal") completeGoal(button.dataset.goalId);
    if (action === "approve-goal") approveGoal(button.dataset.goalId);
  });

  document.addEventListener("change", (event) => {
    const input = event.target.closest("[data-upload-kind]");
    if (!input || !input.files || !input.files[0]) return;
    addUpload(input.dataset.uploadKind, input.files[0]);
    input.value = "";
  });

  document.addEventListener("input", (event) => {
    const field = event.target.closest("[data-field]");
    if (!field) return;
    if (field.dataset.field === "goal-draft") state.goal_draft.ordinary_goal = field.value;
    if (field.dataset.field === "diy-goal") {
      state.diy = state.diy || buildLocalDiyState(state.active_theme_id, state.goal_draft.ordinary_goal, state.goal_draft.selected_generation_reference_ids);
      state.diy.workflow_draft.ordinary_goal = field.value;
    }
  });

  document.addEventListener("blur", (event) => {
    const overlay = event.target.closest('[data-design-id="editable-goal-overlay"]');
    if (overlay) updateOverlay(overlay.textContent.trim());
  }, true);

  async function init() {
    try {
      state = normalizeBootstrap(await apiJson("/api/bootstrap"));
    } catch (error) {
      state = makeFallbackState();
    }
    setTheme(state.active_theme_id);
  }

  init();
})();
