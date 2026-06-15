/* ============================================================
   APP — state store, backend wiring, region rendering
   ============================================================ */

/* derived selectors (used by component render fns) */
function currentRequest(s) {
  return s.requests.find(r => r.id === s.selectedId) || null;
}
function currentVenue(s) {
  return Data.venues.find(v => v.id === s.venueId) || Data.venues[0];
}
function activeConversation(s) {
  return (s.conversations && s.conversations[s.selectedId]) || null;
}
function activeTrace(s) {
  return (s.traces && s.traces[s.selectedId]) || null;
}

/* app clock — browser-local current day for masthead and calendar */
function currentDay(now = new Date()) {
  return new Date(now.getFullYear(), now.getMonth(), now.getDate());
}
function formatMastheadDate(now = new Date()) {
  return `${now.getDate()} ${CAL_MON[now.getMonth()].slice(0, 3)} ${now.getFullYear()}`;
}
function formatMastheadTime(now = new Date()) {
  let hour = now.getHours();
  const suffix = hour >= 12 ? 'PM' : 'AM';
  hour = hour % 12 || 12;
  return `${String(hour).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')} ${suffix}`;
}
function refreshClock() {
  const now = new Date();
  Data.org.dateLabel = formatMastheadDate(now);
  Data.org.timeLabel = formatMastheadTime(now);
  const nextToday = currentDay(now);
  if (!sameDay(state.today, nextToday)) {
    state.today = nextToday;
    updateHeaderStats();
  }
  renderTopBar();
}
const APP_TODAY = currentDay();
const addDays = (d, n) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
const slotIdxOf = label => (label && label.trim().startsWith('8 AM')) ? 0 : 1;
const TRY_ME_ID = 'try-me-live-model';

function tryMeRequest() {
  const rawMessage = 'Hi, can we book South Field tomorrow afternoon for a cricket match with 12 players? Budget is around Rs 5500.';
  return {
    id: TRY_ME_ID,
    name: 'TRY ME',
    players: 12,
    type: 'Live demo',
    ago: 'Click to start',
    day: 'Tomorrow',
    slot: '2 PM – 6 PM',
    phone: '+91 90000 00000',
    activity: 'Cricket',
    date: 'Tomorrow',
    isNew: true,
    status: 'demo_idle',
    badge: 'Live demo',
    replyDraft: '',
    rawMessage,
    chatDraft: rawMessage,
    venueId: 'south',
    isTryMe: true,
    modelBacked: true,
  };
}

function withTryMeRequest(requests) {
  return [tryMeRequest(), ...requests.filter(req => req.id !== TRY_ME_ID)];
}

function isModelBackedRequest(req) {
  return !!req?.modelBacked;
}

function modelBookingFromConversation(conversation) {
  return conversation?.model_extraction?.booking || null;
}

function titleCaseWords(value) {
  return String(value || '').replace(/\b\w/g, ch => ch.toUpperCase());
}

function slotLabelFromModel(value) {
  const text = String(value || '').toLowerCase();
  if (text.includes('afternoon') || text.includes('2') || text.includes('6')) return '2 PM – 6 PM';
  if (text.includes('morning') || text.includes('8') || text.includes('12')) return '8 AM – 12 PM';
  return normalizedSlotLabel(value || '');
}

function applyModelBookingToState(req, conversation) {
  const booking = modelBookingFromConversation(conversation);
  if (!booking) return;

  if (booking.sport) req.activity = titleCaseWords(booking.sport);
  if (booking.players) req.players = Number(booking.players);
  if (booking.customer?.name) req.name = booking.customer.name;
  if (booking.customer?.phone) req.phone = booking.customer.phone;

  const dateText = String(booking.date_text || '').toLowerCase();
  if (dateText.includes('today')) req.day = 'Today';
  else if (dateText.includes('tomorrow')) req.day = 'Tomorrow';
  if (req.day) req.date = req.day;

  const slot = slotLabelFromModel(booking.time_window);
  if (slot) req.slot = slot;

  const venueName = String(booking.venue_preference || '').toLowerCase();
  const venue = Data.venues.find(item => String(item.name || '').toLowerCase() === venueName)
    || Data.venues.find(item => venueName && String(item.name || '').toLowerCase().includes(venueName))
    || currentVenue(state);
  if (venue?.id) req.venueId = venue.id;

  if (req.id !== state.selectedId) return;
  state.venueId = req.venueId || state.venueId;
  state.players = Number(req.players || 0);
  state.slot = req.slot || state.slot;
  state.slotIndex = slotIdxOf(state.slot);
  state.selDate = req.day === 'Today' ? new Date(state.today) : addDays(state.today, 1);
  state.dateLabel = fmtDateLabel(state.selDate, state.today);
  state.price = Number(booking.budget?.amount || 0) || venue?.suggested || state.price;
}

