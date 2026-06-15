const state = {
  packet: null,
  mode: "hinglish",
  recorder: null,
  chunks: [],
  startedAt: 0,
  lastTrace: null,
  modelMessage: "",
  modelRuntime: "hf_space",
  simulateNextSendFailure: false,
};

const els = {
  brandName: document.querySelector("#brand-name"),
  contactEmail: document.querySelector("#contact-email"),
  heading: document.querySelector("#widget-heading"),
  subheading: document.querySelector("#widget-subheading"),
  evalNotice: document.querySelector("#eval-notice"),
  segments: [...document.querySelectorAll(".segment")],
  runtimeSegmented: document.querySelector("#runtime-segmented"),
  recorderPanel: document.querySelector(".recorder-panel"),
  recordButton: document.querySelector("#record-button"),
  recordDisabledReason: document.querySelector("#record-disabled-reason"),
  stateLabel: document.querySelector("#state-label"),
  helperCopy: document.querySelector("#helper-copy"),
  processingPanel: document.querySelector("#processing-panel"),
  progressItems: [...document.querySelectorAll(".progress-list li")],
  reviewPanel: document.querySelector("#review-panel"),
  messageEditor: document.querySelector("#message-editor"),
  sendButton: document.querySelector("#send-button"),
  recordAgainButton: document.querySelector("#record-again-button"),
  transcriptOutput: document.querySelector("#transcript-output"),
  terminalPanel: document.querySelector("#terminal-panel"),
  terminalTitle: document.querySelector("#terminal-title"),
  terminalCopy: document.querySelector("#terminal-copy"),
  newMessageButton: document.querySelector("#new-message-button"),
  errorPanel: document.querySelector("#error-panel"),
  errorTitle: document.querySelector("#error-title"),
  errorCopy: document.querySelector("#error-copy"),
  retryButton: document.querySelector("#retry-button"),
  copyButton: document.querySelector("#copy-button"),
  debugOutput: document.querySelector("#debug-output"),
  debugButtons: [...document.querySelectorAll("[data-simulate]")],
};

const stateCopy = {
  idle: ["Ready to record", "Review happens before anything is sent."],
  permissionPending: ["Waiting for microphone permission", "Your browser will ask for microphone access."],
  recording: ["Recording", "Speak naturally. Stop when you are done."],
  processing: ["Processing your message", "We are preparing a draft for review."],
  review: ["Draft ready", "Edit the English message before sending."],
  editing: ["Editing", "Your changes will be sent with the same trace id."],
  sending: ["Sending", "Saving to the demo ledger fallback."],
  success: ["Message saved", "The demo ledger fallback was used."],
  micDenied: ["Microphone access is blocked", "Allow microphone access in your browser settings, then retry."],
  emptyAudio: ["We did not catch that", "Record again and speak for at least a moment."],
  asrFailure: ["We could not understand the recording", "Record again to retry the deterministic ASR step."],
  textFailure: ["Could not draft the message", "You can edit the transcript or retry."],
  sendFailure: ["Could not send", "Your message is still here. Retry send or copy it."],
};

function setAppState(name) {
  const [label, helper] = stateCopy[name] || stateCopy.idle;
  els.stateLabel.textContent = label;
  els.helperCopy.textContent = helper;
  els.recorderPanel.classList.toggle("is-recording", name === "recording");
  updateDebug({ ui_state: name });
}

function setPanels({ processing = false, review = false, terminal = false, error = false } = {}) {
  els.processingPanel.hidden = !processing;
  els.reviewPanel.hidden = !review;
  els.terminalPanel.hidden = !terminal;
  els.errorPanel.hidden = !error;
}

function updateDebug(extra = {}) {
  if (!state.packet) return;
  const runtime = state.packet.provenance || {};
  const provenance = {
    site_id: state.packet.site_id,
    brand_name: state.packet.brand_name,
    contact_email: state.packet.contact_email,
    packet_version: state.packet.schema_version,
    speech_mode: state.mode,
    selected_model_runtime: state.modelRuntime,
    runtime_switch_allowed: Boolean(state.packet.runtime_controls?.allow_switch),
    asr_language_hint: state.mode === "hindi" || state.mode === "hinglish" ? "hi-IN" : "hi-IN",
    asr_model_id: runtime.asr_model_id,
    text_model_id: runtime.text_model_id,
    model_runtime: runtime.model_runtime,
    model_backend: runtime.model_backend,
    model_artifact_format: runtime.model_artifact_format,
    quantization: runtime.quantization,
    mock_mode: runtime.mock_mode,
    fallback_used: runtime.fallback_used,
    audio_eval_consent: state.packet.audio_eval_consent,
    visitor_notice_shown: Boolean(state.packet.audio_eval_notice),
    raw_audio_retained: Boolean(state.packet.retention.retain_raw_audio_for_eval),
    trace_id: state.lastTrace?.trace_id || null,
    timings_ms: state.lastTrace?.timings_ms || {},
    ...extra,
  };
  els.debugOutput.textContent = JSON.stringify(provenance, null, 2);
}

