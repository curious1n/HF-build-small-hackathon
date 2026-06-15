const state = {
  packet: null,
  view: "ready",
  mode: "hinglish",
  recorder: null,
  chunks: [],
  startedAt: 0,
  lastTrace: null,
  transcript: "",
  modelMessage: "",
  modelRuntime: "hf_space",
  transcriptOpen: false,
  simulateNextSendFailure: false,
};

const els = {
  brandName: document.querySelector("#brand-name"),
  runtimePillLabel: document.querySelector("#runtime-pill-label"),
  heading: document.querySelector("#widget-heading"),
  subheading: document.querySelector("#widget-subheading"),
  modeButtons: [...document.querySelectorAll("[data-mode]")],
  runtimeSwitch: document.querySelector("#runtime-switch"),
  composePanel: document.querySelector("#compose-panel"),
  micPanel: document.querySelector("#mic-panel"),
  recordingPanel: document.querySelector("#recording-panel"),
  processingPanel: document.querySelector("#processing-panel"),
  reviewPanel: document.querySelector("#review-panel"),
  successPanel: document.querySelector("#success-panel"),
  simpleErrorPanel: document.querySelector("#simple-error-panel"),
  draftErrorPanel: document.querySelector("#draft-error-panel"),
  stateLabel: document.querySelector("#state-label"),
  helperCopy: document.querySelector("#helper-copy"),
  recordButton: document.querySelector("#record-button"),
  recordDisabledReason: document.querySelector("#record-disabled-reason"),
  stopButton: document.querySelector("#stop-button"),
  waveform: document.querySelector("#waveform"),
  progressItems: [...document.querySelectorAll(".progress-list li")],
  reviewHead: document.querySelector("#review-head"),
  sendErrorBanner: document.querySelector("#send-error-banner"),
  messageEditor: document.querySelector("#message-editor"),
  transcriptToggle: document.querySelector("#transcript-toggle"),
  transcriptBox: document.querySelector("#transcript-box"),
  transcriptMode: document.querySelector("#transcript-mode"),
  transcriptOutput: document.querySelector("#transcript-output"),
  reviewActions: document.querySelector("#review-actions"),
  sendingActions: document.querySelector("#sending-actions"),
  sendFailureActions: document.querySelector("#send-failure-actions"),
  sendButton: document.querySelector("#send-button"),
  retrySendButton: document.querySelector("#retry-send-button"),
  copyButton: document.querySelector("#copy-button"),
  copyConfirmation: document.querySelector("#copy-confirmation"),
  recordAgainButton: document.querySelector("#record-again-button"),
  terminalTitle: document.querySelector("#terminal-title"),
  terminalCopy: document.querySelector("#terminal-copy"),
  newMessageButton: document.querySelector("#new-message-button"),
  errorTitle: document.querySelector("#error-title"),
  errorCopy: document.querySelector("#error-copy"),
  simpleErrorIcon: document.querySelector("#simple-error-icon"),
  retryButton: document.querySelector("#retry-button"),
  draftTranscriptMode: document.querySelector("#draft-transcript-mode"),
  draftTranscriptOutput: document.querySelector("#draft-transcript-output"),
  copyTranscriptButton: document.querySelector("#copy-transcript-button"),
  retryDraftButton: document.querySelector("#retry-draft-button"),
  draftRecordAgainButton: document.querySelector("#draft-record-again-button"),
  transcriptCopyConfirmation: document.querySelector("#transcript-copy-confirmation"),
  debugDetails: document.querySelector("#debug-details"),
  debugGrid: document.querySelector("#debug-grid"),
  debugButtons: [...document.querySelectorAll("[data-simulate]")],
};

const viewCopy = {
  ready: ["Ready to record", "Review happens before anything is sent."],
  editing: ["Editing", "Your changes will be sent with the same trace id."],
};

const errorCopy = {
  "err-mic": {
    title: "Microphone access is blocked.",
    body: "Allow microphone access in your browser settings, then retry.",
    icon: "mic",
  },
  "err-empty": {
    title: "We did not catch that.",
    body: "Record again and speak for at least a moment.",
    icon: "alert",
  },
  "err-asr": {
    title: "We could not understand the recording.",
    body: "Record again.",
    icon: "alert",
  },
};

function setHidden(element, hidden) {
  if (element) element.hidden = hidden;
}