function shouldAutoSyncSelectedRequest() {
  return !isModelBackedRequest(currentRequest(state));
}

/* baseline (pre-edit) value of an editable field */
function fieldBase(key) {
  const req = currentRequest(state);
  if (key === 'Activity') return req ? req.activity : '';
  if (key === 'Date') return state.dateLabel;
  if (key === 'Slot') return state.slot;
  if (key === 'Players') return String(state.players);
  return '';
}

/* ───────────── state ───────────── */
const state = {
  requests: withTryMeRequest(Data.requests.slice()),
  selectedId: Data.requests[0]?.id || '',
  venueId: Data.venues[0]?.id || '',
  venueOpen: false,
  price: Data.venues[0]?.suggested || 0,
  players: Data.requests[0]?.players || 0,
  slot: Data.requests[0]?.slot || '8 AM – 12 PM',
  slotIndex: slotIdxOf(Data.requests[0]?.slot),
  today: APP_TODAY,
  selDate: addDays(APP_TODAY, 1),
  dateLabel: fmtDateLabel(addDays(APP_TODAY, 1), APP_TODAY),
  teamA: 'Bangalore Bat Kings',
  teamB: '',
  fieldEdits: {},
  editingField: null,
  slotDraft: null,
  notes: '',
  backendReady: false,
  backendError: '',
  syncStatus: 'idle',
  conversations: {},
  traces: {},
  modelRuns: {},
  modalStatus: null,
  demoChatDraft: '',
  requestSeq: 0,
  demoReloading: false,
  confirmedTodayBase: Data.stats.confirmedToday || 0,
};

/* ───────────── backend adapter ───────────── */
function normalizedSlotLabel(label) {
  return String(label || '').replace(/ - /g, ' – ');
}

function firstSlotForVenue(venue, slotDefs) {
  const entries = Object.entries(venue.slots || {});
  const [slotId, inventory] = entries[0] || ['morning', { rate: venue.suggested || 0 }];
  const slot = slotDefs.find(item => item.id === slotId) || slotDefs[0] || {};
  return { slotId, inventory, slot };
}

function applyBootstrap(payload) {
  const slotDefs = payload.slots || [];
  Data.slots = slotDefs.slice();
  Data.bookings = (payload.bookings || []).map(item => ({ ...item }));
  Data.org.channel = payload.runtime?.channel_label || 'WhatsApp simulator';
  Data.org.channelState = payload.runtime?.channel_status === 'provider-error' ? 'Provider error' : 'Simulator';
  Data.stats.pending = Number(payload.runtime?.pending_count || 0);
  Data.stats.confirmedToday = Number(payload.runtime?.confirmed_today || Data.stats.confirmedToday || 0);
  state.confirmedTodayBase = Data.stats.confirmedToday;
  Data.venues = (payload.venues || []).map(venue => {
    const first = firstSlotForVenue(venue, slotDefs);
    return {
      id: venue.id,
      name: venue.name,
      slot: normalizedSlotLabel(first.slot.label || '8 AM - 12 PM'),
      surface: venue.surface || 'Grass',
      type: venue.grass_type || venue.type || 'Natural',
      suggested: Number(first.inventory.rate || 0),
      slots: venue.slots || {},
      grass_type: venue.grass_type || venue.type || '',
    };
  });
  Data.integrations = (payload.integrations || []).map(item => ({
    id: item.id,
    name: item.label,
    icon: item.id === 'video' ? 'video' : 'cric',
    s1: item.copy || item.state,
    s2: item.state === 'disabled' ? 'Unavailable' : 'Disabled',
  }));
  state.requests = withTryMeRequest((payload.requests || []).map(requestFromBackend));
  updateHeaderStats();
  loadRequest(payload.decision?.selected_request_id || Data.requests[0]?.id || state.requests.find(req => !req.isTryMe)?.id || '');
  state.backendReady = true;
  state.backendError = '';
}

