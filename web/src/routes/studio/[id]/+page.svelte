<script>
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { api, usd, evidenceLabel, setSession, typeNoun } from '$lib/api.js';
  import Standing from '$lib/components/Standing.svelte';
  import Columns from '$lib/components/Columns.svelte';
  import EvidenceGrid from '$lib/components/EvidenceGrid.svelte';
  import Arrow from '$lib/components/Arrow.svelte';

  let d = $state(null), rows = $state([]), ops = $state(null), disc = $state(null), stmt = $state(null);
  let error = $state(''), note = $state(''), busy = $state(false), filter = $state(null), grid = $state();
  let track = $state({}), share = $state({ recipient: '', purpose: '' }), shared = $state(null), csv = $state({ catalog: '', orders: '' }), report = $state(null);
  const id = $derived(page.params.id);
  const tab = $derived(page.url.searchParams.get('tab') ?? 'overview');
  // Catalog, Business readiness and Sources are hidden for the hackathon submission; the code stays. Empty HIDDEN_TABS to show them.
  const HIDDEN_TABS = ['catalog', 'readiness', 'settings'];
  const tabs = [['overview', 'Overview'], ['passport', 'Passport'], ['evidence', 'Evidence'], ['coach', 'Coach'], ['orders', 'Orders'], ['catalog', 'Catalog'], ['readiness', 'Business readiness'], ['settings', 'Sources']]
    .filter(([k]) => !HIDDEN_TABS.includes(k));

  async function load() {
    error = '';
    try {
      d = await api(`/api/studio/${id}`);
      if (tab === 'evidence' || tab === 'coach') rows = await api(`/api/studio/${id}/evidence`);
      if (tab === 'orders') ops = await api(`/api/studio/${id}/operations`);
      if (tab === 'passport') disc = await api(`/api/studio/${id}/disclosure`);
      if (tab === 'readiness' && d.passport?.has_record) stmt = await api(`/api/studio/${id}/statement`);
    } catch (e) { if (e.status === 401 || e.status === 403) goto('/studio'); else error = e.message; }
  }
  $effect(() => { id; tab; load(); });
  async function act(fn, done) { busy = true; error = ''; note = ''; try { const r = await fn(); note = done?.(r) ?? ''; await load(); return r; } catch (e) { error = e.message; } finally { busy = false; } }

  const p = $derived(d?.passport);
  const noun = $derived(typeNoun[p?.business_type] ?? 'orders');
  const headline = $derived(!p?.has_record ? 'Your workspace is ready. Add your records to see where you stand.'
    : p.standing === 'sealed' ? `Sealed: all ${p.rules_total} rules met on your last ${p.recent_orders} ${noun}`
    : p.standing === 'new' ? `${Math.max(0, 30 - p.orders_completed)} more ${noun} and ${Math.max(0, 60 - p.history_days)} more days to a full record`
    : p.standing === 'reported' ? `Your own records meet ${p.rules_met} of ${p.rules_total} rules. PayPal has not confirmed them yet`
    : `${p.rules_total - p.rules_met} of ${p.rules_total} rules stand between you and the seal`);
  const ruleFacts = $derived(d ? d.rules.filter((r) => r.rule !== 'enough_history').map((r) => ({ ...r, fact: d.facts.find((f) => f.metric === r.metric) })) : []);
  const quality = $derived(d?.facts.find((f) => f.metric === 'confirmed_payment_share'));
  const coachFilter = { tracking: 'missing_tracking', fast_ship: 'slow', refunds: 'refunded', disputes: 'lost', completion: 'not_fulfilled', delivery: 'not_fulfilled', cancellations: 'cancelled' };
  const go = (t, f = null) => { filter = f; goto(`/studio/${id}?tab=${t}`, { noScroll: true }); };
  const signOut = () => { setSession(null); goto('/studio'); };
  const hidden = $derived(new Set(disc?.facts.filter((f) => !f.disclosed).map((f) => f.metric)));
  const toggleFact = (m) => act(() => api(`/api/studio/${id}/disclosure`, { publish: disc.published, hidden_metrics: hidden.has(m) ? [...hidden].filter((x) => x !== m) : [...hidden, m] }));
  const needText = (r) => `Needs ${r.threshold}% or ${r.comparison === '>=' ? 'more' : 'less'}`;