function setView(view) {
  state.view = view;
  setHidden(els.composePanel, view !== "ready");
  setHidden(els.micPanel, view !== "mic-pending");
  setHidden(els.recordingPanel, view !== "recording");
  setHidden(els.processingPanel, view !== "processing");
  setHidden(els.reviewPanel, !["review", "editing", "sending", "err-send"].includes(view));
  setHidden(els.successPanel, view !== "success");
  setHidden(els.simpleErrorPanel, !["err-mic", "err-empty", "err-asr"].includes(view));
  setHidden(els.draftErrorPanel, view !== "err-draft");

  renderReviewState();
  renderSimpleError();
  updateDebug({ ui_state: view });
}

function renderReadyCopy() {
  const [label, helper] = viewCopy[state.view] || viewCopy.ready;
  els.stateLabel.textContent = label;
  els.helperCopy.textContent = helper;
}

function renderSimpleError() {
  const data = errorCopy[state.view];
  if (!data) return;
  els.errorTitle.textContent = data.title;
  els.errorCopy.textContent = data.body;
  els.simpleErrorIcon.replaceChildren(errorIcon(data.icon));
}

function errorIcon(kind) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  if (kind === "mic") {
    [
      ["line", { x1: "3", y1: "3", x2: "21", y2: "21" }],
      ["path", { d: "M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V5a3 3 0 0 0-5.94-.6" }],
      ["path", { d: "M17 16.95A7 7 0 0 1 5 12v-1m14 0v1a7 7 0 0 1-.11 1.23" }],
      ["line", { x1: "12", y1: "19", x2: "12", y2: "22" }],
    ].forEach(([tag, attrs]) => svg.append(svgChild(tag, attrs)));
    return svg;
  }
  [
    ["circle", { cx: "12", cy: "12", r: "9" }],
    ["line", { x1: "12", y1: "8", x2: "12", y2: "12.5" }],
    ["line", { x1: "12", y1: "16", x2: "12", y2: "16" }],
  ].forEach(([tag, attrs]) => svg.append(svgChild(tag, attrs)));
  return svg;
}

function svgChild(tag, attrs) {
  const child = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attrs).forEach(([key, value]) => child.setAttribute(key, value));
  return child;
}

function renderReviewState() {
  const view = state.view;
  const sendFailed = view === "err-send";
  setHidden(els.reviewHead, sendFailed);
  setHidden(els.sendErrorBanner, !sendFailed);
  setHidden(els.reviewActions, !["review", "editing"].includes(view));
  setHidden(els.sendingActions, view !== "sending");
  setHidden(els.sendFailureActions, !sendFailed);
}

function modeLabel() {
  return state.mode === "hindi" ? "Hindi" : "Hinglish";
}

function selectMode(mode) {
  state.mode = mode === "hindi" ? "hindi" : "hinglish";
  els.modeButtons.forEach((button) => {
    const selected = button.dataset.mode === state.mode;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-checked", String(selected));
  });
  els.transcriptMode.textContent = `${modeLabel()} transcript`;
  els.draftTranscriptMode.textContent = `${modeLabel()} transcript`;
  els.transcriptBox.dataset.mode = state.mode;
  updateDebug();
}

function resetForModeChange(mode) {
  if (state.view !== "ready") resetFlow();
  selectMode(mode);
}

function renderRuntimeControls(controls = {}) {
  const options = Array.isArray(controls.options) ? controls.options : [];
  els.runtimeSwitch.replaceChildren();
  options.forEach((option) => {
    const button = document.createElement("button");
    button.className = "runtime-button";
    button.type = "button";
    button.role = "radio";
    button.dataset.runtime = option.value;
    button.disabled = !option.enabled;
    button.title = option.disabled_reason || option.label;
    button.setAttribute("aria-checked", "false");

    const name = document.createElement("span");
    name.className = "runtime-name";
    name.textContent = option.label;
    button.append(name);

    if (option.note) {
      const note = document.createElement("span");
      note.className = "runtime-note";
      note.textContent = option.note;
      button.append(note);
    }

    button.addEventListener("click", () => selectModelRuntime(option.value));
    els.runtimeSwitch.append(button);
  });
  selectModelRuntime(controls.selected || "hf_space", { silent: true });
}

function selectModelRuntime(runtime, { silent = false } = {}) {
  const buttons = [...els.runtimeSwitch.querySelectorAll("[data-runtime]")];
  const requested = buttons.find((button) => button.dataset.runtime === runtime);
  const selectedRuntime = requested && !requested.disabled ? runtime : "hf_space";
  state.modelRuntime = selectedRuntime;
  buttons.forEach((button) => {
    const selected = button.dataset.runtime === selectedRuntime;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-checked", String(selected));
  });
  if (!silent) resetFlow();
  renderRuntimePill();
  updateRecordAvailability();
  updateDebug({ model_runtime_changed: !silent });
}