function resetRuntimeState() {
  state.conversations = {};
  state.traces = {};
  state.modelRuns = {};
  state.demoChatDraft = '';
  state.syncStatus = 'idle';
  state.backendError = '';
  state.fieldEdits = {};
  state.editingField = null;
  state.slotDraft = null;
  state.notes = '';
  state.requestSeq += 1;
}

function updatePendingStat() {
  Data.stats.pending = state.requests.filter(req => req.isNew && !req.isTryMe).length;
}

function bookingDateTextFor(date) {
  if (sameDay(date, state.today)) return 'today';
  if (sameDay(date, addDays(state.today, 1))) return 'tomorrow';
  if (sameDay(date, addDays(state.today, -1))) return 'yesterday';
  return isoDate(date);
}

function bookingOccupiesSlot(booking) {
  const status = String(booking?.status || '').toLowerCase();
  return status.includes('confirmed') || status.includes('pending');
}

function syntheticSlotOccupied(date, slotIndex, venueIndex) {
  const k = date.getFullYear() * 366
    + (date.getMonth() + 1) * 32
    + date.getDate() * 2
    + slotIndex
    + venueIndex * 17;
  return calSeed(k) > 0.5;
}

function computeWeeklyOccupancy() {
  const venues = Data.venues || [];
  const slots = Data.slots?.length ? Data.slots : [{ id: 'morning' }, { id: 'afternoon' }];
  let occupied = 0;
  let total = 0;
  for (let day = 0; day < 7; day++) {
    const date = addDays(state.today, day);
    const dateText = bookingDateTextFor(date);
    venues.forEach((venue, venueIndex) => {
      slots.forEach((slot, slotIndex) => {
        total += 1;
        const explicit = (Data.bookings || []).filter(item =>
          item.venue_id === venue.id &&
          item.slot_id === slot.id &&
          String(item.date_text || '').toLowerCase() === dateText);
        if (explicit.length ? explicit.some(bookingOccupiesSlot) : syntheticSlotOccupied(date, slotIndex, venueIndex)) {
          occupied += 1;
        }
      });
    });
  }
  return total ? Math.round((occupied / total) * 100) : 0;
}

function confirmedTodayDelta() {
  return (Data.bookings || []).filter(item =>
    String(item.id || '').startsWith('ui-') &&
    String(item.status || '').toLowerCase().includes('confirmed')).length;
}

function updateHeaderStats() {
  updatePendingStat();
  Data.stats.confirmedToday = Number(state.confirmedTodayBase || 0) + confirmedTodayDelta();
  Data.stats.occupancyWeek = computeWeeklyOccupancy();
  Data.stats.occupancy = Data.stats.occupancyWeek;
}

function selectedDateText() {
  if (sameDay(state.selDate, state.today)) return 'today';
  if (sameDay(state.selDate, addDays(state.today, 1))) return 'tomorrow';
  return isoDate(state.selDate);
}

function selectedSlotId() {
  return Data.slots[state.slotIndex]?.id || (state.slotIndex === 1 ? 'afternoon' : 'morning');
}

function addTemporaryBooking(req, conversation) {
  if (conversation?.terminal_state !== 'confirmed_simulated') return;
  const bookingId = `ui-${req.id}-${selectedDateText()}-${selectedSlotId()}`;
  Data.bookings = Data.bookings.filter(item => item.id !== bookingId);
  Data.bookings.push({
    id: bookingId,
    venue_id: state.venueId,
    slot_id: selectedSlotId(),
    date_text: selectedDateText(),
    status: 'confirmed_simulated',
    team_id: req.id,
    players: Number(effField(state, 'Players', String(state.players))) || req.players,
  });
  updateHeaderStats();
}