function applyTokens(tokens) {
  const root = document.documentElement;
  Object.entries(tokens).forEach(([key, value]) => {
    root.style.setProperty(`--${key.replaceAll("_", "-")}`, value);
  });
}

function applyPacket(packet) {
  state.packet = packet;
  applyTokens(packet.design_tokens);
  els.brandName.textContent = packet.brand_name;
  els.contactEmail.textContent = packet.contact_email;
  els.heading.textContent = packet.copy.heading;
  els.subheading.textContent = packet.copy.subheading;
  els.recordButton.textContent = packet.copy.record_cta;
  els.sendButton.textContent = packet.copy.send_cta;
  els.evalNotice.textContent = packet.audio_eval_notice;
  els.evalNotice.hidden = !packet.audio_eval_consent;
  state.mode = packet.locale_defaults.default_speech_mode;
  state.modelRuntime = packet.runtime_controls?.selected || packet.provenance?.model_runtime || "hf_space";
  selectMode(state.mode);
  renderRuntimeControls(packet.runtime_controls);
  updateDebug({ packet_loaded: true });
}

function selectMode(mode) {
  state.mode = mode;
  els.segments.forEach((button) => {
    const selected = button.dataset.mode === mode;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-checked", String(selected));
  });
  updateDebug();
}

function renderRuntimeControls(controls = {}) {
  if (!els.runtimeSegmented) return;
  const options = Array.isArray(controls.options) ? controls.options : [];
  els.runtimeSegmented.replaceChildren();
  options.forEach((option) => {
    const button = document.createElement("button");
    button.className = "segment runtime-segment";
    button.type = "button";
    button.role = "radio";
    button.dataset.runtime = option.value;
    button.disabled = !option.enabled;
    button.title = option.enabled ? option.disabled_reason || option.label : "Enable VCW_ALLOW_RUNTIME_SWITCH=1 to test this runtime";

    const label = document.createElement("span");
    label.className = "segment-label";
    label.textContent = option.label;
    button.append(label);

    if (option.note) {
      const note = document.createElement("span");
      note.className = "segment-note";
      note.textContent = option.note;
      button.append(note);
    }

    button.addEventListener("click", () => selectModelRuntime(option.value));
    els.runtimeSegmented.append(button);
  });
  selectModelRuntime(state.modelRuntime, { silent: true });
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
  if (els.recordDisabledReason) {
    els.recordDisabledReason.hidden = !reason;
    els.recordDisabledReason.textContent = reason ? `Why it's disabled: ${reason}` : "";
  }
  updateDebug({ record_disabled_reason: reason || null });
}

function selectModelRuntime(runtime, { silent = false } = {}) {
  const buttons = [...els.runtimeSegmented.querySelectorAll("[data-runtime]")];
  const requested = buttons.find((button) => button.dataset.runtime === runtime);
  const enabledRequested = requested && !requested.disabled;
  state.modelRuntime = enabledRequested ? runtime : "hf_space";
  buttons.forEach((button) => {
    const selected = button.dataset.runtime === state.modelRuntime;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-checked", String(selected));
  });
  if (!silent) resetFlow();
  updateRecordAvailability();
  updateDebug({ model_runtime_changed: !silent });
}

async function api(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || data.detail || data.blocker || "Request failed");
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

function setProgressStep(activeIndex) {
  els.progressItems.forEach((item, index) => {
    item.classList.toggle("is-done", index < activeIndex);
    item.classList.toggle("is-active", index === activeIndex);
  });
}

function startProcessing() {
  setPanels({ processing: true });
  setAppState("processing");
  els.progressItems.forEach((item) => item.classList.remove("is-active", "is-done"));
  setProgressStep(0);
}