function runtimePillText() {
  if (state.modelRuntime === "modal") {
    const option = selectedRuntimeOption();
    return option?.available === false ? "Modal setup" : "Modal warm";
  }
  if (state.modelRuntime === "hf_personal_space") return "HF personal";
  if (state.modelRuntime === "hf_space") return "HF model";
  return "Voice";
}

function renderRuntimePill() {
  if (els.runtimePillLabel) els.runtimePillLabel.textContent = runtimePillText();
}

function applyTokens(tokens) {
  const root = document.documentElement;
  Object.entries(tokens || {}).forEach(([key, value]) => {
    root.style.setProperty(`--${key.replaceAll("_", "-")}`, value);
  });
}

function applyPacket(packet) {
  state.packet = packet;
  applyTokens(packet.design_tokens);
  els.brandName.textContent = packet.brand_name;
  els.heading.textContent = packet.copy.heading;
  els.subheading.textContent = packet.copy.subheading;
  els.recordButton.querySelector("span").textContent = packet.copy.record_cta;
  selectMode(packet.locale_defaults.default_speech_mode);
  renderRuntimeControls(packet.runtime_controls);
  renderReadyCopy();
  updateRecordAvailability();
  updateDebug({ packet_loaded: true });
}

async function api(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error || data.detail || data.blocker || "Request failed");
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const value = String(reader.result || "");
      resolve(value.includes(",") ? value.split(",", 2)[1] : value);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

function selectedRuntimeOption() {
  const options = state.packet?.runtime_controls?.options || [];
  return options.find((option) => option.value === state.modelRuntime) || null;
}

function recordDisabledReason() {
  if (state.recorder?.state === "recording") return "";
  const option = selectedRuntimeOption();
  if (option && option.available === false) {
    return option.disabled_reason || "Selected model runtime is not available.";
  }
  return "";
}

function updateRecordAvailability() {
  if (!state.packet) return;
  const reason = recordDisabledReason();
  els.recordButton.disabled = Boolean(reason);
  els.recordDisabledReason.hidden = !reason;
  els.recordDisabledReason.textContent = reason ? `Why it's disabled: ${reason}` : "";
  updateDebug({ record_disabled_reason: reason || null });
}

function visitorNoticeShown() {
  return false;
}

function setProgressStep(activeIndex) {
  els.progressItems.forEach((item, index) => {
    item.classList.toggle("is-done", index < activeIndex);
    item.classList.toggle("is-active", index === activeIndex);
  });
}

async function mirrorPendingWork(requestPromise) {
  const checkpoints = [900, 2400];
  for (let index = 0; index < checkpoints.length; index += 1) {
    const result = await Promise.race([
      requestPromise.then(() => "done", () => "done"),
      sleep(checkpoints[index]).then(() => "pending"),
    ]);
    if (result === "done") return;
    setProgressStep(index + 1);
  }
}

function buildWaveform() {
  const bars = [];
  for (let index = 0; index < 30; index += 1) {
    const bar = document.createElement("span");
    bar.style.animationDelay = `${(index * 0.045).toFixed(3)}s`;
    bars.push(bar);
  }
  els.waveform.replaceChildren(...bars);
}

async function startRecording() {
  if (recordDisabledReason()) {
    updateRecordAvailability();
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
    showError("err-mic");
    return;
  }
  state.transcriptOpen = false;
  setView("mic-pending");
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.chunks = [];
    state.recorder = new MediaRecorder(stream);
    state.recorder.ondataavailable = (event) => {
      if (event.data.size > 0) state.chunks.push(event.data);
    };
    state.recorder.onstop = () => finishRecording(stream);
    state.startedAt = Date.now();
    state.recorder.start();
    setView("recording");
  } catch (_error) {
    updateRecordAvailability();
    showError("err-mic");
  }
}

function stopRecording() {
  if (state.recorder?.state === "recording") {
    els.stopButton.disabled = true;
    state.recorder.stop();
  }
}

async function finishRecording(stream) {
  stream.getTracks().forEach((track) => track.stop());
  const durationMs = Date.now() - state.startedAt;
  const mimeType = state.recorder?.mimeType || "audio/webm";
  const blob = new Blob(state.chunks, { type: mimeType });
  state.recorder = null;
  els.stopButton.disabled = false;
  updateRecordAvailability();
  if (durationMs < 700 || blob.size < 128) {
    showError("err-empty");
    return;
  }
  const audioBase64 = await blobToBase64(blob);
  await processRecording({
    duration_ms: durationMs,
    audio_size_bytes: blob.size,
    audio_mime: blob.type || mimeType,
    audio_base64: audioBase64,
  });
}