function requestFromBackend(req) {
  const [venueId, slotId] = String(req.requested_slot_id || '').split(':');
  const venue = Data.venues.find(item => item.id === venueId) || Data.venues[0] || {};
  const slot = slotId === 'afternoon' ? '2 PM – 6 PM' : '8 AM – 12 PM';
  return {
    id: req.id,
    name: req.customer_name,
    players: Number(req.players || 0),
    type: req.group_type || 'Booking',
    ago: req.received_label || 'now',
    day: String(req.date_label || '').startsWith('Today') ? 'Today' : 'Tomorrow',
    slot,
    phone: req.phone,
    activity: req.activity || 'Venue booking',
    date: req.date_label || 'Tomorrow',
    isNew: req.status !== 'sent',
    status: req.status || 'new',
    badge: req.status === 'conflict' ? 'Conflict' : req.status === 'clarification' ? 'Clarify' : 'New',
    replyDraft: req.reply_draft || '',
    rawMessage: `${req.customer_name}: need ${venue.name || 'a venue'} ${slot} for ${req.players || 'the group'} players.`,
    venueId: venue.id,
  };
}

async function fetchJson(path, options) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.error || body.message || `HTTP ${response.status}`);
  }
  return body;
}

async function loadBootstrap() {
  try {
    const payload = await fetchJson('/api/bootstrap');
    applyBootstrap(payload);
    renderAll();
    await syncSelectedRequest();
  } catch (error) {
    state.backendError = error.message || 'Backend bootstrap unavailable';
    state.backendReady = false;
    renderAll();
  }
}

async function reloadDemo() {
  if (state.demoReloading) return;
  state.demoReloading = true;
  renderTopBar();
  try {
    const payload = await fetchJson('/api/reload-demo', { method: 'POST', body: JSON.stringify({}) });
    resetRuntimeState();
    applyBootstrap(payload);
    state.demoReloading = false;
    renderAll();
    await syncSelectedRequest();
    toast('Demo data reloaded');
  } catch (error) {
    state.demoReloading = false;
    state.backendError = error.message || 'Reload failed';
    renderAll();
    toast('Reload failed');
  }
}

function candidateFromState(req) {
  const venue = currentVenue(state);
  const [firstName, ...rest] = String(req.name || '').split(' ');
  return {
    intent: 'book_slot',
    customer: { name: req.name, phone: req.phone },
    sport: String(effField(state, 'Activity', req.activity) || 'venue booking').toLowerCase(),
    date_text: sameDay(state.selDate, state.today) ? 'today' : 'tomorrow',
    time_window: String(CAL_SLOTS[state.slotIndex].label).replace(/–/g, '-'),
    venue_preference: venue.name,
    surface_preference: `${venue.surface || ''} ${venue.type || ''}`.trim(),
    players: Number(effField(state, 'Players', String(state.players))) || state.players || req.players,
    budget: { amount: state.price || venue.suggested || 0, currency: 'Rs' },
    missing_fields: [],
    confidence: 0.92,
    reply_draft: replyDraftForState(state),
    customer_short_name: firstName || rest.join(' '),
  };
}

function messageForRequest(req) {
  return req.rawMessage || `Need ${req.activity.toLowerCase()} ${req.day.toLowerCase()} ${req.slot} for ${req.players} players.`;
}

function replyDraftForState(s) {
  const req = currentRequest(s);
  if (!req) return 'Pick a request to review the reply draft.';
  const conversation = activeConversation(s);
  if (isModelBackedRequest(req) && !conversation && s.syncStatus !== 'syncing' && s.modelRuns[req.id]?.status !== 'error') {
    return '';
  }
  if (isModelBackedRequest(req) && s.syncStatus === 'syncing' && !conversation) {
    return 'Calling the Modal model for this booking request now.';
  }
  if (isModelBackedRequest(req) && !conversation && s.modelRuns[req.id]?.status === 'error') {
    return 'The live model call did not complete. The trace panel has the blocker.';
  }
  const text = conversation?.outbound_message?.text || req.replyDraft;
  if (text) return text;
  const venue = currentVenue(s);
  return `Hi ${req.name.split(' ')[0]}, ${venue.name} is available ${s.dateLabel} from ${s.slot}. The slot is ${fmtPrice(s.price)}. I can hold it after owner approval.`;
}

