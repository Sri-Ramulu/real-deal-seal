<script>
  // The same question, asked twice at the same moment: once with Evidence off, once with Evidence on.
  // Before anyone presses the button it shows the recorded run for that question, so the section is never empty.
  import { api, usd, rich } from '$lib/api.js';
  import Arrow from './Arrow.svelte';
  import Standing from './Standing.svelte';
  let { shops = [], pairs = [], model = 'claude-sonnet-5-5', recordedOn = '' } = $props();

  const questions = ['I want a purple table runner for my dining table.', 'A lavender linen sheet set for a queen bed.',
    'A white enamel tea kettle.', 'A lavender scented candle.'];
  let q = $state(questions[0]), live = $state(null), busy = $state(false), error = $state('');
  const shopByName = (n) => shops.find((s) => s.merchant_name === n);
  const shopById = (id) => shops.find((s) => s.merchant_id === id);
  const recorded = $derived(pairs.find((p) => p.model === model && p.request === q));

  function side(res) {
    const o = res.offers?.find((x) => x.sku === res.pick);
    return { shop: o ? shopById(o.shop_id) : null, product: o?.product, price: o?.price_usd, sku: o?.sku,
      why: (res.answer || '').split('\n').find((l) => l.trim()) ?? '', tools: res.trace?.length ?? 0, label: res.model_label };
  }
  async function run() {
    busy = true; error = ''; live = null;
    const ask = (evidence) => api('/api/chat', { messages: [{ role: 'user', content: q }], evidence, model: 'claude-sonnet' });
    try { const [off, on] = await Promise.all([ask(false), ask(true)]); live = { off: side(off), on: side(on) }; }
    catch (e) { error = e.message; }
    busy = false;
  }
  function choose(x) { q = x; live = null; error = ''; }
  const off = $derived(live?.off ?? (recorded ? { shop: shopByName(recorded.baseline_shop) } : null));
  const on = $derived(live?.on ?? (recorded ? { shop: shopByName(recorded.evidence_shop) } : null));
  const bad = (s) => s?.standing === 'withdrawn';
</script>

<div class="sbs">
  <div class="qs" role="group" aria-label="Pick a question">
    {#each questions as x}<button class:on={x === q} onclick={() => choose(x)} disabled={busy}>{x}</button>{/each}
  </div>
  <div class="cols">
    {#each [['off', off, 'Evidence off', 'Today’s AI shopper: it sees only what each seller wrote.'], ['on', on, 'Evidence on', 'It can open each shop’s signed record before it picks.']] as [key, s, title, sub]}
      <article class={key} class:bad={bad(s?.shop)} aria-live="polite">
        <span class="label">{title}</span>
        <p class="small sub">{sub}</p>
        {#if busy}<div class="dots"><i></i><i></i><i></i></div><p class="small">Asking the assistant…</p>
        {:else if s?.shop}
          {#if s.sku}<img src="/api/products/{s.sku}/image.svg" alt={s.product} width="320" height="190" loading="lazy" />{/if}
          <p class="picked">It picked</p>
          <strong class="shop">{s.shop.merchant_name}</strong>
          {#if s.product}<p class="prod">{s.product}, {usd(s.price)}</p>{/if}
          {#if key === 'on'}<Standing standing={s.shop.standing} headline={s.shop.headline} />
            {#if s.why}<p class="why">{@html rich(s.why)}</p>{:else}<p class="why">{s.shop.verdict}</p>{/if}
          {:else}
            {#if s.why}<p class="why">{@html rich(s.why)}</p>{/if}
            <div class="record">
              <span class="label">What it could not see</span>
              <Standing standing={s.shop.standing} headline={s.shop.headline} />
              <p class="small">{s.shop.verdict}</p>
            </div>
          {/if}
          {#if s.tools}<p class="small meta">{s.label} · {s.tools} tool {s.tools === 1 ? 'call' : 'calls'}</p>{/if}
          <a class="small" href="/shops/{s.shop.merchant_id}">Open this shop’s passport</a>
        {:else if s}<p class="small">It made no pick this time. Run it again or open the assistant.</p>
        {:else}<p class="small">Press the button to ask.</p>{/if}
      </article>
    {/each}
  </div>
  <div class="bar">
    <button class="btn" onclick={run} disabled={busy}>{busy ? 'Asking twice…' : live ? 'Run it again' : 'Run it live'} <Arrow /></button>
    <p class="small">{#if error}{error}{:else if live}A live run, just now, with Claude Sonnet. Answers vary a little from run to run.{:else if recorded}Shown: the recorded run{recordedOn ? ` from ${recordedOn}` : ''}. Press the button to ask both ways yourself; it takes about 20 seconds.{:else}Same model, same catalog, same question.{/if} All shops are fictional.</p>
  </div>
</div>

<style>
  .sbs { display: grid; gap: 14px; }
  .qs { display: flex; flex-wrap: wrap; gap: 6px; }
  .qs button { border: 0; background: var(--tile); padding: 10px 14px; border-radius: 4px; font: inherit; font-size: 0.95rem; cursor: pointer; text-align: left; color: var(--ink); }
  .qs button.on { background: var(--ink); color: #fff; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; align-items: stretch; }
  article { min-width: 0; background: var(--tile); border-radius: 8px; padding: clamp(18px, 2.4vw, 30px); display: grid; gap: 8px; align-content: start; justify-items: start; }
  article.on { background: #fff; box-shadow: inset 0 0 0 2px var(--ink); }
  article.off.bad { box-shadow: inset 0 0 0 2px var(--oxblood); }
  .sub { margin: 0 0 8px; color: var(--muted); }
  img { width: 100%; max-width: 300px; height: auto; aspect-ratio: 320/190; background: #fff; border-radius: 4px; }
  .picked { margin: 6px 0 0; font-size: 0.85rem; color: var(--muted); }
  .shop { font: 500 clamp(1.5rem, 2.6vw, 2.2rem)/1.1 var(--display); letter-spacing: -0.03em; overflow-wrap: anywhere; }
  .off.bad .shop { text-decoration: line-through; text-decoration-color: var(--oxblood); text-decoration-thickness: 2px; }
  .prod { margin: 0; }
  .why { margin: 6px 0 0; font-size: 0.95rem; max-width: 52ch; }
  .record { margin-top: 10px; padding: 14px 16px; background: #fff; border-left: 3px solid var(--oxblood); border-radius: 0 4px 4px 0; display: grid; gap: 8px; justify-items: start; width: 100%; }
  .record p { margin: 0; }
  .meta { color: var(--muted); margin: 4px 0 0; }
  .bar { display: flex; gap: 18px; align-items: center; flex-wrap: wrap; }
  .bar p { margin: 0; max-width: 60ch; }
  .dots { display: flex; gap: 6px; padding: 10px 0; }
  .dots i { width: 8px; height: 8px; border-radius: 50%; background: var(--red); animation: bob 1s infinite; }
  .dots i:nth-child(2) { animation-delay: 0.15s; } .dots i:nth-child(3) { animation-delay: 0.3s; }
  @keyframes bob { 50% { transform: translateY(-6px); opacity: 0.4; } }
  @media (max-width: 760px) { .cols { grid-template-columns: 1fr; } }
</style>