</script>

<svelte:head><title>{d?.merchant.name ?? 'Studio'} | Merchant Studio</title></svelte:head>

<section class="wrap section-tight">
  {#if d}
    <div class="top">
      <div><span class="label">Merchant Studio · {d.merchant.name} · {p?.business_type_label ?? d.merchant.business_type}</span><h1>{headline}</h1></div>
      <div class="side">{#if p?.has_record}<Standing standing={p.standing} headline={p.headline} />{/if}
        <p class="small">{p?.has_record ? `Records as of ${p.data_as_of}. Rules ${p.criteria_version}.` : ''} {d.merchant.passport_published ? 'Passport is public.' : 'Passport is not public.'}</p>
        <button class="link" onclick={signOut}>Sign out</button></div>
    </div>
    <nav class="tabs" aria-label="Studio sections">{#each tabs as [k, label]}<a href="/studio/{id}?tab={k}" aria-current={tab === k ? 'page' : undefined} data-sveltekit-noscroll>{label}</a>{/each}</nav>
    {#if error}<p class="notice err">{error}</p>{/if}
    {#if note}<p class="notice">{note}</p>{/if}

    {#if !p?.has_record && !['settings', 'catalog', 'passport'].includes(tab)}
      <div class="empty card"><h2>No records yet</h2><p>{d.pending ?? 'Import your order records or take a PayPal order. Facts appear here as soon as there is something to count.'}</p>
        {#if !HIDDEN_TABS.includes('settings')}<a class="btn" href="/studio/{id}?tab=settings">Add your records <Arrow /></a>{/if}</div>

    {:else if tab === 'overview'}
      <div class="tiles" style="--n:{ruleFacts.length + 1}">
        <div class="kpi"><span class="label">Net sales</span><span class="num v">{usd(p.net_sales_usd)}</span><span class="small">{p.orders_completed} completed {noun} over {p.history_days} days</span></div>
        {#each ruleFacts as r}
          <button class="kpi click" class:miss={!r.met} onclick={() => go('evidence', r.metric)}>
            <span class="label">{r.fact?.label}</span>
            <span class="num v">{r.measured_value ?? '–'}{r.measured ? '%' : ''}</span>
            <span class="small">{r.numerator} of {r.denominator}. {needText(r)}</span>
            <span class="tag">{evidenceLabel[r.evidence_class]}</span>
            <span class="open">See the {noun} <Arrow size={11} /></span>
          </button>
        {/each}
      </div>
      <div class="two">
        <div class="panel">
          <h2>{d.coach.length ? `${d.coach.length} ${d.coach.length === 1 ? 'thing' : 'things'} to do next` : 'Nothing to fix. Keep it up.'}</h2>
          {#each d.coach.slice(0, 3) as a}<article class="act"><div><h3>{a.title}</h3><p class="small">{a.rule_label}. Now: <strong>{a.now}</strong>.{a.to_meet_rule ? ` ${a.to_meet_rule}.` : ''}</p></div></article>{/each}
          {#if d.coach.length}<a class="btn black" href="/studio/{id}?tab=coach">Open the coach <Arrow size={12} /></a>{:else}<p>Every rule is met. The seal renews each time the record is refreshed.</p>{/if}
        </div>
        <div class="panel">
          <h2>{noun[0].toUpperCase() + noun.slice(1)} each week</h2>
          <Columns points={d.weekly} valueKey="orders" labelKey="week_start" format={(v) => `${v} ${noun}`} />
          {#if quality}<p class="quality"><strong>{quality.numerator} of {quality.denominator}</strong> recent payments are confirmed by PayPal records. {quality.value < 100 ? 'The rest are your own imported records, which cannot earn the seal.' : ''}</p>{/if}
        </div>
      </div>

    {:else if tab === 'passport' && disc}
      <div class="two">
        <div class="panel">
          <h2>{disc.published ? 'Your passport is public' : 'Your passport is not public'}</h2>
          <p>{disc.published ? 'Shoppers and AI agents can read the facts on the right, and your products appear in search.' : 'Nothing about your business is shown to shoppers or agents until you publish.'}</p>
          <div class="row">
            {#if disc.published}
              <button class="btn black" disabled={busy} onclick={() => act(() => api(`/api/studio/${id}/disclosure`, { publish: false, hidden_metrics: [...hidden] }), () => 'Withdrawn. Your seal no longer checks out, and shoppers see that you took your record down.')}>Withdraw the passport</button>
              <a class="btn ghost" href="/shops/{id}">See the public page <Arrow size={12} /></a>
            {:else}
              <button class="btn" disabled={busy || !disc.has_record} onclick={() => act(() => api(`/api/studio/${id}/disclosure`, { publish: true, hidden_metrics: [...hidden] }), () => 'Published. Your signed passport is live.')}>Publish and issue the passport <Arrow size={12} /></button>
            {/if}
          </div>
          <h3 class="sub">Never public</h3>
          <ul>{#each disc.never_public as n}<li>{n}</li>{/each}</ul>
          <p class="small">{disc.rule}</p>
        </div>
        <div class="panel">
          <h2>What the public sees</h2>
          <p><Standing standing={p?.standing ?? 'no_record'} headline={disc.standing} /></p><p>{disc.verdict}</p>
          <table class="plain"><tbody>
            {#each disc.facts as f}
              <tr class:off={!f.disclosed}><td>{f.label}<br /><span class="small">{evidenceLabel[f.evidence_class]}</span></td>
                <td class="num">{f.value ?? '–'}{f.unit === '%' ? '%' : ''}{f.denominator ? ` (${f.numerator} of ${f.denominator})` : ''}</td>
                <td>{#if f.is_optional_to_disclose}<button class="link" disabled={busy} onclick={() => toggleFact(f.metric)}>{f.disclosed ? 'Hide' : 'Show'}</button>{:else}<span class="small">Always shown</span>{/if}</td></tr>
            {/each}
          </tbody></table>
        </div>
      </div>

    {:else if tab === 'evidence'}
      <div class="ehead"><h2>{filter ? `The ${noun} behind that number` : `Every one of your ${noun}, behind every number`}</h2>
        <div class="row">{#if filter}<button class="btn ghost" onclick={() => (filter = null)}>Show all</button>{/if}<button class="btn ghost" onclick={() => grid.exportCsv()}>Export CSV</button></div></div>
      <EvidenceGrid bind:this={grid} {rows} {filter} />
      <p class="source">Only you can see these rows. Buyer names, emails and addresses are never stored. Red cells count against a rule.</p>

    {:else if tab === 'coach'}
      <div class="two">
        <div class="panel">
          <h2>{d.coach.length ? 'What to do next' : 'Nothing to fix'}</h2>
          {#each d.coach as a}
            <article class="act block">
              <h3>{a.title}</h3><p>{a.why}</p>
              <p class="small">Rule: {a.rule_label}. Now: <strong>{a.now}</strong>.{a.to_meet_rule ? ` ${a.to_meet_rule}.` : ''}</p>
              {#if a.can_do_here === 'add_tracking'}
                <div class="fix">
                  {#each a.order_ids.slice(0, 4) as oid}
                    {@const o = rows.find((r) => r.order_id === oid)}
                    <form onsubmit={(e) => { e.preventDefault(); act(() => api(`/api/studio/${id}/coach/add-tracking`, { order_id: oid, tracking_number: track[oid] }), (r) => `Recorded. Tracking went from ${r.before.numerator} of ${r.before.denominator} to ${r.after.numerator} of ${r.after.denominator}${r.sent_to_paypal ? ' and was sent to PayPal' : ''}. It is labeled as reported by you.`); }}>
                      <span class="small">Order {o?.order_no ?? ''} · {o?.order_date ?? ''} · {o ? usd(o.amount_usd, 2) : ''}</span>
                      <input class="input" placeholder="Carrier tracking number" bind:value={track[oid]} minlength="6" required />
                      <button class="btn black" disabled={busy}>Add tracking</button>
                    </form>
                  {/each}
                  {#if a.order_ids.length > 4}<p class="small">{a.order_ids.length - 4} more after these.</p>{/if}
                </div>
              {:else if a.orders_to_review}<button class="btn ghost" onclick={() => go('evidence', coachFilter[a.rule])}>Review {a.orders_to_review} {noun} <Arrow size={12} /></button>{/if}
            </article>
          {/each}
          {#if !d.coach.length}<p>Every published rule for your business type is met.</p>{/if}
        </div>
        <div class="panel">
          <h2>What you have done</h2>
          {#if !d.coach_history.length}<p>Each fix you make here is recorded with the number before and after.</p>{/if}
          <table class="plain"><tbody>{#each d.coach_history as hrow}<tr><td>{hrow.kind.replace('_', ' ')}<br /><span class="small">{hrow.created_at.slice(0, 10)} · {hrow.detail}</span></td><td class="num">{hrow.before_value}<br />→ <strong>{hrow.after_value ?? '…'}</strong></td><td>{hrow.status === 'verified' ? '✓ Verified' : 'Recorded'}</td></tr>{/each}</tbody></table>
        </div>
      </div>

    {:else if tab === 'orders' && ops}
      <h2 class="mt">Your last {ops.orders.length} {noun}</h2>
      <p class="small legend"><i class="dot"></i> paid <i class="bar"></i> days to fulfil <i class="trk"></i> tracking on record <i class="x"></i> refunded or cancelled. The scale is 0 to 7 days.</p>
      <div class="timeline">
        {#each ops.orders as o}
          <div class="trow" class:bad={o.is_refunded || o.cancelled_by_business}>
            <span class="small">#{o.order_no} · {o.order_date}</span><span class="num">{usd(o.amount_usd, 2)}</span>
            <span class="lane"><i class="dot"></i>{#if o.is_fulfilled}<i class="bar" class:slow={o.fulfil_days > 2} style="width:{Math.min(100, (o.fulfil_days / 7) * 100)}%"></i>{#if o.has_tracking}<i class="trk" style="left:{Math.min(100, (o.fulfil_days / 7) * 100)}%"></i>{/if}{/if}</span>
            <span class="small">{o.cancelled_by_business ? 'Cancelled by you' : o.is_refunded ? 'Refunded' : o.is_fulfilled ? `${o.fulfil_days === 0 ? 'Same day' : o.fulfil_days + (o.fulfil_days === 1 ? ' day' : ' days')}${p.business_type === 'physical' ? (o.has_tracking ? ', tracked' : ', no tracking') : ''}` : 'Not fulfilled yet'}</span>
          </div>
        {/each}
      </div>
      <div class="two gap">
        <div class="panel"><h2>Checkouts opened here</h2>
          {#if !ops.checkouts.length}<p>No one has opened a checkout for your products yet.</p>{/if}
          <table class="plain"><tbody>{#each ops.checkouts as c}<tr><td>{c.sku} × {c.quantity}<br /><span class="small">{c.created_at.slice(0, 16).replace('T', ' ')} · {c.mode === 'simulated' ? 'simulated, not counted as evidence' : 'PayPal sandbox'}</span></td><td class="num">{usd(c.amount_usd, 2)}</td><td>{c.status}</td></tr>{/each}</tbody></table></div>
        <div class="panel"><h2>Activity log</h2><table class="plain"><tbody>{#each ops.audit.slice(0, 12) as a}<tr><td class="small">{a.at.slice(0, 16).replace('T', ' ')}</td><td>{a.action}</td><td class:err={a.result !== 'ok'}>{a.result}</td></tr>{/each}</tbody></table></div>
      </div>

    {:else if tab === 'catalog'}
      <div class="two">
        <div class="panel"><h2>{(d.products.length || d.catalog.length)} products on offer</h2>
          <table class="plain"><thead><tr><th>SKU</th><th>Name</th><th>Price</th><th>Stock</th></tr></thead>
            <tbody>{#each (d.products.length ? d.products : d.catalog.map((c) => ({ ...c, product_name: c.name }))) as c}<tr><td><code>{c.sku}</code></td><td>{c.product_name}</td><td class="num">{usd(c.price_usd, 2)}</td><td class="num">{c.stock}</td></tr>{/each}</tbody></table></div>
        <form class="panel" onsubmit={(e) => { e.preventDefault(); act(async () => (report = await api(`/api/studio/${id}/catalog/import`, { csv: csv.catalog })), (r) => `${r.accepted} items saved, ${r.rejected.length} rejected.`); }}>
          <h2>Add or update products</h2><p class="small">Paste a CSV with the header <code>sku,name,price_usd,stock,tags,description</code>. Separate tags with |.</p>
          <textarea class="input" rows="7" bind:value={csv.catalog} placeholder="sku,name,price_usd,stock,tags,description" required></textarea>
          <button class="btn black" disabled={busy}>Import products</button>
          {#if report?.rejected?.length}<ul class="small">{#each report.rejected as r}<li>Row {r.row}: {r.reason}</li>{/each}</ul>{/if}
        </form>
      </div>

    {:else if tab === 'readiness' && stmt}
      {@const s = stmt.statement.credentialSubject}
      <div class="two">
        <div class="panel"><h2>Statement of commercial records</h2>
          <p class="small">Signed by Real Deal Seal. An evidence record, not a credit score or a lending decision.</p>
          <table class="plain"><thead><tr><th>Month</th><th>{noun}</th><th>Captured</th><th>Refunded</th><th>Net</th><th>PayPal-confirmed</th></tr></thead>
            <tbody>{#each s.months as m}<tr><td>{m.month}</td><td class="num">{m.orders}</td><td class="num">{usd(m.capturedUsd)}</td><td class="num">{usd(m.refundedUsd)}</td><td class="num">{usd(m.netUsd)}</td><td class="num">{m.paypalConfirmedOrders} of {m.orders}</td></tr>{/each}
              <tr class="total"><td>Total</td><td class="num">{s.totals.orders}</td><td class="num">{usd(s.totals.capturedUsd)}</td><td class="num">{usd(s.totals.refundedUsd)}</td><td class="num">{usd(s.totals.netUsd)}</td><td class="num">{s.totals.paypalConfirmedOrders} of {s.totals.orders}</td></tr></tbody></table>
          {#if s.correctiveActions.length}<h3 class="sub">Improvements on record</h3><ul>{#each s.correctiveActions as a}<li>{a.action.replace('_', ' ')}: {a.before} → {a.after}</li>{/each}</ul>{/if}
          <h3 class="sub">Limits stated on the document</h3><ul class="small">{#each s.limitations as l}<li>{l}</li>{/each}</ul>
        </div>
        <div class="panel">
          <h2>Share it with one recipient</h2>
          <form onsubmit={(e) => { e.preventDefault(); act(async () => (shared = await api(`/api/studio/${id}/statement/share`, share)), () => 'Link created. Copy it now: it is shown once.'); }}>
            <label class="field">Who is it for <input class="input" bind:value={share.recipient} placeholder="Harbor Community Bank" required /></label>
            <label class="field">What is it for <input class="input" bind:value={share.purpose} placeholder="Business account review" required /></label>
            <button class="btn" disabled={busy}>Create a private link <Arrow size={12} /></button>
          </form>
          {#if shared}<p class="notice"><strong>For {shared.recipient}:</strong><br /><a href={shared.share_url}>{shared.share_url}</a></p>{/if}
          <h3 class="sub">Who can see it</h3>
          {#if !stmt.shares.length}<p class="small">No one. You have not shared a statement.</p>{/if}
          <table class="plain"><tbody>{#each stmt.shares as g}<tr><td>{g.recipient}<br /><span class="small">{g.purpose} · {g.granted_at.slice(0, 10)}</span></td>
            <td>{#if g.revoked_at}<span class="small">Withdrawn {g.revoked_at.slice(0, 10)}</span>{:else}<button class="link" onclick={() => act(() => api(`/api/studio/${id}/statement/shares/${g.grant_id}/revoke`, {}), () => 'Withdrawn. The link no longer opens.')}>Take it back</button>{/if}</td></tr>{/each}</tbody></table>
        </div>
      </div>

    {:else if tab === 'settings'}
      <div class="two">
        <div class="panel"><h2>Where your records come from</h2>
          <table class="plain"><tbody>{#each d.connections as c}<tr><td><strong>{c.provider.replace('_', ' ')}</strong><br /><span class="small">{c.detail}</span></td><td>{c.status}</td></tr>{/each}</tbody></table>
          {#if !d.connections.length}<p>No source connected yet.</p>{/if}
          <div class="row"><button class="btn black" disabled={busy} onclick={() => act(() => api(`/api/studio/${id}/connect/paypal`, {}), (r) => r.detail)}>Connect PayPal</button>
            <button class="btn ghost" disabled={busy} onclick={() => act(() => api(`/api/studio/${id}/connect/records_import`, {}), (r) => r.detail)}>Use my own records</button>
            <button class="btn ghost" disabled={busy} onclick={() => act(() => api(`/api/studio/${id}/refresh`, {}), (r) => (r.ok ? 'Updated just now.' : `The refresh failed and your last good figures were kept: ${r.error}`))}>Refresh now</button></div>
          <h3 class="sub">Imports</h3>
          {#if !d.imports.length}<p class="small">Nothing imported yet.</p>{/if}
          <table class="plain"><tbody>{#each d.imports as i}<tr><td>{i.kind}<br /><span class="small">{i.retrieved_at.slice(0, 16).replace('T', ' ')} · sha256 {i.sha256.slice(0, 12)}…</span></td><td class="num">{i.rows_accepted} accepted<br />{i.rows_rejected} rejected</td></tr>{/each}</tbody></table>
        </div>
        <form class="panel" onsubmit={(e) => { e.preventDefault(); act(async () => (report = await api(`/api/studio/${id}/orders/import`, { csv: csv.orders })), (r) => `${r.accepted} ${noun} accepted, ${r.rejected.length} rejected. ${r.label}`); }}>
          <h2>Import order records</h2>
          <p class="small">Header: <code>order_id,order_date,amount_usd,status,buyer_ref,refunded_usd,fulfilled_days,tracking_ref,cancelled,dispute</code>. Each row is checked; rejected rows come back with the reason. Imported records are labeled as reported by you.</p>
          <textarea class="input" rows="8" bind:value={csv.orders} placeholder="order_id,order_date,amount_usd,..." required></textarea>
          <button class="btn black" disabled={busy}>Check and import</button>
          {#if report?.rejected?.length}<ul class="small">{#each report.rejected.slice(0, 12) as r}<li>Row {r.row}: {r.reason}</li>{/each}</ul>{/if}
        </form>
      </div>
    {/if}
  {:else if error}<p class="notice err">{error}</p>
  {:else}<p>Opening the studio.</p>{/if}
</section>

<style>
  .top { display: grid; grid-template-columns: 1fr auto; gap: 32px; align-items: end; margin-bottom: 28px; }
  h1 { font-size: clamp(1.9rem, 4vw, 3.3rem); margin-top: 6px; max-width: 22ch; }
  .side { display: grid; gap: 8px; justify-items: end; text-align: right; }
  .link { background: none; border: 0; cursor: pointer; padding: 0; text-decoration: underline; }
  .tabs { margin-bottom: 2px; }
  .tiles { display: grid; grid-template-columns: repeat(var(--n), 1fr); gap: 2px; margin-top: 2px; }
  .kpi { background: var(--tile); padding: 22px; display: grid; gap: 4px; align-content: start; text-align: left; border: 0; color: inherit; position: relative; }
  .kpi .v { font-size: clamp(2.1rem, 3.4vw, 3.1rem); font-weight: 300; color: var(--ink); line-height: 1.05; }
  .kpi.click { cursor: pointer; transition: background 0.25s var(--ease); padding-bottom: 46px; }
  .kpi.miss .v { color: var(--red); } .kpi.miss { box-shadow: inset 0 4px 0 var(--red); }
  .kpi.click:hover { background: var(--ink); color: #fff; } .kpi.click:hover :is(.v, .label, .small, .tag) { color: #fff; }
  .tag { font-size: 0.74rem; font-weight: 600; margin-top: 8px; color: var(--muted); }
  .open { position: absolute; left: 22px; bottom: 16px; font-size: 0.82rem; font-weight: 600; display: flex; gap: 8px; align-items: center; opacity: 0.55; }
  .two { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 2px; margin-top: 2px; } .two.gap { margin-top: 40px; }
  .panel { background: var(--tile); padding: 30px; display: grid; gap: 14px; align-content: start; }
  .panel .input { background: #fff; } .panel p { margin: 0; }
  h2 { font-size: clamp(1.4rem, 2.3vw, 1.9rem); font-weight: 400; }
  .act { padding: 14px 0; border-top: 1px solid var(--line); } .act.block { display: grid; gap: 10px; } .act p { margin: 0; }
  .fix { display: grid; gap: 8px; } .fix form { display: grid; grid-template-columns: 1fr 1.2fr auto; gap: 8px; align-items: center; }
  .fix .btn, .row .btn, .ehead .btn { padding: 11px 15px; font-size: 0.9rem; }
  .row { display: flex; gap: 8px; flex-wrap: wrap; }
  .sub { margin-top: 14px; } .mt { margin-top: 28px; } ul { margin: 0; padding-left: 18px; display: grid; gap: 5px; }
  .quality { font-size: 0.95rem; } tr.off td { opacity: 0.45; } tr.total td { font-weight: 700; border-top: 1.5px solid var(--ink); }
  .ehead { display: flex; justify-content: space-between; align-items: end; gap: 20px; flex-wrap: wrap; margin: 28px 0 8px; }
  .empty { margin-top: 2px; padding: 48px; display: grid; gap: 14px; justify-items: start; }
  .legend { margin: 6px 0 14px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; max-width: none; }
  .legend i { position: static !important; display: inline-block; margin-left: 12px; }
  .timeline { display: grid; gap: 2px; }
  .trow { display: grid; grid-template-columns: 170px 80px 1fr 190px; gap: 16px; align-items: center; background: var(--tile); padding: 9px 16px; }
  .trow.bad { background: repeating-linear-gradient(135deg, var(--tile) 0 8px, #e9e9e9 8px 9px); }
  .lane { position: relative; height: 14px; display: block; border-left: 1.5px solid var(--ink); }
  i.dot { width: 10px; height: 10px; border-radius: 50%; background: var(--ink); position: absolute; left: -6px; top: 2px; }
  i.bar { height: 6px; background: var(--ink); position: absolute; left: 0; top: 4px; border-radius: 0 3px 3px 0; min-width: 4px; } i.bar.slow { background: var(--red); }
  i.trk { width: 9px; height: 9px; background: #fff; box-shadow: inset 0 0 0 2.5px var(--ink); position: absolute; top: 2.5px; margin-left: 4px; transform: rotate(45deg); }
  i.x { width: 14px; height: 10px; background: repeating-linear-gradient(135deg, #fff 0 3px, #999 3px 4px); }
  .legend i.bar { width: 26px; } .legend i.dot { margin-left: 0; }
  @media (max-width: 1100px) { .tiles { grid-template-columns: repeat(2, 1fr); } .two, .top { grid-template-columns: 1fr; } .side { justify-items: start; text-align: left; } .trow { grid-template-columns: 1fr 70px; } .trow .lane { grid-column: 1 / -1; } .fix form { grid-template-columns: 1fr; } }
</style>
