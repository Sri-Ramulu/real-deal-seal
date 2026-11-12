<script>
  import { onMount, tick } from 'svelte';
  import { api, usd } from '$lib/api.js';
  import Arrow from '$lib/components/Arrow.svelte';
  import SealMark from '$lib/components/SealMark.svelte';

  let health = $state(null), turns = $state([]), input = $state(''), busy = $state(false), evidence = $state(true), model = $state(''), error = $state(''), log;
  // Each starter was run 3 times with evidence off and 3 times with evidence on (Claude Sonnet, 12 Nov 2026):
  // the pick changed every time, so a tester sees the switch matter.
  const starters = ['I want a purple table runner for my dining table.', 'A linen sheet set in lavender for our guest room, good value.',
    'I need a wooden cutting board as a gift, under $40.', 'A white enamel tea kettle.'];
  onMount(async () => {
    health = await api('/api/health').catch(() => null);
    model = health?.default_model ?? '';
  });

  async function send(text) {
    const content = (text ?? input).trim();
    if (!content || busy) return;
    input = ''; error = ''; busy = true;
    turns.push({ role: 'user', content });
    await tick(); log?.scrollTo({ top: log.scrollHeight, behavior: 'smooth' });
    try {
      const r = await api('/api/chat', { messages: turns.map((t) => ({ role: t.role, content: t.content })), evidence, model: model || null });
      turns.push({ role: 'assistant', content: r.answer, ...r });
    } catch (e) { error = e.message; }
    busy = false;
    await tick(); log?.scrollTo({ top: log.scrollHeight, behavior: 'smooth' });
  }
  async function buy(o) {
    error = '';
    try { const s = await api('/api/checkout', { sku: o.sku, quantity: 1 }); window.location.href = s.approve_url; }
    catch (e) { error = e.message; }
  }
  const standingClass = (h = '') => (h.includes('withdrawn') ? 'withdrawn' : h.includes('sealed') && h.includes('Real') ? 'sealed' : h.includes('Verified') ? 'verified' : h.includes('Self-reported') ? 'reported' : h.includes('history') ? 'new' : 'no_record');
</script>

<svelte:head><title>Shopping assistant | Real Deal Seal</title></svelte:head>

