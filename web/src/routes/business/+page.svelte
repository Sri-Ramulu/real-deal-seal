<script>
  import LightspeedStudy from '$lib/components/LightspeedStudy.svelte';
  import Arrow from '$lib/components/Arrow.svelte';
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  let ns = $state(null), sc = $state(null);
  onMount(async () => { try { sc = await api('/api/scorecard'); ns = sc.north_star; } catch { ns = null; } });
  const kpi = (k) => sc?.perspectives.flatMap((p) => p.kpis).find((x) => x.key === k);
  const flywheel = ['A business takes payments through PayPal', 'Its record becomes a signed passport', 'AI shoppers can check it and choose it', 'More checkouts go through PayPal', 'The record gets longer and stronger'];
  const tiers = [
    ['Passport', 'Free', 'Every eligible business', ['Signed Merchant Passport', 'Public seal check', 'Listed to AI agents over MCP'], 'Free on purpose. Being visible to AI shoppers must not depend on paying.'],
    ['Merchant Studio', 'Subscription', 'Businesses that want to improve', ['Coach with before-and-after tracking', 'Evidence explorer and exports', 'Business Readiness statements and sharing'], 'Paid for tools, never for standing.'],
    ['Evidence API', 'Usage-based', 'Marketplaces and AI-commerce builders', ['Eight agent tools over MCP and REST', 'Credential verification', 'Service agreement and support'], 'For approved integrators.']
  ];
  const beneficiaries = [
    ['PayPal', 'Payment history becomes a reason to stay. Agents that can check a merchant are more likely to send the checkout through PayPal, where the record lives.'],
    ['Small businesses', 'A business is chosen for what it delivered, not for how well known it is. The same record shows what to fix and backs a statement it can share.'],
    ['Shoppers', 'A recommendation that says what was counted, out of how many, and where the number came from. And a payment only they can approve.'],
    ['Agent builders', 'Small, checkable answers instead of marketing copy: a standing, facts with denominators, and a signature code can verify.']
  ];
  const excluded = ['Lending decisions, credit scores and financing guarantees', 'A resale marketplace or agent-to-agent price negotiation', 'Holding or delaying funds', 'Any claim that PayPal issues or endorses the seal'];
</script>

<svelte:head><title>Why PayPal wins | Real Deal Seal</title></svelte:head>

