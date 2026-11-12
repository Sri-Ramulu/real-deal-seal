<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api, setSession, evidenceLabel } from '$lib/api.js';
  import Arrow from '$lib/components/Arrow.svelte';
  import Standing from '$lib/components/Standing.svelte';

  // Onboarding in five screens: the business, its source, its catalog, its records, and what goes public.
  let step = $state(1), types = $state([]), error = $state(''), busy = $state(false), id = $state(null);
  let f = $state({ name: '', business_type: 'physical', category: '', region: 'US', sells: '', ships_from: '', returns_policy: '', email: '', password: '' });
  let conn = $state(null), catalogCsv = $state(''), ordersCsv = $state(''), catReport = $state(null), ordReport = $state(null), disc = $state(null);
  const steps = ['Your business', 'Connect a source', 'Your catalog', 'Your records', 'What goes public'];
  const type = $derived(types.find((t) => t.business_type === f.business_type));
  onMount(async () => (types = await api('/api/business-types')));

  async function run(fn) { busy = true; error = ''; try { await fn(); } catch (e) { error = e.message; } busy = false; }
  const create = () => run(async () => { const r = await api('/api/onboarding/workspaces', f); id = r.merchant_id; setSession({ token: r.token, merchant_id: id, role: 'owner' }); step = 2; });
  const connect = (provider) => run(async () => { conn = await api(`/api/studio/${id}/connect/${provider}`, {}); });
  const importCatalog = () => run(async () => { catReport = await api(`/api/studio/${id}/catalog/import`, { csv: catalogCsv }); });
  const importOrders = () => run(async () => { ordReport = await api(`/api/studio/${id}/orders/import`, { csv: ordersCsv }); disc = await api(`/api/studio/${id}/disclosure`); });
  const toPublic = () => run(async () => { disc = await api(`/api/studio/${id}/disclosure`); step = 5; });
  const publish = () => run(async () => { await api(`/api/studio/${id}/disclosure`, { publish: true, hidden_metrics: [] }); goto(`/studio/${id}`); });
</script>

<svelte:head><title>Open a workspace | Real Deal Seal</title></svelte:head>

