/* ============================================================
   COMPONENTS — pure render functions. Each returns a DOM node
   built from data + the current `state`. Re-render by region.
   Callbacks come in via the `on` handlers object from app.js.
   ============================================================ */

/* ───────────── Top bar ───────────── */
function TopBar(data, on, appState) {
  const statCell = (k, v, accent) =>
    h('div', { class: 'stat-cell' },
      h('span', { class: 'k' }, k),
      h('span', { class: 'v' + (accent ? ' accent' : '') }, String(v)));
  const reloading = !!appState?.demoReloading;
  const occupancy = Number(data.stats.occupancyWeek ?? data.stats.occupancy ?? 0);

  return h('header', { class: 'topbar', 'data-design-id': 'brand-header' },
    h('div', { class: 'brand' },
      h('img', { src: 'assets/floodlight-logo.png', alt: 'Floodlight' })),
    h('div', { class: 'stats' },
      h('div', { class: 'stat-cell chan', 'data-design-id': 'channel-status' },
        Icons.whatsapp(30),
        h('div', { class: 'meta' },
          h('div', { class: 'k' }, data.org.channel),
          h('div', { class: 's' }, data.org.channelState || 'Connected'))),
      statCell('Pending Requests', data.stats.pending, true),
      statCell('Confirmed Today', data.stats.confirmedToday, true),
      h('div', { class: 'stat-cell occ-cell' },
        h('div', { class: 'occ-txt' },
          h('div', { class: 'k' }, 'Occupancy This Week'),
          h('div', { class: 'v accent' }, occupancy + '%')),
        ringNode(occupancy, 30)),
      statCell('Date', data.org.dateLabel),
      statCell('Time', data.org.timeLabel)),
    h('div', { class: 'top-actions' },
      h('button', {
          class: 'reload-demo',
          'data-design-id': 'reload-demo',
          disabled: reloading,
          onClick: () => on.reloadDemo(),
        },
        Icons.refresh(16),
        h('span', {}, reloading ? 'Resetting' : 'Reset'))),
    h('div', { class: 'ball' },
      h('img', { src: 'assets/cricket-ball.png', alt: '' })));
}

/* ───────────── Queue (left column) ───────────── */
function RequestCard(req, selected, on) {
  const cardClass = 'req-card' + (selected ? ' is-selected' : '') + (req.isTryMe ? ' is-try-me' : '');
  const meta = req.isTryMe && req.status === 'demo_idle'
    ? 'Edit prompt · Modal'
    : req.isTryMe && req.status === 'demo_calling'
      ? 'Calling Modal'
      : `${req.players} players · ${req.type}`;
  return h('button', {
      class: cardClass,
      dataset: { id: req.id },
      'data-design-id': req.isTryMe ? 'try-me-queue-card' : undefined,
      onClick: () => on.select(req.id),
    },
    h('div', { class: 'row1' },
      h('div', { class: 'av' }, Icons.waOutline(16)),
      h('div', {},
        h('div', { class: 'ago' }, req.ago),
        h('div', { class: 'nm' }, req.name),
        h('div', { class: 'meta' }, meta))),
    h('div', { class: 'row2' },
      h('div', { class: 'when' },
        h('div', { class: 'd' }, req.day),
        h('div', { class: 't' }, req.slot)),
      (req.badge || req.isNew) && h('span', { class: 'badge' }, req.badge || 'New')));
}

function Queue(state, on) {
  const newCount = state.requests.filter(r => r.isNew && !r.isTryMe).length;
  return h('aside', { class: 'col queue', 'data-design-id': 'request-queue' },
    h('div', { class: 'queue-head' },
      h('span', { class: 'u-label' }, 'Live Request Queue'),
      h('span', { class: 'count' }, h('span', { class: 'u-dot' }), `${newCount} New`)),
    h('div', { class: 'queue-list' },
      state.requests.map(r => RequestCard(r, r.id === state.selectedId, on))),
    h('div', { class: 'queue-foot' },
      h('button', { onClick: on.filter },
        Icons.filter(18),
        h('span', { class: 'lab' }, 'Filter & Sort'),
        h('span', { class: 'chev' }, Icons.chevronRight(18)))));
}

