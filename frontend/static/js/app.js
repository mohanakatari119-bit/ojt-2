const API_BASE = '';

function getApiKey() { return localStorage.getItem('api_key') || ''; }
function setApiKey(k) { localStorage.setItem('api_key', k); }
function clearApiKey() { localStorage.removeItem('api_key'); }

async function apiFetch(path, opts = {}) {
  const key = getApiKey();
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  if (key) headers['Authorization'] = `Bearer ${key}`;
  const res = await fetch(API_BASE + path, { ...opts, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw Object.assign(new Error(err.detail || 'API error'), { status: res.status });
  }
  if (res.status === 204) return null;
  return res.json();
}

function statusBadge(code) {
  if (!code) return `<span class="badge badge-gray">—</span>`;
  const cls = code < 300 ? 'green' : code < 400 ? 'blue' : code < 500 ? 'yellow' : 'red';
  return `<span class="badge badge-${cls}">${code}</span>`;
}

function methodPill(m) {
  const cls = ['GET','POST','PUT','PATCH','DELETE'].includes(m) ? m : 'default';
  return `<span class="method method-${cls}">${m}</span>`;
}

function latencyBadge(ms) {
  if (ms == null) return `<span class="text-muted">—</span>`;
  const cls = ms < 200 ? 'green' : ms < 1000 ? 'yellow' : 'red';
  return `<span class="badge badge-${cls}">${ms.toFixed(0)} ms</span>`;
}

function relTime(iso) {
  const d = new Date(iso);
  const diff = (Date.now() - d) / 1000;
  if (diff < 60) return `${Math.round(diff)}s ago`;
  if (diff < 3600) return `${Math.round(diff/60)}m ago`;
  if (diff < 86400) return `${Math.round(diff/3600)}h ago`;
  return d.toLocaleDateString();
}

function fmtJSON(obj) {
  if (!obj) return '—';
  try { return JSON.stringify(typeof obj === 'string' ? JSON.parse(obj) : obj, null, 2); }
  catch { return String(obj); }
}

function showNotice(el, msg, type = 'error') {
  el.innerHTML = `<div class="notice notice-${type}">${msg}</div>`;
}

function buildSidebar(active) {
  const links = [
    { id: 'logs',    href: '/dashboard',   label: 'Logs'    },
    { id: 'metrics', href: '/metrics-ui',  label: 'Metrics' },
    { id: 'alerts',  href: '/alerts-ui',   label: 'Alerts'  },
  ];
  const items = links.map(l => `
    <a href="${l.href}" class="nav-link ${active === l.id ? 'active' : ''}">${l.label}</a>
  `).join('');

  return `
  <aside class="sidebar">
    <div class="sidebar-logo">
      <div class="logo-text">API Monitor</div>
    </div>
    <nav class="sidebar-nav">
      <div class="nav-section">Monitor</div>
      ${items}
      <div class="nav-section">More</div>
      <a href="/docs" target="_blank" class="nav-link">API Docs</a>
    </nav>
  </aside>`;
}

function guardAuth() {
  if (!getApiKey() && !window.location.pathname.endsWith('/')) {
    window.location.href = '/';
  }
}