<section class="wrap section narrow">
  <h1>Open a workspace</h1>
  <ol class="steps">{#each steps as s, i}<li class:on={step === i + 1} class:done={step > i + 1}><span class="num">{i + 1}</span>{s}</li>{/each}</ol>
  {#if error}<p class="notice err">{error}</p>{/if}

  {#if step === 1}
    <form class="card" onsubmit={(e) => { e.preventDefault(); create(); }}>
      <h2>Tell us about the business</h2>
      <div class="grid2">
        <label class="field">Business name <input class="input" bind:value={f.name} required minlength="2" /></label>
        <label class="field">What you sell, in a few words <input class="input" bind:value={f.sells} placeholder="Hand-thrown mugs" /></label>
      </div>
      <fieldset><legend class="label">What kind of business is it?</legend>
        <div class="types">{#each types as t}
          <label class:picked={f.business_type === t.business_type}><input type="radio" bind:group={f.business_type} value={t.business_type} />
            <strong>{t.business_type_label}</strong><span class="small">{t.examples}</span></label>{/each}</div></fieldset>
      {#if type}<div class="notice"><strong>You will be judged on these rules, and only these:</strong><ul>{#each type.rules as r}<li>{r}</li>{/each}</ul></div>{/if}
      <div class="grid2">
        <label class="field">Category <input class="input" bind:value={f.category} placeholder="Home goods" /></label>
        <label class="field">{f.business_type === 'physical' ? 'Ships from' : 'Based in'} <input class="input" bind:value={f.ships_from} placeholder="Boise, ID" /></label>
        <label class="field">Your email <input class="input" type="email" bind:value={f.email} required autocomplete="username" /></label>
        <label class="field">Choose a password (8 or more characters) <input class="input" type="password" bind:value={f.password} required minlength="8" autocomplete="new-password" /></label>
      </div>
      <button class="btn" disabled={busy}>Create the workspace <Arrow /></button>
    </form>

  {:else if step === 2}
    <div class="card"><h2>Where should your records come from?</h2>
      <p>You choose the source. Nothing is public yet, and you never paste a PayPal password or API secret here.</p>
      <div class="types two">
        <button class="choice" disabled={busy} onclick={() => connect('paypal')}><strong>Connect PayPal</strong><span class="small">Orders paid through PayPal are read back from PayPal and count as confirmed. Only these can earn the seal.</span></button>
        <button class="choice" disabled={busy} onclick={() => connect('records_import')}><strong>Use my own records</strong><span class="small">Upload a file of past orders. They are labeled "reported by the business" until PayPal confirms new ones.</span></button>
      </div>
      {#if conn}<p class="notice"><strong>{conn.provider.replace('_', ' ')}: {conn.status}.</strong> {conn.detail}</p>
        <button class="btn" onclick={() => (step = 3)}>Next: your catalog <Arrow /></button>{/if}
    </div>

  {:else if step === 3}
    <form class="card" onsubmit={(e) => { e.preventDefault(); importCatalog(); }}>
      <h2>What do you sell?</h2>
      <p class="small">Paste a CSV with this header: <code>sku,name,price_usd,stock,tags,description</code>. Separate tags with |. You can skip this and add products later.</p>
      <textarea class="input" rows="6" bind:value={catalogCsv} placeholder="sku,name,price_usd,stock,tags,description&#10;MUG-01,Speckled mug,28,40,mug|ceramic|gift,Hand-thrown stoneware mug"></textarea>
      <div class="row"><button class="btn black" disabled={busy || !catalogCsv.trim()}>Check and save</button><button type="button" class="btn ghost" onclick={() => (step = 4)}>{catReport ? 'Next: your records' : 'Skip for now'} <Arrow size={12} /></button></div>
      {#if catReport}<p class="notice"><strong>{catReport.accepted} saved, {catReport.rejected.length} rejected.</strong>{#each catReport.rejected as r}<br />Row {r.row}: {r.reason}{/each}</p>{/if}
    </form>

  {:else if step === 4}
    <form class="card" onsubmit={(e) => { e.preventDefault(); importOrders(); }}>
      <h2>Bring your order history</h2>
      <p class="small">Header: <code>order_id,order_date,amount_usd,status,buyer_ref,refunded_usd,fulfilled_days,tracking_ref,cancelled,dispute</code>. Every row is checked for duplicates, currency, dates and amounts. <code>buyer_ref</code> is turned into a one-way key and never stored.</p>
      <textarea class="input" rows="8" bind:value={ordersCsv} placeholder="order_id,order_date,amount_usd,status,buyer_ref,refunded_usd,fulfilled_days,tracking_ref,cancelled,dispute"></textarea>
      <div class="row"><button class="btn black" disabled={busy || !ordersCsv.trim()}>Check and import</button><button type="button" class="btn ghost" disabled={busy} onclick={toPublic}>{ordReport ? 'Next: what goes public' : 'Skip for now'} <Arrow size={12} /></button></div>
      {#if ordReport}<p class="notice"><strong>{ordReport.accepted} accepted, {ordReport.rejected.length} rejected.</strong> {ordReport.label}{#each ordReport.rejected.slice(0, 10) as r}<br />Row {r.row}: {r.reason}{/each}</p>{/if}
    </form>

  {:else if step === 5 && disc}
    <div class="card"><h2>This is what shoppers and AI agents would see</h2>
      {#if disc.has_record}
        <p><Standing standing={disc.standing.includes('sealed') && disc.standing.includes('Real') ? 'sealed' : disc.standing.includes('Self') ? 'reported' : disc.standing.includes('history') ? 'new' : 'verified'} headline={disc.standing} /></p><p>{disc.verdict}</p>
        <table class="plain"><tbody>{#each disc.facts as x}<tr><td>{x.label}<br /><span class="small">{evidenceLabel[x.evidence_class]}</span></td><td class="num">{x.value ?? '–'}{x.unit === '%' ? '%' : ''}{x.denominator ? ` (${x.numerator} of ${x.denominator})` : ''}</td></tr>{/each}</tbody></table>
        <p class="small"><strong>Never public:</strong> {disc.never_public.join(', ')}. {disc.rule}</p>
        <div class="row"><button class="btn" disabled={busy} onclick={publish}>Publish and issue my passport <Arrow /></button><a class="btn ghost" href="/studio/{id}">Not yet. Take me to my studio</a></div>
      {:else}
        <p>There are no records yet, so there is nothing to publish. That is fine: your workspace is ready, and facts appear as soon as there is something to count.</p>
        <a class="btn" href="/studio/{id}">Open my studio <Arrow /></a>
      {/if}
    </div>
  {/if}
</section>

<style>
  .narrow { max-width: 980px; } h1 { margin-bottom: 28px; } h2 { font-size: 1.9rem; }
  .steps { list-style: none; display: flex; gap: 2px; padding: 0; margin: 0 0 2px; flex-wrap: wrap; }
  .steps li { flex: 1; background: var(--tile); padding: 12px 14px; font-size: 0.9rem; font-weight: 600; color: var(--muted); display: flex; gap: 10px; align-items: center; white-space: nowrap; }
  .steps li .num { width: 24px; height: 24px; border-radius: 50%; display: grid; place-items: center; background: #fff; font-size: 0.8rem; }
  .steps li.on { background: var(--ink); color: #fff; } .steps li.on .num { background: var(--red); color: #fff; } .steps li.done .num { background: var(--ink); color: #fff; }
  .card { display: grid; gap: 18px; padding: 36px; } .card .input { background: #fff; } .card p { margin: 0; }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  fieldset { border: 0; padding: 0; margin: 0; display: grid; gap: 8px; }
  .types { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2px; } .types.two { grid-template-columns: 1fr 1fr; }
  .types label, .choice { background: #fff; padding: 16px; display: grid; gap: 6px; cursor: pointer; border: 0; text-align: left; align-content: start; box-shadow: inset 0 0 0 1.5px transparent; transition: 0.2s; }
  .types label.picked { box-shadow: inset 0 0 0 2px var(--red); } .types input { position: absolute; opacity: 0; }
  .types label:focus-within { outline: 3px solid var(--ink); } .choice:hover { background: var(--ink); color: #fff; } .choice:hover .small { color: #ddd; }
  .notice ul { margin: 8px 0 0; padding-left: 18px; } .row { display: flex; gap: 10px; flex-wrap: wrap; }
  @media (max-width: 800px) { .grid2, .types, .types.two { grid-template-columns: 1fr; } .steps li { flex: none; } }
</style>