<section class="wrap section">
  <h1>Why PayPal wins</h1>
  <p class="lede sub">AI assistants are starting to choose where people shop. PayPal already holds the one thing an assistant can’t get from a listing: what a business actually delivered. Real Deal Seal makes that record checkable.</p>
  {#if ns}
  <div class="wins">
    <article>
      <span class="label">Measured</span>
      <p class="num big">{ns.baseline_withdrawn} <i>to</i> {ns.withdrawn}</p>
      <h3>Shoppers are steered away from bad sellers</h3>
      <p>Of 50 AI picks, {ns.baseline_withdrawn} went to a shop whose seal had been withdrawn when the assistant saw listings only, and {ns.withdrawn} when it could read the record.</p>
      <a class="small" href="/proof">Every run, in the proof lab</a>
    </article>
    <article>
      <span class="label">Measured</span>
      <p class="num big">{ns.baseline_numerator} <i>to</i> {ns.numerator}</p>
      <h3>Honest PayPal merchants get chosen</h3>
      <p>Honest small shops won {ns.numerator} of 50 picks with evidence, up from {ns.baseline_numerator}. Every one of those shops checks out through PayPal here.</p>
      <a class="small" href="/scorecard">The scorecard and its sources</a>
    </article>
    <article>
      <span class="label">Measured</span>
      <p class="num big">{kpi('net_usd')?.display ?? ''}</p>
      <h3>The evidence sits on real PayPal records</h3>
      <p>{ns.paypal_orders} PayPal sandbox orders, read back from PayPal, are behind the three PayPal shops’ facts. The buyer approves each payment in PayPal, and the server confirms the capture with PayPal.</p>
      <a class="small" href="/shops/lydia">See one passport</a>
    </article>
    <article class="proj">
      <span class="label">Proposition, not measured</span>
      <p class="num big">?</p>
      <h3>More checkouts through PayPal</h3>
      <p>If agents prefer sellers they can check, and the record lives with PayPal, more agent checkouts should run through PayPal. This project has not measured that. It would take live merchants and real purchases.</p>
    </article>
  </div>
  <p class="small">Measured figures: {ns.model?.includes('sonnet') ? 'Claude Sonnet' : ns.model}, the same 50 requests with Evidence off and on, one run each, recorded {ns.recorded_on} on this site, with fictional shops. They are AI recommendations, not purchases.</p>
  {/if}
</section>

<section class="wrap section"><LightspeedStudy /></section>

<section class="stone section">
  <div class="wrap">
    <h2>Who gains, in order</h2>
    <div class="four">{#each beneficiaries as [who, why], i}<article><span class="n num">{i + 1}</span><h3>{who}</h3><p>{why}</p></article>{/each}</div>
  </div>
</section>

<section class="wrap section">
  <h2>The loop that makes it grow</h2>
  <p class="lede sub">Each turn adds evidence, and evidence is what gets a business chosen next time.</p>
  <ol class="loop">{#each flywheel as f, i}<li style="animation-delay:{i * 90}ms"><span class="num">{i + 1}</span>{f}</li>{/each}</ol>
  <p class="small">What is measured today is the third step only, in a controlled test{ns ? `: with evidence, honest small shops won ${ns.numerator} of 50 AI decisions instead of ${ns.baseline_numerator}, and shops whose seals were withdrawn won ${ns.withdrawn} instead of ${ns.baseline_withdrawn}` : ''}. The later steps are the proposition, not a result.</p>
</section>

<section class="dark section">
  <div class="wrap">
    <h2>Paying never changes a standing</h2>
    <p class="lede sub light">A trust signal that can be bought is worthless. Paid plans add tools. They cannot add a rule met, hide a rule missed, or move a business up a list.</p>
    <div class="tiers">{#each tiers as [name, price, who, items, note]}
      <article><span class="label">{who}</span><h3>{name}</h3><p class="price num">{price}</p><ul>{#each items as i}<li>{i}</li>{/each}</ul><p class="small">{note}</p></article>{/each}</div>
    <p class="small light">Prices are a proposed model, not live plans. PayPal's own transaction economics stay PayPal's; this project assumes no share of them.</p>
  </div>
</section>

<section class="wrap section two">
  <div><h2>What this is not</h2><ul class="no">{#each excluded as e}<li>{e}</li>{/each}</ul></div>
  <div><h2>Three promises</h2>
    <p><strong>Every claim shows its count.</strong> What was measured, out of how many, over which window.</p>
    <p><strong>Every fact shows its source.</strong> PayPal record, reported by the business, simulated, or missing. Nothing is upgraded.</p>
    <p><strong>Every seal can be checked by anyone.</strong> With a published key and plain code, not by asking a model.</p>
    <a class="btn" href="/story">Read the story <Arrow /></a></div>
</section>

<style>
  h2 { margin-bottom: 18px; } .sub { margin-bottom: 36px; } .light { color: #d8d8d8; }
  h1 { margin-bottom: 24px; }
  .wins { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2px; margin-bottom: 18px; }
  .wins article { min-width: 0; background: var(--tile); padding: 26px; display: grid; gap: 10px; align-content: start; }
  .wins .big { font-size: clamp(2.2rem, 4vw, 3.4rem); font-weight: 300; line-height: 1; margin: 6px 0; color: var(--ink); }
  .wins i { font-style: normal; font-size: 0.45em; color: var(--muted); }
  .wins h3 { font-size: 1.2rem; } .wins p { margin: 0; font-size: 0.96rem; }
  .wins .proj { background: #fff; box-shadow: inset 0 0 0 1.5px var(--line); } .wins .proj .big { color: var(--muted); }
  @media (max-width: 960px) { .wins { grid-template-columns: 1fr 1fr; } }
  @media (max-width: 560px) { .wins { grid-template-columns: 1fr; } }
  .four { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2px; margin-top: 28px; }
  .four article { background: #fff; padding: 26px; display: grid; gap: 10px; align-content: start; } .four p { margin: 0; font-size: 0.97rem; }
  .n { width: 34px; height: 34px; border-radius: 50%; background: var(--red); color: #fff; display: grid; place-items: center; font-weight: 600; }
  .loop { list-style: none; padding: 0; margin: 0 0 20px; display: grid; grid-template-columns: repeat(5, 1fr); gap: 2px; }
  .loop li { background: var(--tile); padding: 22px 18px 26px; font-weight: 600; display: grid; gap: 14px; align-content: start; animation: up 0.5s var(--ease) backwards; position: relative; }
  .loop li .num { font-size: 2.2rem; font-weight: 300; color: var(--red); line-height: 1; } .loop li:last-child { background: var(--red); color: #fff; } .loop li:last-child .num { color: #fff; }
  @keyframes up { from { opacity: 0; transform: translateY(14px); } }
  .tiers { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px; margin-bottom: 20px; }
  .tiers article { background: #1c1c1c; padding: 28px; display: grid; gap: 10px; align-content: start; } .tiers .label { color: #aaa; } .tiers h3 { color: #fff; font-size: 1.6rem; }
  .price { font-size: 2.2rem; font-weight: 300; color: #fff; margin: 0; } .tiers ul { margin: 0; padding-left: 18px; display: grid; gap: 6px; } .tiers .small { color: #bbb; }
  .two { display: grid; grid-template-columns: 1fr 1fr; gap: clamp(28px, 6vw, 96px); } .no { list-style: none; padding: 0; display: grid; gap: 2px; }
  .no li { background: var(--tile); padding: 14px 16px 14px 44px; position: relative; } .no li::before { content: '✕'; position: absolute; left: 16px; color: var(--red); font-weight: 700; }
  @media (max-width: 1000px) { .four { grid-template-columns: 1fr 1fr; } .loop, .tiers, .two { grid-template-columns: 1fr; } }
</style>