/* ───────────── Center stage ───────────── */
/* incoming chat history seeded from the request data */
function buildHistory(req, conversation) {
  if (req.modelBacked && conversation?.turns?.length) {
    return conversation.turns.map(turn => ({
      time: turn.received_at ? 'Live' : 'Now',
      lines: [turn.raw_message || req.rawMessage],
    }));
  }
  if (req.modelBacked && req.pendingInboundMessage) {
    return [
      { time: 'Now', lines: [req.pendingInboundMessage] },
    ];
  }
  if (req.modelBacked) return [];
  if (req.rawMessage) {
    return [
      { time: '12:02', lines: [req.rawMessage] },
      { time: '12:03', lines: ['Can you confirm and share the quote?'] },
    ];
  }
  return [
    { time: '12:02', lines: [`Hi, is the ground free ${req.day.toLowerCase()}?`] },
    { time: '12:03', lines: [`Want to book ${req.activity.toLowerCase()} for ${req.players} players`] },
    { time: '12:04', lines: [`${req.type} match · ${req.slot}`] },
    { time: '12:05', lines: ['Can you confirm and share the quote?'] },
  ];
}

/* effective value of an editable field (edited value wins over base) */
function effField(state, key, base) {
  return state.fieldEdits && state.fieldEdits[key] ? state.fieldEdits[key].value : base;
}

function Stage(state, on) {
  const req = currentRequest(state);
  if (!req) {
    return h('main', { class: 'col stage', 'data-design-id': 'conversation-stage' },
      h('div', { class: 'stage-empty' },
        h('div', { class: 'ico' }, Icons.inbox(30)),
        h('div', { class: 'big' }, 'Queue is clear'),
        h('div', {}, 'No pending booking requests right now.')));
  }
  const venue = currentVenue(state);
  const conversation = activeConversation(state);
  const first = req.name.split(' ')[0];
  const draft = replyDraftForState(state);
  const modelReadyForInput = req.modelBacked && !conversation && state.syncStatus !== 'syncing' && state.modelRuns?.[req.id]?.status !== 'error';
  const actV = effField(state, 'Activity', req.activity);
  const dateV = fmtDateLabel(state.selDate, state.today);
  const slotV = CAL_SLOTS[state.slotIndex].label;
  const playersV = effField(state, 'Players', String(state.players));
  const booking = modelBooking(state);
  const showPreviewMeta = !req.modelBacked || !!booking;
  const metaSlot = booking ? detailSlotFromBooking(booking.time_window) || slotV : slotV;
  const metaPlayers = booking?.players ? String(booking.players) : playersV;
  const metaQuote = booking?.budget?.amount ? fmtPrice(Number(booking.budget.amount)) : fmtPrice(state.price);
  const leadLine = req.status === 'conflict'
    ? 'the requested slot needs an alternative.'
    : req.status === 'clarification'
      ? 'I need one more detail before owner approval.'
      : 'your booking is confirmed.';
  const suppressModelEmptyReply = req.modelBacked && !conversation;
  const replyComposerText = replyComposerTextForState(state);
  const showTryMeComposer = req.modelBacked && !req.pendingInboundMessage && !conversation;

  /* customer's incoming messages */
  const incoming = buildHistory(req, conversation).map(m =>
    h('div', { class: 'msg in' },
      h('div', { class: 'bubble in' },
        ...m.lines.map(l => h('p', {}, l)),
        h('div', { class: 'tstamp' }, m.time))));

  /* our outgoing draft reply — live preview */
  const outgoing = modelReadyForInput || suppressModelEmptyReply ? null : h('div', { class: 'msg out' },
    h('div', { class: 'bubble out' },
      h('p', {}, 'Hi ', h('strong', {}, first), `, ${leadLine}`),
      h('p', {}, h('strong', {}, actV), ' at ', h('strong', {}, venue.name),
        ` · ${dateV} · ${slotV} · ${playersV} players`),
      h('p', { class: 'price-line' }, fmtPrice(state.price)),
      draft && h('p', {}, draft),
      state.notes.trim() && h('p', {}, state.notes.trim()),
      h('div', { class: 'tstamp' }, '12:06 · Draft')));

  return h('main', { class: 'col stage', 'data-design-id': 'conversation-stage' },
    h('div', { class: 'stage-head' },
      h('span', { class: 'u-label' }, 'Conversation'),
      h('span', { class: 'u-rule' })),
    h('div', { class: 'preview-card' },
      h('div', { class: 'pc-head' },
        Icons.whatsapp(30),
        h('div', { class: 'who' },
          h('div', { class: 'n' }, req.name),
          h('div', { class: 'p' }, req.phone)),
        h('div', { class: 'chan' }, h('span', { class: 'u-dot' }), 'WhatsApp')),
      h('div', { class: 'pc-body' },
        showTryMeComposer && TryMeComposer(state, on),
        h('div', { class: 'chat-thread' },
          h('div', { class: 'day-chip' }, 'Today'),
          ...incoming,
          !modelReadyForInput && !suppressModelEmptyReply && h('div', { class: 'draft-divider', 'data-design-id': 'reply-draft' }, h('span', { class: 'u-dot' }), draftLabelForState(state)),
          outgoing)),
      ReplySendComposer(state, on, replyComposerText)),
    showPreviewMeta && h('div', { class: 'preview-meta' },
      MetaPill('Venue', venue.name),
      MetaPill('Slot', metaSlot),
      MetaPill('Players', metaPlayers),
      MetaPill('Quote', metaQuote, true)));
}

