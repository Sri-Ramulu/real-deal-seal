// One place that talks to the API. Errors come back as plain messages the page can show.
// A merchant's session token lives in sessionStorage (cleared when the tab closes); reads and writes are guarded.
const KEY = 'rds-session';

export function session() {
  try { return JSON.parse(sessionStorage.getItem(KEY) || 'null'); } catch { return null; }
}
export function setSession(s) {
  try { s ? sessionStorage.setItem(KEY, JSON.stringify(s)) : sessionStorage.removeItem(KEY); } catch { /* storage unavailable: stay signed in for this page only */ }
  memory = s;
}
let memory = null;

export async function api(path, body, { method } = {}) {
  const s = session() || memory;
  const headers = { ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}), ...(s?.token ? { Authorization: `Bearer ${s.token}` } : {}) };
  const res = await fetch(path, { method: method ?? (body === undefined ? 'GET' : 'POST'), headers, body: body === undefined ? undefined : JSON.stringify(body) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.message || data.detail || `The server answered ${res.status}.`);
    err.status = res.status;
    throw err;
  }
  return data;
}

export const usd = (n, digits = 0) => '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });

export const evidenceLabel = {
  paypal_sandbox_confirmed: 'PayPal sandbox record',
  merchant_reported: 'Reported by the business',
  simulated: 'Simulated for the demo',
  missing: 'Nothing to measure yet'
};

export const typeNoun = { physical: 'orders', services: 'jobs', digital: 'sales', local: 'bookings' };

// '20261112T021525Z' -> '12 Nov 2026, 02:15 UTC'
export const runDate = (id) => {
  const m = /^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})/.exec(id ?? '');
  if (!m) return id ?? '';
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${+m[3]} ${months[+m[2] - 1]} ${m[1]}, ${m[4]}:${m[5]} UTC`;
};
export const modelName = (m) => { const [name, ...v] = m.replace('claude-', '').split('-'); return name[0].toUpperCase() + name.slice(1) + ' ' + v.join('.'); };
