<script>
  import { onMount } from 'svelte';
  import { api, modelName, runDate } from '$lib/api.js';
  import Slope from '$lib/components/Slope.svelte';
  import RuleBars from '$lib/components/RuleBars.svelte';

  let s = $state(null), shops = $state([]), error = $state('');
  onMount(async () => { try { [s, shops] = await Promise.all([api('/api/scorecard'), api('/api/merchants')]); } catch (e) { error = e.message; } });
  const ns = $derived(s?.north_star);
  const connected = $derived(shops.filter((x) => x.has_record && x.business_type === 'physical'));
  const bars = (key, thr, dir) => connected.map((x) => ({ name: x.merchant_name, value: x[key], met: dir === 'min' ? x[key] >= thr : x[key] <= thr,
    counted: `last ${x.recent_orders} orders` }));
</script>

<svelte:head><title>Scorecard | Real Deal Seal</title></svelte:head>

<section class="wrap section">
  {#if error}<p class="notice">{error}</p>{/if}
  {#if ns}
    <div class="star">
      <div>
        <span class="label">North Star</span>
        <h1>With evidence, honest small shops won {ns.numerator} of {ns.denominator} AI shopping decisions. Without it, {ns.baseline_numerator}.</h1>
        <p class="lede">{ns.why}</p>
        <p class="small">{ns.name}. {modelName(ns.model)}, the same 50 requests in both conditions. {ns.caveat}</p>
      </div>
      <figure>
        <Slope series={ns.by_model.map((m) => ({ name: m.label, from: m.baseline, to: m.with_evidence, highlight: m.model === ns.model,
          detail: `${m.label}: ${m.baseline_n} of 50 without evidence, ${m.with_evidence_n} of 50 with it` }))} />
        <figcaption class="source">Share of requests won by an honest small shop (seal not withdrawn). Hover a line for counts.</figcaption>
      </figure>
    </div>

    <h2>Balanced scorecard</h2>
    <p class="lede sub">Four views of the same business, so one good number cannot hide a bad one. Red marks a number that is off its target.</p>
    <div class="persp">
      {#each s.perspectives as p}
        <section class="p">
          <header><h3>{p.name}</h3><p class="small">{p.question}</p></header>
          {#each p.kpis as k}
            <div class="k" class:off={!k.on_target}>
              <span class="num v">{k.display}</span>
              <div><strong>{k.label}</strong><p class="small">{k.note}</p><p class="tgt small">{k.target === 'context' ? 'For context' : `${k.on_target ? 'On target' : 'Off target'}: ${k.target}`}. <code>{k.source}</code></p></div>
            </div>
          {/each}
        </section>
      {/each}
    </div>
    <p class="source">{s.targets_note} Data as of {runDate(s.pipeline_run)}. Every figure comes from the semantic layer or a named data table.</p>

    <h2>Martha misses four rules, and the scorecard says which</h2>
    <p class="lede sub">Each rule is shown against its published threshold, measured on the shop's last 50 orders. Only physical-goods shops are shown here, because these rules apply only to them.</p>
    <div class="rules">
      <div class="card"><h3>Shipped orders with tracking</h3><RuleBars rows={bars('tracking_pct', 90, 'min')} threshold={90} /></div>
      <div class="card"><h3>Shipped within 2 days</h3><RuleBars rows={bars('fast_ship_pct', 80, 'min')} threshold={80} /></div>
      <div class="card"><h3>Orders refunded</h3><RuleBars rows={bars('refund_pct', 8, 'max')} threshold={8} direction="max" max={20} /></div>
    </div>
    <p class="source">Black bars meet the rule, red bars do not; the vertical line is the threshold. For Lydia, Martha and Priscilla, tracking is reported by the shop, shipping speed is simulated for the demo, and refunds come from PayPal sandbox records. The other shops' records are simulated demo records reported by the shop. All shops are fictional. Source: shop passports.</p>
  {:else if !error}<p>Loading the scorecard.</p>{/if}
</section>

<style>
  .star { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: clamp(28px, 5vw, 80px); align-items: center; margin-bottom: 30px; }
  h1 { font-size: clamp(2.1rem, 4.6vw, 4rem); line-height: 1.02; margin: 10px 0 24px; }
  h2 { margin: 88px 0 14px; }
  .sub { margin-bottom: 36px; }
  figure { margin: 0; }
  .persp { display: grid; grid-template-columns: repeat(2, 1fr); gap: 2px; }
  .p { background: var(--tile); padding: 30px; }
  .p header { border-bottom: 1.5px solid var(--ink); padding-bottom: 14px; margin-bottom: 6px; }
  .p header p { margin: 4px 0 0; }
  .k { display: grid; grid-template-columns: 150px 1fr; gap: 18px; padding: 18px 0; border-bottom: 1px solid var(--line); align-items: start; }
  .k:last-child { border: 0; padding-bottom: 0; }
  .v { font-size: 2.1rem; font-weight: 300; color: var(--ink); line-height: 1.1; }
  .k.off .v { color: var(--red); }
  .k p { margin: 3px 0 0; }
  .tgt { color: var(--ink); }
  .k.off .tgt { color: var(--red); font-weight: 600; }
  .rules { display: grid; gap: 2px; }
  .rules h3 { margin-bottom: 18px; }
  @media (max-width: 1000px) { .star, .persp { grid-template-columns: 1fr; } .k { grid-template-columns: 110px 1fr; } }
</style>
