<script>
  import { onMount } from 'svelte';
  import { api, usd } from '$lib/api.js';
  import Arrow from '$lib/components/Arrow.svelte';

  let all = $state([]), q = $state(''), found = $state(null), open = $state(null), detail = $state(null), market = $state(null), error = $state(''), busy = $state(false);
  onMount(async () => (all = await api('/api/products')));
  const list = $derived(found ?? all);
  const cls = (h) => (h.includes('Real Deal') ? 'sealed' : h.includes('Verified') ? 'verified' : h.includes('Self-reported') ? 'reported' : h.includes('history') ? 'new' : 'no_record');
  async function search() { found = q.trim() ? await api(`/api/products?q=${encodeURIComponent(q)}`) : null; }
  async function show(o) {
    open = o; detail = null; market = null; error = '';
    [detail, market] = await Promise.all([api('/api/tools/get_merchant_passport', { shop_id: o.shop_id }), api('/api/tools/compare_market_prices', { query: o.product })]);
  }
  async function buy() { busy = true; error = ''; try { const s = await api('/api/checkout', { sku: open.sku, quantity: 1 }); window.location.href = s.approve_url; } catch (e) { error = e.message; busy = false; } }
</script>

<svelte:head><title>Shop | Real Deal Seal</title></svelte:head>

<section class="wrap section">
  <div class="head"><h1>Shop</h1>
    <form onsubmit={(e) => { e.preventDefault(); search(); }}><input class="input" bind:value={q} placeholder="Search: purple table runner, linen napkins, garden tote" aria-label="Search products" /><button class="btn">Search <Arrow size={12} /></button></form></div>
  <p class="lede">Every offer shows the shop's standing beside the price. Results are sorted by how well they match your search, then by price. No shop can pay to rank higher.</p>
  {#if found && !found.length}<p class="notice">Nothing matched "{q}". Try naming the item and one detail, for example "purple napkins".</p>{/if}
  <div class="grid">
    {#each list as o (o.sku)}
      <button class="offer" onclick={() => show(o)}>
        <img class="thumb" src="/api/products/{o.sku}/image.svg" alt={o.product} loading="lazy" width="320" height="190" />
        <strong>{o.product}</strong><span class="small">{o.shop}</span>
        <span class="chip {cls(o.shop_standing)}">{o.shop_standing}</span>
        <span class="foot"><span class="num price">{usd(o.price_usd)}</span><span class="more">See the evidence <Arrow size={11} /></span></span>
      </button>
    {/each}
  </div>
</section>

{#if open}
  <div class="scrim" onclick={() => (open = null)} role="presentation"></div>
  <div class="sheet" role="dialog" aria-modal="true" aria-label={open.product}>
    <button class="close" onclick={() => (open = null)} aria-label="Close">✕</button>
    <span class="label">{open.shop} · {open.ships_from ?? ''}</span>
    <img class="hero-img" src="/api/products/{open.sku}/image.svg" alt={open.product} width="320" height="190" />
    <h2>{open.product}</h2>
    <p class="num big">{usd(open.price_usd, 2)}</p>
    <div class="seller"><span class="label">In the seller's own words (not checked)</span><p>{open.seller_text.text}</p>
      {#if open.seller_text.contains_instructions_for_ai}<p class="err small">This listing contains text aimed at AI assistants.</p>{/if}</div>
    {#if detail}
      <h3>{detail.standing}</h3><p>{detail.verdict}</p>
      {#if detail.facts?.length}<table class="plain"><tbody>{#each detail.facts.filter((f) => f.counted) as f}<tr><td>{f.fact}</td><td class="num">{f.value}</td><td class="small">{f.counted} · {f.evidence.replaceAll('_', ' ')}</td></tr>{/each}</tbody></table>
        <a class="link" href="/shops/{open.shop_id}">Open the full passport <Arrow size={12} /></a>{/if}
    {:else}<p class="small">Reading the business's record.</p>{/if}
    {#if market?.available}<p class="small ctx">Price context: similar items on the web typically cost about {usd(market.typical_price_usd)} ({usd(market.range_usd[0])} to {usd(market.range_usd[1])}). {market.note}</p>{/if}
    {#if error}<p class="notice err">{error}</p>{/if}
    {#if open.paypal_checkout}<button class="btn" onclick={buy} disabled={busy || !open.in_stock}>{open.in_stock ? 'Buy with PayPal' : 'Out of stock'} <Arrow /></button>
    {:else}<p class="notice">This shop has no PayPal connection here, so no checkout can be opened.</p>{/if}
    <p class="small">You approve the payment yourself in PayPal, and our server sets the price.</p>
  </div>
{/if}

<style>
  .head { display: flex; justify-content: space-between; align-items: end; gap: 32px; flex-wrap: wrap; margin-bottom: 20px; }
  .head form { display: flex; gap: 2px; flex: 1; max-width: 620px; } .head .btn { border-radius: 0 4px 4px 0; }
  .lede { margin-bottom: 36px; max-width: 70ch; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 2px; }
  .offer { background: var(--tile); border: 0; text-align: left; padding: 22px; display: flex; flex-direction: column; gap: 7px; align-items: flex-start; min-width: 0; cursor: pointer; color: inherit; transition: background 0.3s var(--ease), color 0.3s; }
  .offer .chip { max-width: 100%; white-space: normal; line-height: 1.25; text-align: left; }
  .thumb { width: 100%; height: auto; aspect-ratio: 320/190; background: #fff; display: block; margin-bottom: 8px; transition: 0.3s; }
  .hero-img { width: 100%; height: auto; aspect-ratio: 320/190; background: var(--tile); border-radius: 6px; }
  .offer strong { font: 600 1.05rem/1.25 var(--display); }
  .foot { display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: auto; padding-top: 8px; }
  .price { font-size: 1.6rem; } .more { font-size: 0.85rem; display: flex; gap: 8px; align-items: center; opacity: 0; transform: translateX(-6px); transition: 0.3s var(--ease); }
  .offer:hover, .offer:focus-visible { background: linear-gradient(180deg, #e2564a, var(--red) 55%, var(--red-deep)); color: #fff; }
  .offer:hover :is(.small, .price), .offer:focus-visible :is(.small, .price) { color: #fff; } .offer:hover .more, .offer:focus-visible .more { opacity: 1; transform: none; }
  .offer:hover .chip { background: #fff; color: var(--ink); box-shadow: none; }
  .scrim { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.45); z-index: 60; animation: fade 0.25s; }
  .sheet { position: fixed; top: 0; right: 0; bottom: 0; width: min(520px, 100vw); background: #fff; z-index: 61; padding: 40px 34px; overflow-y: auto; display: grid; gap: 14px; align-content: start; animation: slide 0.4s var(--ease); }
  @keyframes slide { from { transform: translateX(100%); } } @keyframes fade { from { opacity: 0; } }
  .close { position: absolute; top: 16px; right: 16px; width: 40px; height: 40px; border: 0; background: var(--tile); border-radius: 50%; cursor: pointer; }
  .sheet h2 { font-size: 2rem; } .big { font-size: 2.6rem; font-weight: 300; color: var(--ink); margin: 0; } .sheet p { margin: 0; }
  .seller { background: var(--tile); padding: 14px 16px; border-left: 3px solid var(--line); display: grid; gap: 6px; } .ctx { background: var(--tile); padding: 12px 14px; }
</style>