<section class="wrap shell">
  <aside>
    <h1>Ask the assistant</h1>
    <p>It searches the catalog, reads each shop's signed record, and tells you what it counted. You approve any payment yourself in PayPal.</p>
    {#if health?.models?.some((m) => m.available)}
      <label class="field model">AI model
        <select class="input" bind:value={model}>
          {#each health.models as m}<option value={m.key} disabled={!m.available}>{m.label}{m.default ? ' (default)' : ''}{m.available ? '' : ' (not set up)'}</option>{/each}
        </select>
      </label>
    {/if}
    <label class="toggle">
      <input type="checkbox" bind:checked={evidence} />
      <span><strong>{evidence ? 'Evidence on' : 'Evidence off'}</strong><br /><span class="small">Turn it off to see what an assistant picks from product listings alone, with no seals or shop records.</span></span>
    </label>
    {#if health}
      <p class="notice small">
        {#if health.assistant === 'offline'}<strong>Offline mode.</strong> No AI model is set up on this server, so answers are a plain catalog search.{:else if evidence}The assistant can search, read shop passports and check seals.{:else}Evidence is off: the assistant can only search listings and open a checkout.{/if}
        {#if Object.values(health.checkout).includes('simulated')}<br /><strong>Simulated checkout.</strong> No PayPal sandbox keys are set on this server, so no PayPal call is made.{:else}<br />Checkout runs in the PayPal sandbox with test money.{/if}
      </p>
    {/if}
  </aside>

  <div class="chat">
    <div class="log" bind:this={log} aria-live="polite">
      {#if !turns.length}
        <div class="empty">
          <SealMark size={72} />
          <p>Try one of these, or ask for anything in Home &amp; Garden.</p>
          <p class="small">Ask once with Evidence off, then again with Evidence on, and compare the pick.</p>
          <div class="starters">{#each starters as s}<button onclick={() => send(s)}>{s}</button>{/each}</div>
        </div>
      {/if}
      {#each turns as t}
        {#if t.role === 'user'}<div class="msg user">{t.content}</div>
        {:else}
          <div class="msg bot">
            <div class="who"><SealMark size={26} /> Assistant <span class="small">{t.mode === 'offline' ? 'offline search' : t.model_label}{t.evidence === false ? ' · evidence off' : ''}</span></div>
            <div class="text">{t.content}</div>
            {#if t.offers?.length}
              <div class="offers">
                {#each t.offers.slice(0, 6) as o}
                  <article class:pick={o.sku === t.pick}>
                    {#if o.sku === t.pick}<span class="flag">The pick</span>{/if}
                    <img class="pic" src="/api/products/{o.sku}/image.svg" alt={o.product} loading="lazy" width="320" height="190" />
                    <h3>{o.product}</h3>
                    <p class="shop">{o.shop}</p>
                    {#if t.evidence !== false}
                      <span class="chip {standingClass(o.shop_standing)}">{o.shop_standing}</span>
                      {#if o.seller_text?.contains_instructions_for_ai}<p class="warn small">This listing contains text aimed at AI assistants. It was ignored.</p>{/if}
                    {/if}
                    <div class="row"><span class="num price">{usd(o.price_usd)}</span>
                      {#if o.paypal_checkout}<button class="btn" onclick={() => buy(o)}>Buy with PayPal <Arrow size={12} /></button>
                      {:else}<span class="small">No PayPal checkout here</span>{/if}</div>
                    {#if t.evidence !== false}<a class="small" href="/shops/{o.shop_id}">Open the shop's passport</a>{/if}
                  </article>
                {/each}
              </div>
            {/if}
            {#if t.checkout}<p class="notice">Checkout opened for {t.checkout.product} ({usd(t.checkout.amount_usd, 2)}). <a href={t.checkout.approve_url}>Approve it in PayPal</a>. Nothing is paid until you do.</p>{/if}
            {#if t.trace?.length}
              <details><summary>What the assistant did ({t.trace.length} tool {t.trace.length === 1 ? 'call' : 'calls'})</summary>
                <ol>{#each t.trace as s}<li><code>{s.tool}</code> {JSON.stringify(s.input)} <span class="small">→ {s.summary}</span></li>{/each}</ol>
              </details>
            {/if}
          </div>
        {/if}
      {/each}
      {#if busy}<div class="msg bot"><div class="who"><SealMark size={26} /> Assistant</div><div class="dots"><i></i><i></i><i></i></div></div>{/if}
    </div>
    {#if error}<p class="notice err">{error}</p>{/if}
    <form onsubmit={(e) => { e.preventDefault(); send(); }}>
      <input bind:value={input} placeholder="What are you shopping for?" aria-label="Your message" />
      <button class="btn" disabled={busy || !input.trim()}>Send <Arrow size={12} /></button>
    </form>
  </div>
</section>

<style>
  .shell { display: grid; grid-template-columns: 340px 1fr; gap: clamp(24px, 4vw, 56px); padding-block: clamp(36px, 5vw, 72px); align-items: start; }
  aside { position: sticky; top: 100px; }
  h1 { font-size: clamp(2.4rem, 4.6vw, 3.8rem); margin-bottom: 18px; }
  .model { margin-top: 20px; } .model select { width: 100%; }
  .toggle { display: flex; gap: 12px; align-items: flex-start; background: var(--tile); padding: 14px 16px; border-radius: 6px; margin: 20px 0; cursor: pointer; }
  .toggle input { width: 20px; height: 20px; accent-color: var(--red); margin-top: 3px; }
  .chat { background: var(--tile); border-radius: 8px; display: grid; grid-template-rows: 1fr auto auto; min-height: 72vh; }
  .log { padding: 26px; overflow-y: auto; max-height: 72vh; display: grid; gap: 18px; align-content: start; }
  .empty { display: grid; justify-items: center; gap: 14px; padding: 48px 0; text-align: center; }
  .starters { display: grid; gap: 8px; width: min(520px, 100%); }
  .starters button { text-align: left; background: #fff; border: 0; padding: 14px 16px; border-radius: 6px; cursor: pointer; transition: 0.2s; }
  .starters button:hover { background: var(--ink); color: #fff; }
  .msg { max-width: 860px; }
  .msg.user { justify-self: end; background: var(--ink); color: #fff; padding: 12px 18px; border-radius: 16px 16px 2px 16px; }
  .msg.bot { background: #fff; padding: 20px 22px; border-radius: 2px 16px 16px 16px; animation: in 0.35s var(--ease); }
  @keyframes in { from { opacity: 0; transform: translateY(10px); } }
  .who { display: flex; align-items: center; gap: 8px; font-weight: 700; margin-bottom: 10px; }
  .text { white-space: pre-wrap; max-width: 70ch; }
  .offers { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 10px; margin-top: 18px; }
  article { position: relative; background: var(--tile); border-radius: 6px; padding: 18px; display: grid; gap: 8px; align-content: start; justify-items: start; }
  article.pick { background: #fff; box-shadow: inset 0 0 0 2px var(--red); }
  .flag { position: absolute; top: -10px; right: 12px; background: var(--red); color: #fff; font-size: 0.75rem; font-weight: 700; padding: 3px 10px; border-radius: 3px; }
  .pic { width: 100%; height: auto; aspect-ratio: 320/190; background: #fff; border-radius: 4px; }
  article h3 { font: 600 1.02rem/1.25 var(--display); }
  .shop { margin: 0; font-size: 0.9rem; color: var(--muted); }
  .row { display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: 6px; gap: 8px; }
  .price { font-size: 1.5rem; font-weight: 500; color: var(--ink); }
  article .btn { padding: 9px 12px; font-size: 0.86rem; gap: 8px; }
  .warn { color: var(--red); font-weight: 600; margin: 0; }
  details { margin-top: 14px; font-size: 0.9rem; }
  summary { cursor: pointer; font-weight: 600; }
  ol { margin: 10px 0 0; padding-left: 22px; display: grid; gap: 6px; word-break: break-word; }
  .dots { display: flex; gap: 6px; padding: 6px 0; }
  .dots i { width: 8px; height: 8px; border-radius: 50%; background: var(--red); animation: bob 1s infinite; }
  .dots i:nth-child(2) { animation-delay: 0.15s; } .dots i:nth-child(3) { animation-delay: 0.3s; }
  @keyframes bob { 50% { transform: translateY(-6px); opacity: 0.4; } }
  form { display: flex; gap: 2px; padding: 12px; }
  form input { flex: 1; border: 0; padding: 16px 18px; font: inherit; border-radius: 4px 0 0 4px; background: #fff; min-width: 0; }
  form .btn { border-radius: 0 4px 4px 0; }
  .err { margin: 0 12px; border-color: var(--red); }
  @media (max-width: 960px) { .shell { grid-template-columns: 1fr; } aside { position: static; } }
</style>