async function processRecording(extra = {}) {
  try {
    setView("processing");
    setProgressStep(0);
    const requestPromise = api("/api/process", {
      speech_mode: state.mode,
      model_runtime: state.modelRuntime,
      visitor_notice_shown: visitorNoticeShown(),
      ...extra,
    });
    await mirrorPendingWork(requestPromise);
    const result = await requestPromise;
    showReviewResult(result);
  } catch (error) {
    if (extra.simulate === "text_failure") {
      state.transcript = state.transcript || "Namaste, mujhe metime.to ke baare mein founders se baat karni hai.";
      showDraftError(error.message);
      return;
    }
    showError("err-asr", error.message);
  }
}

async function processTextDraft() {
  if (!state.transcript) {
    resetFlow();
    return;
  }
  try {
    setView("processing");
    setProgressStep(2);
    const result = await api("/api/text-smoke", {
      speech_mode: state.mode,
      model_runtime: state.modelRuntime,
      transcript: state.transcript,
      visitor_notice_shown: visitorNoticeShown(),
    });
    showReviewResult(result);
  } catch (error) {
    showDraftError(error.message);
  }
}

function showReviewResult(result) {
  state.lastTrace = result.trace;
  state.transcript = result.transcript || "";
  state.modelMessage = result.model_message_en || "";
  els.messageEditor.value = state.modelMessage;
  els.transcriptOutput.textContent = state.transcript;
  els.draftTranscriptOutput.textContent = state.transcript;
  setProgressStep(3);
  renderTranscript();
  setView("review");
  updateDebug({ transcript: state.transcript });
}

function showDraftError(detail = "") {
  els.draftTranscriptOutput.textContent = state.transcript || "Transcript unavailable.";
  renderTranscript();
  setView("err-draft");
  updateDebug({ draft_error: detail || null });
}

async function sendMessage() {
  setView("sending");
  try {
    const result = await api("/api/send", {
      site_id: state.packet.site_id,
      contact_email: state.packet.contact_email,
      model_message_en: state.modelMessage,
      final_message_en: els.messageEditor.value,
      trace_id: state.lastTrace?.trace_id,
      simulate: state.simulateNextSendFailure ? "send_failure" : null,
    });
    state.simulateNextSendFailure = false;
    els.terminalTitle.textContent = "Message sent.";
    els.terminalCopy.textContent = result.visitor_copy || "Thanks. The team will get back to you.";
    setView("success");
    updateDebug({ delivery: "demo_ledger", send_result: result.status });
  } catch (error) {
    state.simulateNextSendFailure = false;
    setView("err-send");
    updateDebug({ send_error: error.message });
  }
}

function showError(kind, detail = "") {
  const data = errorCopy[kind] || errorCopy["err-asr"];
  els.errorTitle.textContent = data.title;
  els.errorCopy.textContent = detail ? `${data.body} ${detail}` : data.body;
  els.simpleErrorIcon.replaceChildren(errorIcon(data.icon));
  setView(kind);
}

function resetFlow() {
  state.chunks = [];
  state.recorder = null;
  state.startedAt = 0;
  state.lastTrace = null;
  state.transcript = "";
  state.modelMessage = "";
  state.transcriptOpen = false;
  state.simulateNextSendFailure = false;
  els.messageEditor.value = "";
  els.transcriptOutput.textContent = "";
  els.draftTranscriptOutput.textContent = "";
  els.copyConfirmation.hidden = true;
  els.transcriptCopyConfirmation.hidden = true;
  renderTranscript();
  renderReadyCopy();
  setView("ready");
  updateRecordAvailability();
}

function renderTranscript() {
  els.transcriptToggle.setAttribute("aria-expanded", String(state.transcriptOpen));
  els.transcriptToggle.querySelector("span").textContent = state.transcriptOpen ? "Hide transcript" : "Show transcript";
  els.transcriptBox.hidden = !state.transcriptOpen;
  els.transcriptOutput.textContent = state.transcript || "";
  els.draftTranscriptOutput.textContent = state.transcript || "";
  els.transcriptMode.textContent = `${modeLabel()} transcript`;
  els.draftTranscriptMode.textContent = `${modeLabel()} transcript`;
  els.transcriptBox.dataset.mode = state.mode;
}

