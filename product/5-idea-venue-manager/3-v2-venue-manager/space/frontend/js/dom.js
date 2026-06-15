/* ============================================================
   DOM — tiny hyperscript helper + icon set
   ============================================================ */

/* h('div', {class:'x', onClick:fn, dataset:{id}}, child, [children]) */
function h(tag, props, ...children) {
  const el = document.createElement(tag);
  const p = props || {};
  for (const [k, v] of Object.entries(p)) {
    if (v == null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k === 'html') el.innerHTML = v;
    else if (k === 'dataset') Object.assign(el.dataset, v);
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
    else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (v === true) el.setAttribute(k, '');
    else el.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c == null || c === false) continue;
    el.appendChild(typeof c === 'object' ? c : document.createTextNode(String(c)));
  }
  return el;
}

/* build an SVG node from a markup string */
function svg(markup) {
  const t = document.createElement('template');
  t.innerHTML = markup.trim();
  return t.content.firstChild;
}

/* icon library — currentColor so semantic text tokens drive them */
const Icons = {
  whatsapp: (s = 30) => svg(`<svg width="${s}" height="${s}" viewBox="0 0 32 32"><circle cx="16" cy="16" r="16" fill="var(--c-accent)"/><path d="M16 7.4a8.4 8.4 0 0 0-7.2 12.7L7.6 24.6l4.6-1.2A8.4 8.4 0 1 0 16 7.4Zm4.9 11.9c-.2.6-1.2 1.1-1.7 1.2-.4.1-1 .1-1.6-.1-.4-.1-.9-.3-1.5-.6-2.6-1.1-4.3-3.8-4.5-4-.1-.2-1-1.4-1-2.6 0-1.2.6-1.8.9-2.1.2-.2.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 1.9c.1.2.1.3 0 .5l-.4.5c-.1.1-.3.3-.1.5.1.3.6 1 1.3 1.6.9.8 1.6 1 1.9 1.2.2.1.4.1.5-.1l.6-.7c.2-.2.3-.2.5-.1l1.8.9c.3.1.4.2.5.3.1.2.1.7-.1 1.3Z" fill="var(--c-on-accent)"/></svg>`),
  waOutline: (s = 16) => svg(`<svg width="${s}" height="${s}" viewBox="0 0 32 32"><path d="M16 6a8 8 0 0 0-6.9 12.1L8 22l4-1.1A8 8 0 1 0 16 6Z" fill="none" stroke="var(--c-accent)" stroke-width="2"/></svg>`),
  copy: (s = 16) => svg(`<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h8"/></svg>`),
  chevron: (s = 16) => svg(`<svg class="chev" width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`),
  chevronRight: (s = 18) => svg(`<svg class="chev" width="${s}" height="${s}" viewBox="0 0 16 16"><path d="M6 4l4 4-4 4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`),
  minus: (s = 18) => svg(`<svg width="${s}" height="${s}" viewBox="0 0 18 18"><path d="M4 9h10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>`),
  plus: (s = 18) => svg(`<svg width="${s}" height="${s}" viewBox="0 0 18 18"><path d="M9 4v10M4 9h10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>`),
  check: (s = 16, c = 'var(--c-on-accent)') => svg(`<svg width="${s}" height="${s}" viewBox="0 0 20 20"><path d="M4 10l4 4 8-9" fill="none" stroke="${c}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>`),
  x: (s = 15) => svg(`<svg width="${s}" height="${s}" viewBox="0 0 20 20"><path d="M5 5l10 10M15 5L5 15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>`),
  info: (s = 14) => svg(`<svg class="info" width="${s}" height="${s}" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M8 7v4M8 5h.01" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>`),
  edit: (s = 18) => svg(`<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M13.5 5.5l5 5"/><path d="M4 20l1.2-4.2L16 5a2.1 2.1 0 0 1 3 3L8.2 18.8 4 20Z"/></svg>`),
  qmark: (s = 8) => svg(`<svg width="${s}" height="${s}" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.1"><path d="M5.4 6a2.6 2.6 0 1 1 3.6 2.4c-.8.4-1.1.9-1.1 1.7" stroke-linecap="round"/><circle cx="7.9" cy="13" r="1.05" fill="currentColor" stroke="none"/></svg>`),
  filter: (s = 18) => svg(`<svg width="${s}" height="${s}" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="6" cy="6" r="2"/><circle cx="14" cy="14" r="2"/><path d="M8 6h8M4 14h8" stroke-linecap="round"/></svg>`),
  refresh: (s = 16) => svg(`<svg width="${s}" height="${s}" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M16 6.5A6.5 6.5 0 0 0 5.1 4.1L4 5.2"/><path d="M4 2v3.2h3.2"/><path d="M4 13.5a6.5 6.5 0 0 0 10.9 2.4L16 14.8"/><path d="M16 18v-3.2h-3.2"/></svg>`),
  video: (s = 16) => svg(`<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="6" width="13" height="12" rx="2"/><path d="M15 10l6-3v10l-6-3"/></svg>`),
  cric: (s = 16) => svg(`<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="9"/><path d="M5 9c4 1 10 1 14 0M5 15c4-1 10-1 14 0"/></svg>`),
  inbox: (s = 30) => svg(`<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 13l2.5-7h13L21 13M3 13v5a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1v-5M3 13h5l1.5 2.5h5L16 13h5"/></svg>`),
};

/* progress ring node */
function ringNode(pct, size = 28) {
  const r = size / 2 - 3, c = 2 * Math.PI * r;
  return svg(`<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    <circle cx="${size/2}" cy="${size/2}" r="${r}" fill="none" stroke="var(--c-border-strong)" stroke-width="3"/>
    <circle cx="${size/2}" cy="${size/2}" r="${r}" fill="none" stroke="var(--c-accent)" stroke-width="3"
      stroke-linecap="round" stroke-dasharray="${c}" stroke-dashoffset="${c * (1 - pct/100)}"
      transform="rotate(-90 ${size/2} ${size/2})"/></svg>`);
}

const fmtPrice = n => '₹' + n.toLocaleString('en-IN');