function TryMeComposer(state, on) {
  const disabled = state.syncStatus === 'syncing';
  const input = h('textarea', {
    rows: '2',
    maxlength: '220',
    placeholder: 'Edit the sample booking message...',
    oninput: e => on.demoChatDraft(e.target.value),
    disabled,
  });
  input.value = state.demoChatDraft || '';
  return h('form', { class: 'chat-compose', 'data-design-id': 'try-me-chat-composer', onSubmit: on.sendDemoChat },
    input,
    h('button', { type: 'submit', disabled: disabled || !String(state.demoChatDraft || '').trim() },
      disabled ? 'Calling' : 'Receive from User'));
}

function ReplySendComposer(state, on, value) {
  const disabled = state.syncStatus === 'syncing';
  const text = String(value || '');
  const input = h('textarea', {
    rows: '2',
    maxlength: '520',
    placeholder: 'Reply draft will appear here...',
    oninput: e => on.replyComposerDraft(e.target.value),
    disabled,
  });
  input.value = text;
  return h('form', { class: 'chat-compose reply-compose', 'data-design-id': 'reply-send-composer', onSubmit: on.sendReplyComposer },
    input,
    h('button', { type: 'submit', disabled: disabled || !text.trim() }, 'Send'));
}

function MetaPill(k, v, accent) {
  return h('div', { class: 'pm' },
    h('div', { class: 'k' }, k),
    h('div', { class: 'v' + (accent ? ' accent' : '') }, String(v)));
}

/* ───────────── Detail panel (right column) ───────────── */
function SectionLabel(text, designId) {
  const attrs = designId ? { class: 'sec-label', 'data-design-id': designId } : { class: 'sec-label' };
  return h('div', attrs,
    h('span', { class: 'u-label' }, text), h('span', { class: 'u-rule' }));
}

function SimpleDetailRow(k, v) {
  return h('div', { class: 'drow' },
    h('span', { class: 'dk' }, k), h('span', { class: 'dv' }, v));
}

function modelBooking(state) {
  return activeConversation(state)?.model_extraction?.booking || null;
}

function displayTitleFromBooking(state) {
  const req = currentRequest(state);
  const conversation = activeConversation(state);
  const booking = modelBooking(state);
  if (req?.modelBacked && state.syncStatus === 'syncing') return 'Reading message';
  if (req?.modelBacked && !conversation) return 'Waiting for message';
  if (booking?.intent === 'book_slot') {
    if (activeConversation(state)?.status === 'needs_player_info') return 'Booking needs clarification';
    if (activeConversation(state)?.status === 'conflict_possible') return 'Booking conflict';
    return 'Book venue';
  }
  return 'Book venue';
}

function detailDateFromBooking(value, state) {
  const text = String(value || '').toLowerCase();
  if (text.includes('today')) return fmtDateLabel(state.today, state.today);
  if (text.includes('tomorrow')) return fmtDateLabel(new Date(state.today.getFullYear(), state.today.getMonth(), state.today.getDate() + 1), state.today);
  return value || '';
}

function detailSlotFromBooking(value) {
  const text = String(value || '').toLowerCase();
  if (text.includes('afternoon') || text.includes('2') || text.includes('6')) return '2 PM – 6 PM';
  if (text.includes('morning') || text.includes('8') || text.includes('12')) return '8 AM – 12 PM';
  return value || '';
}