function draftLabelForState(s) {
  const conversation = activeConversation(s);
  const req = currentRequest(s);
  if (isModelBackedRequest(req) && !conversation && s.syncStatus !== 'syncing') return 'Message ready · not sent';
  if (isModelBackedRequest(req) && s.syncStatus === 'syncing') return 'Live model call · Modal';
  if (isModelBackedRequest(req) && conversation?.model_extraction?.backend === 'modal_http') return 'Modal model reply · not sent';
  if (s.syncStatus === 'syncing') return 'Backend review · syncing';
  if (conversation?.terminal_state === 'confirmed_simulated') return 'Simulator sent · terminal';
  if (conversation?.status === 'failed_model') return 'Model blocked · not sent';
  if (conversation?.status === 'conflict_possible') return 'Conflict draft · not sent';
  if (conversation?.status === 'needs_player_info') return 'Clarification draft · not sent';
  return 'Draft reply · not sent';
}

async function syncSelectedRequest() {
  const req = currentRequest(state);
  if (!req) return null;
  const seq = ++state.requestSeq;
  state.syncStatus = 'syncing';
  state.backendError = '';
  const modelBacked = isModelBackedRequest(req);
  const message = messageForRequest(req);
  const traceId = modelBacked ? `ui-modal-${Date.now()}` : `ui-${req.id}`;
  const startedAt = Date.now();
  if (modelBacked) {
    req.status = 'demo_calling';
    req.badge = 'Calling';
    state.modelRuns[req.id] = {
      status: 'calling',
      traceId,
      startedAt,
      endpoint: '/api/whatsapp/simulated-model-message',
      message,
    };
    renderQueue();
    renderStage();
  }
  renderDetail();
  try {
    const payload = {
      session_id: `ui-${req.id}`,
      message_id: `ui-${req.id}-${Date.now()}`,
      sender_phone: req.phone,
      text: message,
      trace_id: traceId,
    };
    if (!modelBacked) {
      payload.extraction = {
        ok: true,
        booking: candidateFromState(req),
        fallback_used: false,
      };
    }
    const body = await fetchJson(modelBacked ? '/api/whatsapp/simulated-model-message' : '/api/whatsapp/simulated-message', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (seq !== state.requestSeq || req.id !== state.selectedId) return null;
    storeConversation(req.id, body.conversation);
    applyModelBookingToState(req, body.conversation);
    await fetchTrace(req.id, body.conversation?.session_id);
    if (modelBacked) {
      const extraction = body.conversation?.model_extraction || {};
      req.status = 'demo_ready';
      req.badge = extraction.ok === false ? 'Blocked' : 'Modal';
      state.modelRuns[req.id] = {
        ...(state.modelRuns[req.id] || {}),
        status: extraction.ok === false ? 'blocked' : 'complete',
        traceId: extraction.trace_id || traceId,
        latencyMs: extraction.client_latency_ms || extraction.latency_ms || (Date.now() - startedAt),
        fallbackUsed: !!extraction.fallback_used,
        validation: extraction.validation || body.conversation?.model_validation || {},
        backend: extraction.backend || 'modal_http',
        modelId: extraction.model_id,
        completedAt: Date.now(),
      };
    }
    state.syncStatus = 'ready';
    renderAll();
    return body.conversation;
  } catch (error) {
    if (seq !== state.requestSeq) return null;
    state.syncStatus = 'error';
    state.backendError = error.message || 'Conversation sync failed';
    if (modelBacked) {
      req.status = 'demo_error';
      req.badge = 'Error';
      state.modelRuns[req.id] = {
        ...(state.modelRuns[req.id] || {}),
        status: 'error',
        traceId,
        latencyMs: Date.now() - startedAt,
        blocker: state.backendError,
        completedAt: Date.now(),
      };
    }
    renderAll();
    return null;
  }
}

async function sendDemoChatMessage(text) {
  const req = currentRequest(state);
  if (!isModelBackedRequest(req)) return null;
  const clean = String(text || '').trim();
  if (!clean) return null;
  req.rawMessage = clean;
  req.chatDraft = '';
  state.demoChatDraft = '';
  delete state.conversations[req.id];
  delete state.traces[req.id];
  return syncSelectedRequest();
}

function storeConversation(requestId, conversation) {
  if (!conversation) return;
  state.conversations[requestId] = conversation;
}

async function fetchTrace(requestId, sessionId) {
  if (!sessionId) return;
  try {
    const body = await fetchJson(`/api/conversations/${encodeURIComponent(sessionId)}/trace`);
    state.traces[requestId] = body.trace;
  } catch (_) {
    state.traces[requestId] = null;
  }
}

async function ensureConversation() {
  const conversation = activeConversation(state);
  if (conversation) return conversation;
  return syncSelectedRequest();
}

async function ownerReview(action) {
  const req = currentRequest(state);
  if (!req) return;
  const conversation = await ensureConversation();
  if (!conversation?.session_id) return;
  state.syncStatus = 'syncing';
  renderDetail();
  try {
    const body = await fetchJson(`/api/conversations/${encodeURIComponent(conversation.session_id)}/owner-review`, {
      method: 'POST',
      body: JSON.stringify({
        action,
        approval_source: 'owner_ui',
        reply_draft: replyDraftForState(state),
      }),
    });
    storeConversation(req.id, body.conversation);
    await fetchTrace(req.id, body.conversation?.session_id);
    const terminal = body.conversation?.terminal_state;
    req.isNew = false;
    req.badge = terminal === 'confirmed_simulated' ? 'Sent' : action === 'reject' ? 'Rejected' : 'Waiting';
    req.status = terminal || body.conversation?.status || req.status;
    addTemporaryBooking(req, body.conversation);
    updatePendingStat();
    state.syncStatus = 'ready';
    renderAll();
    toast(action === 'approve' && terminal === 'confirmed_simulated'
      ? `Backend approved and simulator sent to ${req.name.split(' ')[0]}`
      : `Backend recorded ${action} for ${req.name.split(' ')[0]}`);
  } catch (error) {
    state.syncStatus = 'error';
    state.backendError = error.message || 'Owner review failed';
    renderAll();
  }
}

/* load the editable fields for a freshly selected request */
function loadRequest(id) {
  const req = state.requests.find(r => r.id === id);
  if (!req) { state.selectedId = null; return; }
  state.requestSeq += 1;
  state.selectedId = id;
  state.syncStatus = state.conversations[id] ? 'ready' : 'idle';
  state.backendError = '';
  state.venueId = req.venueId || Data.venues[0]?.id || '';
  state.venueOpen = false;
  const venue = currentVenue(state);
  state.price = venue?.suggested || 0;
  state.players = req.players;
  state.slot = req.slot;
  state.slotIndex = slotIdxOf(req.slot);
  state.today = currentDay();
  state.selDate = req.day === 'Today' ? new Date(state.today) : addDays(state.today, 1);
  state.dateLabel = fmtDateLabel(state.selDate, state.today);
  state.teamA = isModelBackedRequest(req) ? '' : 'Bangalore Bat Kings';
  state.teamB = '';
  state.fieldEdits = {};
  state.editingField = null;
  state.slotDraft = null;
  state.notes = '';
  if (isModelBackedRequest(req) && !state.conversations[id]) {
    if (req.chatDraft == null) req.chatDraft = messageForRequest(req);
    state.demoChatDraft = req.chatDraft;
  } else {
    state.demoChatDraft = '';
  }
}

async function loadModelStatus() {
  try {
    state.modalStatus = await fetchJson('/api/model-status');
    renderDetail();
  } catch (_) {
    state.modalStatus = null;
  }
}

/* ───────────── region rendering ───────────── */
const app = document.getElementById('app');

function detailScrollState() {
  return {
    panel: app.querySelector('.detail')?.scrollTop || 0,
    inner: app.querySelector('.detail-scroll')?.scrollTop || 0,
  };
}
function restoreDetailScroll(pos) {
  const panel = app.querySelector('.detail');
  const inner = app.querySelector('.detail-scroll');
  if (panel) panel.scrollTop = pos.panel || 0;
  if (inner) inner.scrollTop = pos.inner || 0;
}
function renderAll() {
  const top = detailScrollState();
  app.replaceChildren(
    TopBar(Data, handlers, state),
    h('div', { class: 'app-body' },
      Queue(state, handlers),
      Stage(state, handlers),
      h('div', { class: 'col-resizer', title: 'Drag to resize', onPointerdown: startResize }),
      Detail(state, handlers)));
  restoreDetailScroll(top);
  scrollThread();
}
function replaceRegion(selector, node) {
  const cur = app.querySelector(selector);
  if (cur) cur.replaceWith(node);
}
const renderQueue  = () => replaceRegion('.queue',  Queue(state, handlers));
const renderTopBar = () => replaceRegion('.topbar', TopBar(Data, handlers, state));
const renderStage  = () => { replaceRegion('.stage', Stage(state, handlers)); scrollThread(); };
function scrollThread() {
  const b = app.querySelector('.pc-body');
  if (b) b.scrollTop = b.scrollHeight;
}
const renderDetail = () => {
  const top = detailScrollState();
  replaceRegion('.detail', Detail(state, handlers));
  restoreDetailScroll(top);
};

/* ───────────── handlers ───────────── */
const handlers = {
  select(id) {
    if (id === state.selectedId) return;
    loadRequest(id);
    renderQueue(); renderStage(); renderDetail();
    if (shouldAutoSyncSelectedRequest()) syncSelectedRequest();
  },

  toggleVenue() { state.venueOpen = !state.venueOpen; renderDetail(); },

  pickVenue(id) {
    const v = Data.venues.find(x => x.id === id);
    state.venueId = id;
    state.venueOpen = false;
    state.price = v.suggested;
    state.slot = v.slot;
    renderDetail(); renderStage();
    if (shouldAutoSyncSelectedRequest()) syncSelectedRequest();
  },

  price(delta) {
    state.price = Math.max(0, state.price + delta);
    const el = document.getElementById('price-val');
    if (el) el.innerHTML = `<span class="cur">₹</span>${state.price.toLocaleString('en-IN')}`;
    renderStage();
  },

  notes(val) {
    state.notes = val;
    const cnt = document.getElementById('notes-cnt');
    if (cnt) cnt.textContent = `${val.length} / 120`;
    renderStage();
  },

  demoChatDraft(val) {
    state.demoChatDraft = val;
    const req = currentRequest(state);
    if (isModelBackedRequest(req) && !activeConversation(state)) req.chatDraft = val;
  },

  sendDemoChat(e) {
    if (e) e.preventDefault();
    sendDemoChatMessage(state.demoChatDraft);
  },

  copy(num) {
    if (navigator.clipboard) navigator.clipboard.writeText(num).catch(() => {});
    toast('Number copied');
  },

  filter() { toast('Filter & sort — coming soon'); },

  reloadDemo() { reloadDemo(); },

  editIntent() {
    if (shouldAutoSyncSelectedRequest() || activeConversation(state)) {
      syncSelectedRequest();
      toast('Backend candidate refreshed');
    } else {
      toast('Edit the message, then send it to the model');
    }
  },

  editField(name) {
    state.editingField = name;
    if (name === 'Slot') state.slotDraft = state.fieldEdits['Slot'] ? state.fieldEdits['Slot'].value : state.slot;
    renderDetail();
    const inp = document.getElementById('edit-input');
    if (inp) { inp.focus(); inp.select(); }
  },

  pickSlotDraft(label) {
    state.slotDraft = label;
    renderDetail();
  },

  saveField(key) {
    if (key === 'Slot') {
      const original = state.fieldEdits['Slot'] ? state.fieldEdits['Slot'].original : state.slot;
      const val = state.slotDraft;
      if (val && val !== original) state.fieldEdits['Slot'] = { original, value: val };
      else delete state.fieldEdits['Slot'];
      state.editingField = null;
      renderDetail(); renderStage();
      if (shouldAutoSyncSelectedRequest()) syncSelectedRequest();
      return;
    }
    const inp = document.getElementById('edit-input');
    if (!inp) return;
    if (key === 'Date') {
      const iso = inp.value;
      if (iso) {
        const [y, m, d] = iso.split('-').map(Number);
        const newLabel = fmtDateLabel(new Date(y, m - 1, d), state.today);
        const original = state.fieldEdits['Date'] ? state.fieldEdits['Date'].original : state.dateLabel;
        if (newLabel !== original) state.fieldEdits['Date'] = { original, value: newLabel, iso };
        else delete state.fieldEdits['Date'];
      }
      state.editingField = null;
      renderDetail(); renderStage();
      if (shouldAutoSyncSelectedRequest()) syncSelectedRequest();
      return;
    }
    const val = inp.value.trim();
    const original = state.fieldEdits[key] ? state.fieldEdits[key].original : fieldBase(key);
    if (val && val !== original) state.fieldEdits[key] = { original, value: val };
    else delete state.fieldEdits[key];
    state.editingField = null;
    renderDetail(); renderStage();
    if (shouldAutoSyncSelectedRequest()) syncSelectedRequest();
  },

  cancelField() {
    state.editingField = null;
    renderDetail();
  },

  team(label) {
    if (label === 'Team B' && !state.teamB) {
      state.teamB = 'Mumbai Spinners';
      renderDetail();
      toast('Team B added');
    } else {
      toast(`Edit ${label.toLowerCase()}`);
    }
  },

  pickSlot(date, idx) {
    state.selDate = date;
    state.slotIndex = idx;
    renderDetail(); renderStage();
    if (shouldAutoSyncSelectedRequest()) syncSelectedRequest();
  },

  approve() { ownerReview('approve'); },
  clarify() { ownerReview('clarify'); },
  reject() { ownerReview('reject'); },
};

/* ───────────── resizable detail panel ───────────── */
const DETAIL_MIN = 360, DETAIL_MAX = 760;
function startResize(e) {
  e.preventDefault();
  const handle = e.currentTarget;
  handle.classList.add('dragging');
  document.body.classList.add('is-resizing');
  const move = ev => {
    const w = Math.min(DETAIL_MAX, Math.max(DETAIL_MIN, window.innerWidth - ev.clientX));
    document.documentElement.style.setProperty('--detail-w', w + 'px');
  };
  const up = () => {
    handle.classList.remove('dragging');
    document.body.classList.remove('is-resizing');
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', up);
    const cur = getComputedStyle(document.documentElement).getPropertyValue('--detail-w').trim();
    if (cur) { try { localStorage.setItem('fl-detail-w', cur); } catch (_) {} }
  };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', up);
}

/* restore persisted width */
try {
  const saved = localStorage.getItem('fl-detail-w');
  if (saved) document.documentElement.style.setProperty('--detail-w', saved);
} catch (_) {}

/* ───────────── toast ───────────── */
let toastWrap;
function toast(msg) {
  if (!toastWrap) {
    toastWrap = h('div', { class: 'toast-wrap' });
    document.body.appendChild(toastWrap);
  }
  const t = h('div', { class: 'toast' }, h('span', { class: 'ic' }, Icons.check(15, 'var(--c-accent)')), msg);
  toastWrap.appendChild(t);
  setTimeout(() => {
    t.style.transition = 'opacity .3s, transform .3s';
    t.style.opacity = '0';
    t.style.transform = 'translateY(8px)';
    setTimeout(() => t.remove(), 320);
  }, 2400);
}

/* ───────────── boot ───────────── */
refreshClock();
renderAll();
loadBootstrap();
loadModelStatus();
setInterval(refreshClock, 15000);