function finishProcessing() {
  els.progressItems.forEach((item) => {
    item.classList.remove("is-active");
    item.classList.add("is-done");
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

async function startRecording() {
  if (recordDisabledReason()) {
    updateRecordAvailability();
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
    showError("micDenied");
    return;
  }
  setPanels();
  setAppState("permissionPending");
  els.recordButton.disabled = true;
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
    els.recordButton.disabled = false;
    els.recordButton.textContent = state.packet.copy.stop_cta;
    setAppState("recording");
  } catch (_error) {
    updateRecordAvailability();
    showError("micDenied");
  }
}

function stopRecording() {
  if (state.recorder?.state === "recording") {
    els.recordButton.disabled = true;
    state.recorder.stop();
  }
}

async function finishRecording(stream) {
  stream.getTracks().forEach((track) => track.stop());
  const durationMs = Date.now() - state.startedAt;
  const blob = new Blob(state.chunks, { type: state.recorder?.mimeType || "audio/webm" });
  state.recorder = null;
  els.recordButton.textContent = state.packet.copy.record_cta;
  updateRecordAvailability();
  if (durationMs < 700 || blob.size < 128) {
    showError("emptyAudio");
    return;
  }
  const audioBase64 = await blobToBase64(blob);
  await processRecording({
    duration_ms: durationMs,
    audio_size_bytes: blob.size,
    audio_mime: blob.type || state.recorder?.mimeType || "audio/webm",
    audio_base64: audioBase64,
  });
}

async function processRecording(extra = {}) {
  try {
    startProcessing();
    const requestPromise = api("/api/process", {
      speech_mode: state.mode,
      model_runtime: state.modelRuntime,
      visitor_notice_shown: !els.evalNotice.hidden,
      ...extra,
    });
    await mirrorPendingWork(requestPromise);
    const result = await requestPromise;
    finishProcessing();
    state.lastTrace = result.trace;
    state.modelMessage = result.model_message_en;
    els.messageEditor.value = result.model_message_en;
    els.transcriptOutput.textContent = result.transcript;
    setPanels({ review: true });
    setAppState("review");
    updateDebug({ transcript: result.transcript });
  } catch (error) {
    showError(extra.simulate === "text_failure" ? "textFailure" : "asrFailure", error.message);
  }
}

async function sendMessage() {
  setAppState("sending");
  els.sendButton.disabled = true;
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
    setPanels({ terminal: true });
    setAppState("success");
    updateDebug({ delivery: "demo_ledger", send_result: result.status });
  } catch (error) {
    state.simulateNextSendFailure = false;
    showError("sendFailure", error.message);
  } finally {
    els.sendButton.disabled = false;
  }
}

function showError(kind, detail = "") {
  const titles = {
    micDenied: "Microphone access is blocked.",
    emptyAudio: "We did not catch that.",
    asrFailure: "We could not understand the recording.",
    textFailure: "We got the transcript but could not draft the message.",
    sendFailure: "Could not send. Your message is still here.",
  };
  const actions = {
    micDenied: "Allow microphone access in your browser settings, then retry.",
    emptyAudio: "Record again.",
    asrFailure: "Record again.",
    textFailure: "Edit the draft or retry.",
    sendFailure: "Retry send or copy message.",
  };
  els.errorTitle.textContent = titles[kind] || "Could not continue.";
  els.errorCopy.textContent = detail ? `${actions[kind]} ${detail}` : actions[kind];
  els.copyButton.hidden = kind !== "sendFailure";
  setPanels({ review: kind === "sendFailure", error: true });
  setAppState(kind);
}

function resetFlow() {
  state.chunks = [];
  state.recorder = null;
  state.startedAt = 0;
  state.lastTrace = null;
  state.modelMessage = "";
  state.simulateNextSendFailure = false;
  els.messageEditor.value = "";
  els.transcriptOutput.textContent = "";
  els.recordButton.textContent = state.packet.copy.record_cta;
  setPanels();
  setAppState("idle");
  updateRecordAvailability();
}

function wireEvents() {
  els.segments.forEach((button) => {
    button.addEventListener("click", () => selectMode(button.dataset.mode));
  });
  els.recordButton.addEventListener("click", () => {
    if (state.recorder?.state === "recording") stopRecording();
    else startRecording();
  });
  els.messageEditor.addEventListener("input", () => setAppState("editing"));
  els.sendButton.addEventListener("click", sendMessage);
  els.recordAgainButton.addEventListener("click", resetFlow);
  els.newMessageButton.addEventListener("click", resetFlow);
  els.retryButton.addEventListener("click", () => {
    if (els.copyButton.hidden) resetFlow();
    else sendMessage();
  });
  els.copyButton.addEventListener("click", async () => {
    await navigator.clipboard.writeText(els.messageEditor.value);
    els.copyButton.textContent = "Copied";
    window.setTimeout(() => {
      els.copyButton.textContent = "Copy message";
    }, 1200);
  });
  els.debugButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      const simulation = button.dataset.simulate;
      if (simulation === "mic-denied") showError("micDenied");
      if (simulation === "empty-audio") showError("emptyAudio");
      if (simulation === "asr-failure") await processRecording({ simulate: "asr_failure" });
      if (simulation === "text-failure") await processRecording({ simulate: "text_failure" });
      if (simulation === "send-failure") {
        state.simulateNextSendFailure = true;
        if (!state.lastTrace) {
          state.lastTrace = { trace_id: "debug-send-failure" };
          state.modelMessage = "Hello metime.to team,\n\nPlease contact me about metime.to.\n\nThank you.";
          els.messageEditor.value = state.modelMessage;
        }
        await sendMessage();
      }
    });
  });
}

async function boot() {
  wireEvents();
  const packet = await fetch("/api/packet").then((response) => response.json());
  applyPacket(packet);
  setAppState("idle");
}

boot().catch((error) => {
  els.errorTitle.textContent = "Widget could not start.";
  els.errorCopy.textContent = error.message;
  setPanels({ error: true });
});