function detectedRows(state, on) {
  const req = currentRequest(state);
  const booking = modelBooking(state);
  if (req?.modelBacked && !booking) {
    return [
      SimpleDetailRow('Activity', ''),
      SimpleDetailRow('User Requested Date', ''),
      SimpleDetailRow('Requested Slot', ''),
      SimpleDetailRow('Players', ''),
      SimpleDetailRow('Team A', ''),
      SimpleDetailRow('Team B', ''),
    ];
  }
  if (req?.modelBacked && booking) {
    return [
      DetailRow('Activity', 'Activity', booking.sport ? titleCaseWords(booking.sport) : req.activity, state, on),
      DetailRow('Date', 'User Requested Date', detailDateFromBooking(booking.date_text, state), state, on),
      DetailRow('Slot', 'Requested Slot', detailSlotFromBooking(booking.time_window), state, on),
      DetailRow('Players', 'Players', booking.players ? String(booking.players) : String(state.players), state, on),
      SimpleDetailRow('Team A', ''),
      SimpleDetailRow('Team B', ''),
    ];
  }
  return [
    DetailRow('Activity', 'Activity', req.activity, state, on),
    DetailRow('Date', 'User Requested Date', state.dateLabel, state, on),
    DetailRow('Slot', 'Requested Slot', state.slot, state, on),
    DetailRow('Players', 'Players', String(state.players), state, on),
    TeamRow('Team A', state.teamA, on),
    TeamRow('Team B', state.teamB, on),
  ];
}