async function copyText(value, confirmationElement, copiedLabel = null) {
  await navigator.clipboard.writeText(value || "");
  confirmationElement.hidden = false;
  if (copiedLabel) copiedLabel.textContent = "Copied";
  window.setTimeout(() => {
    confirmationElement.hidden = true;
    if (copiedLabel) copiedLabel.textContent = "Copy message";
  }, 1200);
}

function debugRows(extra = {}) {
  const runtime = state.packet?.provenance || {};
  const trace = state.lastTrace || {};
  return {
    "site id": state.packet?.site_id || "loading",
    "packet": state.packet?.schema_version || "loading",
    "speech mode": state.mode,
    "selected runtime": state.modelRuntime,
    "runtime allowed": String(Boolean(state.packet?.runtime_controls?.allow_switch)),
    "request runtime": trace.model_runtime || state.modelRuntime || "unknown",
    "server default": runtime.model_runtime || "unknown",
    "backend": trace.model_backend || runtime.model_backend || "unknown",
    "fallback": String(trace.fallback_used ?? runtime.fallback_used ?? "unknown"),
    "trace id": trace.trace_id || "none",
    "timings": JSON.stringify(trace.timings_ms || {}),
    "eval retention": String(Boolean(state.packet?.retention?.retain_raw_audio_for_eval)),
    "asr model": trace.asr_model_id || runtime.asr_model_id || "unknown",
    "text model": trace.text_model_id || runtime.text_model_id || "unknown",
    ...extra,
  };
}

function updateDebug(extra = {}) {
  const rows = debugRows(extra);
  const fragments = Object.entries(rows).map(([key, value]) => {
    const row = document.createElement("div");
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = key;
    dd.textContent = String(value ?? "");
    row.append(dt, dd);
    return row;
  });
  els.debugGrid.replaceChildren(...fragments);
}

function wireEvents() {
  els.modeButtons.forEach((button) => {
    button.addEventListener("click", () => resetForModeChange(button.dataset.mode));
  });
  els.recordButton.addEventListener("click", startRecording);
  els.stopButton.addEventListener("click", stopRecording);
  els.messageEditor.addEventListener("input", () => {
    state.view = "editing";
    renderReviewState();
    updateDebug({ ui_state: "editing" });
  });
  els.transcriptToggle.addEventListener("click", () => {
    state.transcriptOpen = !state.transcriptOpen;
    renderTranscript();
  });
  els.sendButton.addEventListener("click", sendMessage);
  els.retrySendButton.addEventListener("click", sendMessage);
  els.recordAgainButton.addEventListener("click", resetFlow);
  els.draftRecordAgainButton.addEventListener("click", resetFlow);
  els.newMessageButton.addEventListener("click", resetFlow);
  els.retryButton.addEventListener("click", resetFlow);
  els.retryDraftButton.addEventListener("click", processTextDraft);
  els.copyButton.addEventListener("click", () => copyText(els.messageEditor.value, els.copyConfirmation, els.copyButton));
  els.copyTranscriptButton.addEventListener("click", () => copyText(state.transcript, els.transcriptCopyConfirmation));
  els.debugButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      const simulation = button.dataset.simulate;
      if (simulation === "mic-denied") showError("err-mic");
      if (simulation === "empty-audio") showError("err-empty");
      if (simulation === "asr-failure") await processRecording({ simulate: "asr_failure" });
      if (simulation === "text-failure") {
        state.transcript = "Namaste, mujhe metime.to ke baare mein founders se baat karni hai.";
        await processRecording({ simulate: "text_failure", transcript: state.transcript });
      }
      if (simulation === "send-failure") {
        state.simulateNextSendFailure = true;
        if (!state.lastTrace) {
          state.lastTrace = { trace_id: "debug-send-failure" };
          state.modelMessage = "Hello metime.to team,\n\nPlease contact me about metime.to.\n\nThank you.";
          state.transcript = "Hi, main metime.to ke baare mein founders se connect karna chahta hoon.";
          els.messageEditor.value = state.modelMessage;
        }
        await sendMessage();
      }
    });
  });
}

async function boot() {
  buildWaveform();
  wireEvents();
  updateDebug();
  const packet = await fetch("/api/packet").then((response) => response.json());
  applyPacket(packet);
  setView("ready");
}

boot().catch((error) => {
  els.errorTitle.textContent = "Widget could not start.";
  els.errorCopy.textContent = error.message;
  els.simpleErrorIcon.replaceChildren(errorIcon("alert"));
  setView("err-asr");
});
