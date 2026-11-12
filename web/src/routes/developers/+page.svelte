<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  let c = $state(null), tools = $state([]), pick = $state('gold.merchant_passport'), fact = $state('gold.fact_orders'), metric = $state(null), q = $state({ view: 'commerce_metrics', measure: 'net_usd', dim: 'merchant_id' });
  onMount(async () => { [c, tools] = await Promise.all([api('/api/platform'), api('/api/tools')]); run(); });
  async function run() { metric = await api(`/api/platform/metric?view=${q.view}&measures=${q.measure}&dimensions=${q.dim}`).catch((e) => ({ error: e.message })); }
  const origin = typeof location !== 'undefined' ? location.origin : '';
  const layers = ['landing', 'bronze', 'silver', 'gold'];
  const short = (id) => id.replace(/^landing\//, '').replace(/^(bronze|silver|gold)\./, '');
  const up = $derived.by(() => {
    if (!c) return new Set();
    const parents = {}; c.lineage.edges.forEach((e) => (parents[e.to] ??= []).push(e.from));
    const seen = new Set([pick]), st = [pick];
    while (st.length) for (const p of parents[st.pop()] ?? []) if (!seen.has(p)) { seen.add(p); st.push(p); }
    return seen;
  });
  const table = $derived(c?.tables.find((t) => t.name === pick));
  const view = $derived(c?.metric_views.find((v) => v.name === q.view));
  const rules = $derived(c ? c.contracts.flatMap((x) => x.rules) : []);
  const gold = $derived(c ? c.tables.filter((t) => t.layer === 'gold') : []);
  const facts = $derived(gold.filter((t) => t.name.includes('.fact_')));
  const serving = $derived(gold.filter((t) => !t.name.includes('.fact_') && !t.name.includes('.dim_')));
  const factTable = $derived(gold.find((t) => t.name === fact));
  const factDims = $derived(c ? gold.filter((t) => t.name.includes('.dim_') && factTable?.columns.some((col) => col.name.endsWith('_key') && t.key.includes(col.name === 'order_date_key' || col.name === 'event_date_key' ? 'date_key' : col.name.replace('chosen_', '')))) : []);
</script>

<svelte:head><title>Developers | Real Deal Seal</title></svelte:head>

<section class="wrap section">
  <h1>Developers</h1>
  <p class="lede top">Eight agent tools over MCP and REST, served from four data products. Each product has an owner, a contract, documented columns, governed metrics and lineage read from the SQL.</p>

  <h2>Connect an agent</h2>
  <div class="two">
    <div><p>Add the MCP server to any MCP client. The same tools are at <code>POST /api/tools/&#123;name&#125;</code> and an OpenAI-style endpoint at <code>/v1/chat/completions</code>.</p>
      <pre>{`{
  "mcpServers": {
    "real-deal-seal": { "type": "http", "url": "${origin}/mcp/" }
  }
}`}</pre>
      <p class="small" style="margin-top:12px">Interactive API reference: <a href="/docs">/docs</a>. OpenAPI contract: <a href="/openapi.json">/openapi.json</a>. A small Python client and a Postman collection are in <code>sdk/</code>. Issuer key: <a href="/api/issuer-key">/api/issuer-key</a>. DID: <a href="/.well-known/did.json">/.well-known/did.json</a>.</p></div>
    <table class="plain"><thead><tr><th>Tool</th><th>Use it to</th></tr></thead><tbody>{#each tools as t}<tr><td><code>{t.name}</code></td><td class="small">{t.description.split('. ')[0]}.</td></tr>{/each}</tbody></table>
  </div>

  <h2>Shops, checkout and the Evidence switch</h2>
  <div class="two">
    <div>
      <p>The demo has ten fictional shops. Every listing says how a shopper can buy it:</p>
      <table class="plain"><thead><tr><th>Shops</th><th>Record</th><th>How a shopper buys</th></tr></thead><tbody>
        <tr><td>Lydia Linen Co., Martha's Kitchen, Priscilla Canvas Works</td><td class="small">PayPal sandbox orders read back from PayPal</td><td class="small">PayPal sandbox checkout (test money); the shopper approves in PayPal</td></tr>
        <tr><td>Copper Kettle Supply, Sage &amp; Stone Studio</td><td class="small">Simulated records the business imported</td><td class="small">PayPal sandbox checkout once the shop's sandbox app keys are set (<code>PAYPAL_COPPER_KETTLE_SUPPLY_CLIENT_ID</code> and so on); a labelled simulated checkout until then</td></tr>
        <tr><td>Violet &amp; Vine Home, Juniper &amp; Oak Goods</td><td class="small">Simulated records; seal withdrawn for cause</td><td class="small">Can't buy here: seal withdrawn</td></tr>
        <tr><td>Babel Home, Hearthline Home, Linen Palace</td><td class="small">None: they never joined</td><td class="small">Can't buy here: doesn't take PayPal</td></tr>
      </tbody></table>
      <p class="small">The first seven have a Merchant Studio with a public demo login. The last three never joined, so they have no studio.</p>
    </div>
    <div>
      <p><code>POST /api/chat</code> takes <code>messages</code>, <code>evidence</code> (default <code>true</code>), <code>model</code> (<code>gemini</code>, <code>claude-sonnet</code> or <code>claude-haiku</code>) and <code>fallback</code> (default <code>true</code>: a busy Gemini is retried twice, then Claude Sonnet answers and the reply is labelled; set <code>false</code> in evaluations).</p>
      <p>Each offer carries <code>paypal_checkout</code>. With evidence on it means checkout can be opened now (false for a withdrawn seal); with evidence off it only says whether the shop takes PayPal, so the baseline never learns about a withdrawal. <code>GET /api/health</code> gives each shop's checkout mode: <code>paypal_sandbox</code> or <code>simulated</code>.</p>
      <p>The two lines at the foot of every passport have one fixed layout, 36 characters each:</p>
      <pre>{`RDS<<SHOP<NAME<<<<<<<<<<<<<<<<<<<<<<
STANDING<<C2<YYYYMMDD<NNNN<<<<<<<<<<
standing (9): SEALED, VERIFIED, REPORTED, NEW,
              WITHDRAWN or NORECORD
C2: published rule set, version 2 (C0: none)
YYYYMMDD: data date; NNNN: completed orders`}</pre>
      <p class="small">The evaluation runner and grader are in <code>evals/live/</code>; the graded run is in <code>data_platform/landing/agent/</code> and every result page reads from it.</p>
    </div>
  </div>

  {#if c}
    <h2>Data products</h2>
    <p class="lede sub">A data mesh of four domains. Each owns its own bronze, silver and gold tables; a shared platform runs them behind four gates. Pipeline run {c.run_id}.</p>
    <div class="products">
      {#each c.products as p}
        {@const k = c.contracts.find((x) => x.domain === p.domain)}
        <article class="card">
          <span class="label">{p.domain} domain</span><h3>{p.name}</h3><p>{p.purpose}</p>
          <p class="small"><strong>Owner:</strong> {p.owner}<br /><strong>Contract:</strong> v{k.version}, {k.rules.filter((r) => r.passed).length} of {k.rules.length} rules passing<br /><strong>Read by:</strong> {p.consumers.join(', ')}</p>
          <div class="ports">{#each p.output_ports as o}<button class:on={pick === o} onclick={() => (pick = o)}>{o}</button>{/each}</div>
        </article>
      {/each}
    </div>
    <div class="gates">{#each c.gates as g}<div><span class="num">{g.checked - g.failed}/{g.checked}</span><strong>Gate {g.gate}: {g.name}</strong></div>{/each}</div>

    <h2>The star schema</h2>
    <p class="lede sub">Gold is a star for analytics: {facts.length} fact tables at a declared grain, pointing at {gold.length - facts.length - serving.length} shared dimensions through surrogate keys. Every foreign key is checked on every build. The {serving.length} agent-ready tables are built on top of it.</p>
    <div class="star">
      <div class="lane"><h3>Facts</h3>{#each facts as t}<button class="node" class:sel={fact === t.name} onclick={() => { fact = t.name; pick = t.name; }}>{short(t.name)}<span>{t.rows} rows</span></button>{/each}
        <h3 class="mt">Agent-ready tables</h3>{#each serving as t}<button class="node" class:sel={fact === t.name} onclick={() => { fact = t.name; pick = t.name; }}>{short(t.name)}<span>{t.rows} rows</span></button>{/each}</div>
      <div class="centre">{#if factTable}<span class="label">{factTable.domain} domain</span><h3>{short(factTable.name)}</h3><p>{factTable.description}</p><p class="small"><strong>Grain:</strong> {factTable.grain}</p>
        <p class="small"><strong>Keys:</strong> {factTable.columns.filter((x) => x.name.endsWith('_key')).map((x) => x.name).join(', ') || 'natural key only'}</p>
        <pre>{`SELECT d.year_month, m.merchant_name, sum(f.net_usd) AS net
FROM gold.fact_orders f
JOIN gold.dim_merchant m USING (merchant_key)
JOIN gold.dim_date d ON d.date_key = f.order_date_key
GROUP BY ALL`}</pre>{/if}</div>
      <div class="lane"><h3>Its dimensions</h3>{#each factDims as t}<button class="node lit" onclick={() => (pick = t.name)}>{short(t.name)}<span>{t.rows} rows</span></button>{/each}{#if !factDims.length}<p class="small">This table carries no dimension keys.</p>{/if}</div>
    </div>

    <h2>Lineage</h2>
    <p class="lede sub">Read from the <code>-- reads:</code> and <code>-- writes:</code> lines of each SQL file, never drawn by hand. Pick a table to light up everything it depends on.</p>
    <div class="lineage">
      {#each layers as l}
        <div class="lane"><h3>{l}</h3>
          {#each c.lineage.nodes.filter((n) => n.layer === l) as n}
            <button class="node {n.domain}" class:lit={up.has(n.id)} class:sel={pick === n.id} onclick={() => (pick = n.id)} disabled={l === 'landing' || l === 'bronze'}>{short(n.id)}<span>{n.domain}</span></button>
          {/each}
        </div>
      {/each}
    </div>
    <p class="source">{up.size - 1} upstream sources and tables feed <code>{pick}</code>.</p>

    {#if table}
      <h2>Metadata: <code class="h">{table.name}</code></h2>
      <p class="lede sub">{table.description} Grain: {table.grain}. {table.rows} rows. Owner: {table.owner}. Built by <code>{table.file}</code>.</p>
      <table class="plain"><thead><tr><th>Column</th><th>Type</th><th>Meaning</th></tr></thead>
        <tbody>{#each table.columns as col}<tr><td><code>{col.name}</code>{table.key.includes(col.name) ? ' (key)' : ''}</td><td class="small">{col.type}</td><td>{col.meaning ?? ''}</td></tr>{/each}</tbody></table>
    {/if}

    <h2>Semantic layer</h2>
    <p class="lede sub">A number has one definition. Dashboards and agents ask for a measure by name; nobody retypes a formula. Asking for a measure that is not defined is refused.</p>
    <div class="two">
      <div>
        <div class="q">
          <label>View <select bind:value={q.view} onchange={() => { q.measure = c.metric_views.find((v) => v.name === q.view).measures[0].name; q.dim = c.metric_views.find((v) => v.name === q.view).dimensions[0].name; run(); }}>{#each c.metric_views as v}<option>{v.name}</option>{/each}</select></label>
          <label>Measure <select bind:value={q.measure} onchange={run}>{#each view.measures as m}<option>{m.name}</option>{/each}</select></label>
          <label>By <select bind:value={q.dim} onchange={run}>{#each view.dimensions as dd}<option>{dd.name}</option>{/each}</select></label>
        </div>
        <p class="small">{view.measures.find((m) => m.name === q.measure)?.description} Defined once as:</p>
        <pre>{view.measures.find((m) => m.name === q.measure)?.expr}</pre>
      </div>
      <pre class="res">{JSON.stringify(metric, null, 2)}</pre>
    </div>

    <h2>Data contracts</h2>
    <p class="lede sub">{rules.filter((r) => r.passed).length} of {rules.length} promises hold on this run. One broken promise stops the build before anything reaches an agent.</p>
    {#each c.contracts as k}
      <details><summary><strong>{k.name}</strong> v{k.version} <span class="small">{k.rules.length} rules, {k.description}</span></summary>
        <table class="plain"><tbody>{#each k.rules.filter((r) => !r.rule.startsWith('column ')) as r}<tr><td class="small">{r.table}</td><td>{r.rule}</td><td>{r.passed ? '✓' : '✕'}</td></tr>{/each}</tbody></table></details>
    {/each}
  {/if}
</section>

<style>
  .top { margin: 24px 0 0; } .sub { margin-bottom: 30px; }
  h2 { font-size: clamp(1.9rem, 3.6vw, 3rem); margin: 88px 0 16px; } .h { font-size: 0.7em; }
  .two { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; align-items: start; }
  .two table td { vertical-align: top; }
  .products { display: grid; grid-template-columns: repeat(2, 1fr); gap: 2px; }
  .products h3 { margin: 4px 0 10px; font-size: 1.5rem; } .products p { font-size: 0.97rem; }
  .ports { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
  .ports button { border: 0; background: #fff; padding: 6px 10px; border-radius: 3px; font: 0.8rem ui-monospace, Menlo, monospace; cursor: pointer; box-shadow: inset 0 0 0 1.2px var(--ink); }
  .ports button.on, .ports button:hover { background: var(--red); color: #fff; box-shadow: none; }
  .gates { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2px; margin-top: 2px; }
  .gates div { background: var(--ink); color: #fff; padding: 18px 22px; display: grid; } .gates .num { font-size: 1.8rem; font-weight: 300; }
  .lineage { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2px; }
  .lane { background: var(--tile); padding: 16px; display: grid; gap: 5px; align-content: start; }
  .lane h3 { font-size: 1rem; margin-bottom: 8px; text-transform: capitalize; }
  .node { text-align: left; border: 0; background: #fff; padding: 7px 10px; border-radius: 3px; font: 0.78rem ui-monospace, Menlo, monospace; cursor: pointer; display: flex; justify-content: space-between; gap: 8px;
    color: var(--muted); transition: 0.25s var(--ease); word-break: break-all; }
  .node span { font: 600 0.68rem var(--body); opacity: 0.7; white-space: nowrap; }
  .node.lit { background: var(--ink); color: #fff; } .node.sel { background: var(--red); color: #fff; } .node:disabled { cursor: default; }
  .star { display: grid; grid-template-columns: 0.9fr 1.3fr 0.9fr; gap: 2px; } .centre { background: var(--ink); color: #e6e6e6; padding: 28px; display: grid; gap: 10px; align-content: start; } .centre h3 { color: #fff; font-size: 1.6rem; } .centre .label, .centre .small { color: #bbb; } .centre pre { background: #1c1c1c; font-size: 0.78rem; } .centre p { margin: 0; } .mt { margin-top: 18px; }
  .q { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; } .q label { display: grid; gap: 4px; font-size: 0.82rem; font-weight: 600; color: var(--muted); }
  select { font: inherit; padding: 10px 12px; border: 0; background: var(--tile); border-radius: 4px; color: var(--ink); }
  .res { max-height: 300px; }
  details { border-top: 1px solid var(--line); padding: 14px 0; } summary { cursor: pointer; display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; }
  details table { margin-top: 10px; }
  @media (max-width: 960px) { .two, .products, .star { grid-template-columns: 1fr; } .lineage, .gates { grid-template-columns: 1fr 1fr; } }
</style>