function isoDate(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function DetailRow(key, label, value, state, on) {
  const edit = state.fieldEdits && state.fieldEdits[key];
  if (state.editingField === key) {
    const onKeydown = e => { if (e.key === 'Enter') on.saveField(key); if (e.key === 'Escape') on.cancelField(); };
    const saveBtn = h('button', { class: 'edit-save', title: 'Save', onClick: () => on.saveField(key) }, Icons.check(14, 'currentColor'));
    const cancelBtn = h('button', { class: 'edit-cancel', title: 'Cancel', onClick: () => on.cancelField() }, Icons.x(13));
    if (key === 'Slot') {
      return h('div', { class: 'drow editing slot-editing' },
        h('span', { class: 'dk' }, label),
        h('div', { class: 'edit-wrap seg-wrap' },
          h('div', { class: 'seg' },
            CAL_SLOTS.map(s => h('button', {
              class: 'seg-btn' + (state.slotDraft === s.label ? ' active' : ''),
              onClick: () => on.pickSlotDraft(s.label) }, s.label))),
          saveBtn, cancelBtn));
    }
    const input = key === 'Date'
      ? h('input', { type: 'date', class: 'edit-input is-date', id: 'edit-input',
          value: edit && edit.iso ? edit.iso : isoDate(state.selDate), onKeydown })
      : h('input', { class: 'edit-input', id: 'edit-input', value: edit ? edit.value : value, onKeydown });
    return h('div', { class: 'drow editing' },
      h('span', { class: 'dk' }, label),
      h('div', { class: 'edit-wrap' }, input, saveBtn, cancelBtn));
  }
  return h('div', { class: 'drow' },
    h('span', { class: 'dk' }, label),
    h('div', { class: 'dv-wrap' },
      edit
        ? h('span', { class: 'dv' },
            h('s', { class: 'dv-old' }, edit.original),
            h('span', { class: 'dv-new' }, edit.value))
        : h('span', { class: 'dv' }, value),
      h('button', { class: 'row-edit', title: `Edit ${label.toLowerCase()}`,
        onClick: () => on.editField(key) }, Icons.edit(14))));
}

function TeamRow(label, name, on) {
  return h('div', { class: 'drow team-row' },
    h('span', { class: 'dk' }, label),
    h('div', { class: 'team-val' },
      name ? h('button', { class: 'team-name', onClick: () => on.team(label) }, name) : null,
      h('button', { class: 'btn-mini', onClick: () => on.team(label) }, name ? 'Edit' : 'Add')));
}

function BackendRows(state) {
  const req = currentRequest(state);
  const conversation = activeConversation(state);
  const trace = activeTrace(state);
  if (state.backendError) {
    return [SimpleDetailRow('Backend', state.backendError)];
  }
  if (state.syncStatus === 'syncing' && !conversation) {
    return [SimpleDetailRow('Backend', 'Syncing selected request')];
  }
  if (req?.modelBacked && !conversation) {
    return [];
  }
  if (!conversation) {
    return [SimpleDetailRow('Backend', state.backendReady ? 'Waiting for selected request' : 'Using local fixture until backend responds')];
  }
  const truth = conversation.truth_check_final && Object.keys(conversation.truth_check_final).length
    ? conversation.truth_check_final
    : conversation.truth_check_initial || {};
  const validation = conversation.model_validation || {};
  const send = conversation.send_adapter || {};
  return [
    SimpleDetailRow('Session', conversation.session_id),
    SimpleDetailRow('Backend action', conversation.status || 'pending'),
    SimpleDetailRow('Truth check', truth.flow_state || truth.status || 'pending'),
    SimpleDetailRow('Validation', validation.valid === false ? 'Schema blocked' : 'Candidate accepted'),
    SimpleDetailRow('Send adapter', `${send.adapter || 'simulator'} · ${send.delivery_state || 'not_sent'}`),
    SimpleDetailRow('Trace id', trace?.trace_id || conversation.trace_id || 'pending'),
  ];
}

function formatLatency(ms, emptyLabel = 'Pending') {
  if (ms == null || ms === '') return emptyLabel;
  const n = Number(ms);
  if (!Number.isFinite(n)) return emptyLabel;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}s`;
  return `${Math.round(n)}ms`;
}

function shortModelId(modelId) {
  const value = String(modelId || 'nvidia/Nemotron-Cascade-2-30B-A3B');
  return value.replace(/^nvidia\//, '');
}

function modelRunState(state) {
  const req = currentRequest(state);
  const conversation = activeConversation(state);
  const trace = activeTrace(state);
  const extraction = conversation?.model_extraction || {};
  const run = state.modelRuns?.[req?.id] || {};
  const validation = extraction.validation || conversation?.model_validation || run.validation || {};
  const runtimeAxes = trace?.runtime_axes || {};
  const calling = (state.syncStatus === 'syncing' && req?.modelBacked) || run.status === 'calling';
  const status = calling
    ? 'Calling'
    : run.status === 'error'
      ? 'Error'
      : extraction.ok === false
        ? 'Blocked'
        : extraction.ok
          ? 'Complete'
          : 'Ready';
  const elapsed = calling && run.startedAt
    ? Date.now() - run.startedAt
    : run.startedAt && run.completedAt
      ? run.completedAt - run.startedAt
      : run.latencyMs || extraction.client_latency_ms || extraction.latency_ms;
  return {
    status,
    traceId: extraction.trace_id || run.traceId || conversation?.trace_id || 'pending',
    latency: extraction.client_latency_ms || extraction.latency_ms || run.latencyMs,
    elapsed,
    signal: calling
      ? 'HTTP request open; waiting for Modal response'
      : extraction.ok
        ? 'Modal response received'
        : run.status === 'error'
          ? 'Request ended with blocker'
          : 'Ready for edited message',
    timeoutSeconds: run.timeoutSeconds || state.modalStatus?.timeout_seconds,
    fallbackUsed: extraction.fallback_used ?? run.fallbackUsed,
    validation,
    backend: extraction.backend || runtimeAxes.model_backend || run.backend || 'modal_http',
    modelId: extraction.model_id || runtimeAxes.model_id || run.modelId || state.modalStatus?.model_id,
    blocker: extraction.blocker || run.blocker || '',
  };
}

function ModelRunBlock(state) {
  const req = currentRequest(state);
  if (!req?.modelBacked) return null;
  const info = modelRunState(state);
  const valid = info.validation?.valid;
  const statusClass = String(info.status || '').toLowerCase();
  const runEnded = ['complete', 'blocked', 'error'].includes(statusClass);
  const pendingOrMissing = runEnded ? 'Not reported' : 'Pending';
  const fallback = info.fallbackUsed === true ? 'Yes' : info.fallbackUsed === false ? 'No' : pendingOrMissing;
  const schema = valid === true ? 'Valid' : valid === false ? 'Blocked' : runEnded ? 'Not validated' : 'Pending';
  const raw = activeConversation(state)?.model_extraction || state.modelRuns?.[req.id] || {};
  return h('div', { class: 'model-run', 'data-design-id': 'model-run-proof' },
    h('div', { class: 'model-run-head' },
      h('div', {},
        h('div', { class: 'u-label' }, 'Model Run'),
        h('div', { class: 'model-name' }, shortModelId(info.modelId))),
      h('span', { class: `model-status ${statusClass}` }, info.status)),
    h('div', { class: 'model-grid' },
      SimpleDetailRow('Runtime', 'Modal'),
      SimpleDetailRow('Backend', info.backend),
      SimpleDetailRow('Signal', info.signal),
      SimpleDetailRow('Elapsed', formatLatency(info.elapsed)),
      SimpleDetailRow('Timeout', info.timeoutSeconds ? `${info.timeoutSeconds}s` : 'Pending'),
      SimpleDetailRow('Latency', formatLatency(info.latency, pendingOrMissing)),
      SimpleDetailRow('Schema', schema),
      SimpleDetailRow('Fallback', fallback),
      SimpleDetailRow('Trace id', info.traceId)),
    info.blocker && h('div', { class: 'model-blocker' }, info.blocker),
    Object.keys(raw).length
      ? h('details', { class: 'raw-details' },
          h('summary', {}, 'Raw model details'),
          h('pre', {}, JSON.stringify(raw, null, 2)))
      : null);
}

function TraceLedger(state) {
  const req = currentRequest(state);
  const conversation = activeConversation(state);
  const trace = activeTrace(state);
  const events = (trace?.agent_trace || conversation?.agent_trace || []).slice(-4);
  if (req?.modelBacked && !conversation && !trace) {
    return h('div', { class: 'trace-ledger', 'data-design-id': 'trace-ledger' });
  }
  if (!events.length) {
    return h('div', { class: 'trace-ledger', 'data-design-id': 'trace-ledger' },
      h('div', { class: 'trace-row' }, h('span', {}, 'Backend trace will appear after sync.')));
  }
  return h('div', { class: 'trace-ledger', 'data-design-id': 'trace-ledger' },
    events.map(event => h('div', { class: `trace-row ${event.tone || ''}` },
      h('span', {}, event.label || event.id || 'Trace event'),
      h('small', {}, event.timestamp_label || event.stage || 'now'))));
}

function actionDisabled(state) {
  const conversation = activeConversation(state);
  return state.syncStatus === 'syncing' || !conversation || !!conversation.terminal_state;
}

function VenueSelector(state, on) {
  const sel = currentVenue(state);
  return h('div', { class: 'venue' + (state.venueOpen ? ' open' : '') },
    h('button', { class: 'venue-hd', onClick: on.toggleVenue },
      h('span', { class: 't' }, sel.name),
      h('span', { class: 's' }, sel.slot, Icons.chevron(14))),
    h('div', { class: 'venue-sub' },
      h('div', { class: 'p' }, h('span', { class: 'pk' }, 'Surface'), h('span', { class: 'pv' }, sel.surface)),
      h('div', { class: 'p' }, h('span', { class: 'pk' }, 'Type'), h('span', { class: 'pv' }, sel.type))),
    h('div', { class: 'venue-opts' },
      Data.venues.map(v => h('button', {
          class: 'venue-opt' + (v.id === state.venueId ? ' active' : ''),
          onClick: () => on.pickVenue(v.id),
        },
        h('span', { class: 'ot' }, v.name),
        h('span', { class: 'os' }, `${v.surface} · ${v.type}`)))));
}

function PriceStepper(state, on) {
  return h('div', {},
    h('div', { class: 'price' },
      h('button', { class: 'step-btn', onClick: () => on.price(-500), 'aria-label': 'Decrease' }, Icons.minus(18)),
      h('div', { class: 'step-val', id: 'price-val' },
        h('span', { class: 'cur' }, '₹'), state.price.toLocaleString('en-IN')),
      h('button', { class: 'step-btn', onClick: () => on.price(500), 'aria-label': 'Increase' }, Icons.plus(18))),
    h('div', { class: 'price-hint' },
      `Suggested price: ${fmtPrice(currentVenue(state).suggested)}`, Icons.info(14)));
}

function NotesField(state, on) {
  const ta = h('textarea', {
    maxlength: '120',
    placeholder: 'Add a note for the customer…',
    oninput: e => on.notes(e.target.value),
  });
  ta.value = state.notes;
  return h('div', { class: 'notes' }, ta,
    h('div', { class: 'cnt', id: 'notes-cnt' }, `${state.notes.length} / 120`));
}

function IntegrationRow(it) {
  return h('div', { class: 'intg' },
    h('div', { class: 'l' },
      h('div', { class: 'ic' }, Icons[it.icon](16)),
      h('div', { class: 'nm' }, it.name)),
    h('div', { class: 'r' },
      h('div', { class: 's1' }, it.s1),
      h('div', { class: 's2' }, it.s2)));
}

/* ───────────── Availability calendar ───────────── */
const CAL_SLOTS = [{ idx: 0, label: '8 AM – 12 PM' }, { idx: 1, label: '2 PM – 6 PM' }];
const CAL_WD = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
const CAL_MON = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const CAL_DOW = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

function calSeed(n) { const x = Math.sin(n * 999.7) * 10000; return x - Math.floor(x); }
function bookingDateText(d, today) {
  const diff = Math.round((dayFloor(d) - dayFloor(today)) / 86400000);
  if (diff === -1) return 'yesterday';
  if (diff === 0) return 'today';
  if (diff === 1) return 'tomorrow';
  return isoDate(d);
}

function slotInfo(d, idx) {
  const k = d.getFullYear() * 366 + (d.getMonth() + 1) * 32 + d.getDate() * 2 + idx;
  const venue = currentVenue(state);
  const slotId = Data.slots[idx]?.id || (idx === 1 ? 'afternoon' : 'morning');
  const dateText = bookingDateText(d, state.today);
  const explicit = (Data.bookings || []).filter(item =>
    item.venue_id === venue.id &&
    item.slot_id === slotId &&
    String(item.date_text || '').toLowerCase() === dateText);
  if (explicit.length) {
    const confirmed = explicit.some(item => String(item.status || '').includes('confirmed'));
    const pending = explicit.some(item => String(item.status || '').includes('pending'));
    return {
      booked: confirmed,
      teamA: confirmed ? 'ok' : 'q',
      teamB: pending ? 'q' : (confirmed ? 'ok' : 'q'),
      statusLabel: confirmed ? 'Booked' : 'Pending demand',
    };
  }
  return {
    booked: calSeed(k) > 0.5,
    teamA: calSeed(k + 3) > 0.45 ? 'ok' : 'q',
    teamB: calSeed(k + 9) > 0.5 ? 'ok' : 'q',
    statusLabel: calSeed(k) > 0.5 ? 'Booked' : 'Open',
  };
}
function sameDay(a, b) { return a && b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate(); }
function dayFloor(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
function fmtDateLabel(d, today) {
  const diff = Math.round((dayFloor(d) - dayFloor(today)) / 86400000);
  const base = `${d.getDate()} ${CAL_MON[d.getMonth()].slice(0, 3)} ${d.getFullYear()}`;
  if (diff === 0) return `Today, ${base}`;
  if (diff === 1) return `Tomorrow, ${base}`;
  return `${CAL_DOW[d.getDay()]}, ${base}`;
}

function TeamGlyph(letter, st) {
  return h('span', { class: 'tg ' + (st === 'ok' ? 'ok' : 'q'),
      title: `Team ${letter} — ${st === 'ok' ? 'confirmed' : 'pending'}` },
    st === 'ok' ? Icons.check(11, 'currentColor') : Icons.qmark(10));
}

function DayCell(date, flags, state, on) {
  const slots = CAL_SLOTS.map(s => {
    const info = slotInfo(date, s.idx);
    const sel = sameDay(date, state.selDate) && state.slotIndex === s.idx;
    return h('button', {
        class: 'cal-slot' + (info.booked ? ' booked' : '') + (sel ? ' sel' : ''),
        title: `${s.label} — ${info.statusLabel || (info.booked ? 'Booked' : 'Open')}`,
        disabled: flags.isPast || undefined,
        onClick: flags.isPast ? undefined : () => on.pickSlot(date, s.idx),
      },
      h('div', { class: 'slot-top' },
        info.booked ? h('span', { class: 'slot-dot' }) : h('span', { class: 'slot-dash' })),
      h('div', { class: 'slot-teams' }, TeamGlyph('A', info.teamA), TeamGlyph('B', info.teamB)));
  });
  return h('div', {
      class: 'cal-day' + (flags.isToday ? ' is-today' : '') + (flags.isPast ? ' is-past' : '') },
    h('div', { class: 'cal-dnum' }, String(date.getDate())),
    h('div', { class: 'cal-slotwrap' }, ...slots));
}

function Calendar(state, on) {
  const today = state.today;
  const blocks = [];
  for (let m = 0; m < 4; m++) {
    const first = new Date(today.getFullYear(), today.getMonth() + m, 1);
    const y = first.getFullYear(), mo = first.getMonth();
    const days = new Date(y, mo + 1, 0).getDate();
    const cells = [];
    for (let i = 0; i < first.getDay(); i++) cells.push(h('div', { class: 'cal-pad' }));
    for (let d = 1; d <= days; d++) {
      const date = new Date(y, mo, d);
      cells.push(DayCell(date, {
        isToday: sameDay(date, today),
        isPast: dayFloor(date) < dayFloor(today),
      }, state, on));
    }
    blocks.push(h('div', { class: 'cal-mlabel' }, `${CAL_MON[mo]} ${y}`));
    blocks.push(h('div', { class: 'cal-grid' }, ...cells));
  }
  return h('div', { 'data-design-id': 'availability-board' },
    h('div', { class: 'cal' },
      h('div', { class: 'cal-weekhead' }, CAL_WD.map(w => h('span', { class: 'cal-wd' }, w))),
      ...blocks),
    h('div', { class: 'cal-legend' },
      h('span', { class: 'lg' }, h('span', { class: 'slot-dot' }), 'Booked'),
      h('span', { class: 'lg conf' }, Icons.check(12, 'currentColor'), 'Confirmed'),
      h('span', { class: 'lg pend' }, Icons.qmark(12), 'Pending')));
}

function Detail(state, on) {
  const req = currentRequest(state);
  if (!req) return h('aside', { class: 'col detail', 'data-design-id': 'booking-detail-panel' });

  return h('aside', { class: 'col detail', 'data-design-id': 'booking-detail-panel' },
    h('div', { class: 'detail-scroll' },
      h('div', {},
        h('div', { class: 'intent-label' }, h('span', { class: 'u-dot' }), 'Detected Request'),
        h('div', { class: 'd-name-row' },
          h('div', { class: 'd-name' }, displayTitleFromBooking(state)),
          h('button', { class: 'intent-edit', title: 'Edit intent', onClick: on.editIntent }, Icons.edit(18)))),
      ModelRunBlock(state),
      h('div', { class: 'drows' }, detectedRows(state, on)),
      h('div', { class: 'divider' }),
      h('div', { class: 'intent-label book-venue' }, h('span', { class: 'u-dot' }), 'Book Venue'),
      SectionLabel('Select Date & Slot'),
      h('div', { class: 'selected-slot' },
        h('span', { class: 'dk' }, 'Selected Date & Slot'),
        h('span', { class: 'sel-val' },
          `${fmtDateLabel(state.selDate, state.today)} · ${CAL_SLOTS[state.slotIndex].label}`)),
      Calendar(state, on),
      h('div', { class: 'divider' }),
      SectionLabel('Backend Review'),
      h('div', { class: 'drows' }, BackendRows(state)),
      TraceLedger(state),
      SectionLabel('Set Price'),
      PriceStepper(state, on),
      SectionLabel('Additional Notes (Optional)'),
      NotesField(state, on),
      SectionLabel('Integrations'),
      h('div', { 'data-design-id': 'disabled-integrations', style: { display: 'flex', flexDirection: 'column', gap: '10px' } },
        Data.integrations.map(IntegrationRow))),
    h('div', { class: 'detail-actions', 'data-design-id': 'approval-actions' },
      h('button', { class: 'btn btn-primary', disabled: actionDisabled(state), onClick: on.approve },
        Icons.check(16),
        h('span', {}, 'Approve & Send', h('small', {}, 'simulator'))),
      h('button', { class: 'btn btn-ghost', disabled: actionDisabled(state), onClick: on.clarify },
        Icons.info(15), 'Clarify'),
      h('button', { class: 'btn btn-ghost', disabled: actionDisabled(state), onClick: on.reject },
        Icons.x(15), 'Reject')));
}
