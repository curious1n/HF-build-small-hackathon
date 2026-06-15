(function () {
  const ASSET_BASE = window.EPIC_ASSET_BASE || "/assets/";
  const API_BASE = window.EPIC_API_BASE || "";
  const root = document.getElementById("diy-app");

  const themeToToken = {
    classroom: "storybook",
    questbook: "atelier",
    comic: "comic",
  };

  const themes = {
    classroom: { label: "Classroom" },
    questbook: { label: "Questbook" },
    comic: { label: "Comic" },
  };

  const icons = {
    back: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M15 18 9 12l6-6" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    wand: '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m14 4 6 6M3 21 17 7l-3-3L3 15v6Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M5 3v3M3.5 4.5h3M20 16v3M18.5 17.5h3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
  };

  const params = new URLSearchParams(window.location.search);
  let state = {
    workflow_draft: {
      ordinary_goal: params.get("goal") || "Clean up my room before dinner",
      selected_theme_id: normalizedTheme(params.get("theme") || "questbook"),
      selected_generation_reference_ids: params.getAll("ref").length
        ? params.getAll("ref")
        : ["parent-photo-demo", "child-photo-demo", "custom-image-reference-demo"],
    },
    preview: null,
    trace_json: {},
    save_to_app_status: "coming_soon",
  };

  function asset(path) {
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

  function normalizedTheme(value) {
    return themes[value] ? value : "questbook";
  }

  async function postJson(path, payload) {
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return response.json();
  }

  async function updatePreview() {
    try {
      state = await postJson("/api/diy-preview", {
        ordinary_goal: state.workflow_draft.ordinary_goal,
        selected_theme_id: state.workflow_draft.selected_theme_id,
        selected_generation_reference_ids: state.workflow_draft.selected_generation_reference_ids,
      });
    } catch (error) {
      state.trace_json = {
        error: "local_diy_preview_api_unavailable",
        message: String(error.message || error),
        save_to_app_status: "coming_soon",
      };
    }
    render();
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

  function nativeWorkflowHtml() {
    return `
      <section class="panel diy-native-panel" data-design-id="diy-workflow-native-link">
        <div class="panel-head">
          <h1>DIY Lab</h1>
          <a class="btn-ghost compact" href="/diy-workflow/" target="_blank" rel="noreferrer">
            <span>Open Full Workflow</span>
          </a>
        </div>
        <p class="empty-line diy-native-note">
          The full Gradio workflow canvas is beta and opens separately; this surface is the V2 mobile mirror used for local UAT.
        </p>
      </section>
    `;
  }

  function render() {
    if (!root) return;
    const draft = state.workflow_draft;
    const preview = state.preview;
    const trace = state.trace_json || {};
    document.documentElement.dataset.theme = themeToToken[normalizedTheme(draft.selected_theme_id)];
    root.innerHTML = `
      <article class="card screen-in ornate v2-shell diy-route">
        <div class="card-inner app-shell">
          <div class="diy-topline">
            <a class="btn-ghost compact" href="/">${icons.back}<span>Main App</span></a>
            <span class="empty-line">Isolated surface</span>
          </div>
          ${nativeWorkflowHtml()}
          <section class="panel" data-design-id="diy-workflow-mirror">
            <div class="panel-head">
              <h2>V2 Preview Inputs</h2>
              <span>${escapeHtml(themes[normalizedTheme(draft.selected_theme_id)].label)}</span>
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
              <p>${escapeHtml(JSON.stringify(trace.quality_mode || {}, null, 2))}</p>
            </details>
            <pre class="trace-json">${escapeHtml(JSON.stringify(trace, null, 2))}</pre>
          </section>
        </div>
      </article>
    `;
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button || button.disabled) return;
    if (button.dataset.action === "diy-theme") {
      state.workflow_draft.selected_theme_id = normalizedTheme(button.dataset.theme);
      updatePreview();
    }
    if (button.dataset.action === "update-diy-preview") updatePreview();
  });

  document.addEventListener("input", (event) => {
    const field = event.target.closest("[data-field]");
    if (!field) return;
    if (field.dataset.field === "diy-goal") state.workflow_draft.ordinary_goal = field.value;
  });

  render();
  updatePreview();
})();
