<script>
  import { onMount } from 'svelte';
  import { api, modelName } from '$lib/api.js';
  import Arrow from '$lib/components/Arrow.svelte';
  import TileArt from '$lib/components/TileArt.svelte';
  import PassportCard from '$lib/components/PassportCard.svelte';
  import Slope from '$lib/components/Slope.svelte';
  import SealMark from '$lib/components/SealMark.svelte';
  import LightspeedStudy from '$lib/components/LightspeedStudy.svelte';
  import SideBySide from '$lib/components/SideBySide.svelte';

  let shops = $state([]), score = $state(null), proof = $state(null), error = $state('');
  onMount(async () => {
    try { [shops, score, proof] = await Promise.all([api('/api/merchants'), api('/api/scorecard'), api('/api/proof')]); }
    catch (e) { error = e.message; }
  });
  const first = $derived(proof?.pairs.find((p) => p.model === score?.north_star.model && p.task_id === 1));
  const ns = $derived(score?.north_star);
  const picked = $derived(shops.find((x) => x.merchant_name === first?.evidence_shop));
  const tiles = [
    ['passport', 'Merchant Passport', '/shops', 'A signed record of what a shop actually delivered.'],
    ['evidence', 'Evidence Explorer', '/studio', 'Every PayPal order behind every number.'],
    ['seal', 'Seal check', '/verify', 'Genuine, edited, expired or forged, step by step.'],
    ['assistant', 'Shopping assistant', '/assistant', 'An AI shopper that reads the evidence before it picks.'],
    ['checkout', 'PayPal checkout', '/shop', 'The agent opens it. Only the buyer approves it.'],
    ['coach', 'Growth coach', '/studio', 'What to fix next, from the shop’s own record.'],
    ['developers', 'Agent tools and data', '/developers', 'Eight MCP tools on four contracted data products.']
  ];
</script>

<svelte:head><title>Real Deal Seal: proof beats brand</title></svelte:head>

<div class="wrap"><a class="judges" href="/judges">Judging this project? Take the 3-minute tour <span aria-hidden="true">→</span></a></div>

<section class="hero wrap">
  <div class="copy">
    <h1>Small shops deliver.<br />Now AI can check.</h1>
    <p class="lede">AI shopping assistants tend to recommend brands they already know. Real Deal Seal helps small shops compete by turning their PayPal sales history into a signed record any assistant can check.</p>
    <div class="actions">
      <a class="btn" href="#difference">See the difference <Arrow /></a>
      <a class="btn ghost" href="/assistant">Ask the assistant <Arrow /></a>
      <a class="btn ghost" href="/verify">Check a seal <Arrow /></a>
    </div>
  </div>
  <div class="duel" aria-label="The same request answered twice">
    <p class="ask">“{first?.request ?? 'I want a purple table runner for my dining table.'}”</p>
    <div class="answer before">
      <span class="label">Search only</span>
      <strong>{first?.baseline_shop ?? 'Babel Home'}</strong>
      <span class="small">It sees only the listing: the price, shipping and returns, as the seller wrote them.</span>
    </div>
    <div class="answer after">
      <span class="label">Search + Real Deal Seal</span>
      <strong>{first?.evidence_shop ?? 'Lydia Linen Co.'}</strong>
      <span class="small">It read the passport first{picked?.has_paypal_record ? `: ${picked.orders_completed} PayPal sandbox orders, tracking on ${picked.tracking_pct}% of recent shipments, and a seal that checks out` : ''}.</span>
      <span class="stampmark"><SealMark size={64} /></span>
    </div>
    <p class="small note">A recorded run from the evaluation ({ns ? modelName(ns.model) : 'Sonnet 5.5'}, request 1 of 50). <a href="/proof">See all 50</a>.</p>
  </div>
</section>

{#if error}<div class="wrap"><p class="notice">The API is not reachable: {error} Start it with <code>make api</code>.</p></div>{/if}

<section class="wrap section-tight" id="difference">
  <h2>See the difference</h2>
  <p class="lede diff">One question, asked twice at the same moment. The only thing that changes is whether the assistant can read each shop’s record.</p>
  <SideBySide {shops} pairs={proof?.pairs ?? []} model={ns?.model} recordedOn={ns?.recorded_on} />
</section>

<section class="wrap section-tight facts">
  {#if ns}
  <div><span class="num big">{ns.baseline_numerator} <i>to</i> {ns.numerator}</span><p>of 50 AI shopping decisions went to an honest small shop once the assistant could read the evidence ({modelName(ns.model)}, a controlled test with fictional shops).</p></div>
  <div><span class="num big">{ns.baseline_withdrawn} <i>to</i> {ns.withdrawn}</span><p>of 50 decisions went to a shop whose seal was withdrawn for cause. Its listings looked clean and cheap; only the record showed otherwise.</p></div>
  <div><span class="num big">{ns.paypal_orders}</span><p>PayPal sandbox orders behind the published facts, and each one can be traced.</p></div>
  {/if}
</section>
{#if ns?.repeat_runs?.length > 1}
  <div class="wrap"><p class="small again">We ran all 50 requests {ns.repeat_runs.length} times. Picks of a shop with a withdrawn seal, without and with evidence: {ns.repeat_runs.map((r) => `${r.baseline_withdrawn} to ${r.withdrawn}`).join(', ')}. Honest small shops: {ns.repeat_runs.map((r) => `${r.baseline_small} to ${r.small}`).join(', ')}. <a href="/proof">See every run</a>.</p></div>
{/if}

<section class="stone section"><div class="wrap"><LightspeedStudy compact /></div></section>

<section class="wrap section">
  <h2>What's in the demo</h2>
  <div class="tiles">
    {#each tiles as [art, name, href, line]}
      <a class="tile" {href}>
        <div class="art"><TileArt name={art} /></div>
        <div class="foot"><span>{name}</span><span class="more">Learn more <Arrow size={12} /></span></div>
        <p class="line">{line}</p>
      </a>
    {/each}
  </div>
</section>

<section class="wrap section" style="padding-top:0">
  <div>
    <div class="head">
      <h2>Three shops,<br />three track records</h2>
      <p class="lede">Every shop is judged by the same five published rules. A long, clean record earns the seal, and a record with problems shows them. Shops that are just getting started are labeled New.</p>
    </div>
    <div class="passports">
      {#each shops.filter((s) => s.origin === 'demo') as shop}
        <PassportCard {shop} href="/shops/{shop.merchant_id}" />
      {/each}
    </div>
    <p class="after-cards">After the demo, any small shop could earn the seal by connecting its own PayPal account.</p>
    <p class="small after-cards">These are demo shops in the PayPal sandbox. Order dates, shipping speed and dispute outcomes are simulated, and every passport labels them that way.</p>
  </div>
</section>

<section class="wrap section proof">
  <div>
    <h2>Evidence moved {ns?.moved ?? '…'} of 50 decisions</h2>
    <p class="lede">We ran the same 50 shopping requests twice with the same model: once with product search only, once with the evidence tools as well. The model had no instructions to favor small shops.</p>
    {#if ns}<p>With evidence, honest small shops won {ns.numerator} of 50 instead of {ns.baseline_numerator}, and shops whose seals were withdrawn went from {ns.baseline_withdrawn} picks to {ns.withdrawn}. The chains still won {ns.chain}, usually on price. The evidence informed the choice without forcing it.</p>{/if}
    <a class="btn black" href="/proof">Open the proof lab <Arrow /></a>
  </div>
  <figure>
    {#if ns}
      <Slope series={ns.by_model.map((m) => ({ name: m.label, from: m.baseline, to: m.with_evidence, highlight: m.model === ns.model,
        detail: `${m.label}: ${m.baseline_n} of 50 without evidence, ${m.with_evidence_n} of 50 with it` }))} />
    {/if}
    <figcaption class="source">Share of 50 requests where the assistant picked an honest small shop, one run per request per model, recorded on {ns?.recorded_on ?? ''} on this site. A controlled test with fictional shops; these are AI recommendations, not purchases. Source: Real Deal Seal evaluation.</figcaption>
  </figure>
</section>

<section class="cta-band">
  <div class="wrap">
    <h2>Try to fool it.</h2>
    <p class="lede">Paste a seal, change one number, and watch the check fail. Or ask the assistant for the forged shop by name.</p>
    <div class="actions"><a class="btn" href="/verify">Check a seal <Arrow /></a><a class="btn ghost light" href="/assistant">Ask the assistant <Arrow /></a></div>
  </div>
</section>

<style>
  .hero { overflow-x: clip; display: grid; grid-template-columns: 1.15fr 0.85fr; gap: clamp(28px, 5vw, 80px); align-items: end; padding-block: clamp(48px, 8vw, 110px) clamp(32px, 5vw, 64px); }
  .copy h1 { margin-bottom: 28px; }
  .actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 30px; }
  .duel { display: grid; gap: 2px; overflow: clip; }
  .ask { font: 500 1.15rem var(--display); margin: 0 0 14px; max-width: none; }
  .answer { position: relative; background: var(--tile); padding: 20px 22px; display: grid; gap: 4px; border-radius: 6px 6px 0 0; }
  .answer strong { font: 500 1.7rem var(--display); letter-spacing: -0.03em; color: var(--ink); }
  .answer.before strong { color: var(--muted); text-decoration: line-through; text-decoration-thickness: 2px; text-decoration-color: var(--red); }
  .answer.after { background: var(--ink); color: #e9e9e9; border-radius: 0 0 6px 6px; padding-right: 96px; animation: rise 0.7s var(--ease) 0.35s backwards; }
  .answer.after strong { color: #fff; }
  .answer.after .label, .answer.after .small { color: #b5b5b5; }
  .stampmark { position: absolute; right: 18px; top: 50%; translate: 0 -50%; animation: stamp 0.55s var(--ease) 1s backwards; }
  @keyframes rise { from { opacity: 0; transform: translateY(18px); } }
  @keyframes stamp { from { transform: scale(2.6) rotate(-25deg); opacity: 0; } }
  .note { margin-top: 12px; }
  .judges { display: inline-block; margin-top: 22px; padding: 8px 14px; background: var(--tile); border-radius: 999px; font-size: 0.92rem; font-weight: 600; text-decoration: none; color: var(--ink); }
  .judges:hover { background: var(--ink); color: #fff; }
  .diff { margin: 14px 0 26px; }
  .again { margin: 18px 0 0; max-width: 90ch; }
  #difference { scroll-margin-top: 90px; }
  .facts { display: grid; grid-template-columns: repeat(3, 1fr); gap: clamp(20px, 4vw, 56px); border-top: 1.5px solid var(--ink); padding-top: 28px; }
  .facts .big { font-size: clamp(2.4rem, 5vw, 4rem); font-weight: 300; color: var(--ink); line-height: 1; display: block; margin-bottom: 10px; }
  .facts i { font-style: normal; font-size: 0.45em; color: var(--muted); letter-spacing: 0; }
  .facts p { font-size: 0.98rem; max-width: 34ch; }
  .tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2px; margin-top: clamp(28px, 4vw, 56px); }
  .tile { position: relative; background: var(--tile); text-decoration: none; display: grid; grid-template-rows: 1fr auto; min-height: 360px; border-radius: 3px;
    transition: background 0.35s var(--ease), color 0.35s var(--ease); overflow: hidden; }
  .tile .art { padding: 36px 28px 0; display: grid; place-items: center; transition: transform 0.45s var(--ease); }
  .tile .foot { display: flex; justify-content: space-between; align-items: center; padding: 18px 24px 6px; font-size: 1.02rem; }
  .tile .more { display: inline-flex; gap: 10px; align-items: center; opacity: 0; transform: translateX(-8px); transition: 0.3s var(--ease); font-size: 0.95rem; }
  .tile .line { padding: 0 24px 22px; margin: 0; font-size: 0.88rem; color: var(--muted); transition: color 0.3s; }
  .tile:hover, .tile:focus-visible { background: linear-gradient(180deg, #e2564a, var(--red) 55%, var(--red-deep)); color: #fff; --art: #fff; }
  .tile:hover .art, .tile:focus-visible .art { transform: translateY(-6px) scale(1.03); }
  .tile:hover .more, .tile:focus-visible .more { opacity: 1; transform: none; }
  .tile:hover .line, .tile:focus-visible .line { color: #ffe3e0; }
  .head { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; align-items: end; margin-bottom: 40px; }
  .passports { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; }
  .after-cards { margin-top: 18px; }
  .proof { display: grid; grid-template-columns: 1fr 1fr; gap: clamp(28px, 6vw, 96px); align-items: center; }
  .proof h2 { margin-bottom: 22px; }
  figure { margin: 0; }
  .cta-band { background: linear-gradient(100deg, #7c2426, var(--oxblood) 45%, #54201c); color: #f4e9e8; padding-block: clamp(56px, 8vw, 110px); }
  .cta-band h2 { color: #fff; margin-bottom: 16px; }
  .cta-band .lede { color: #f1dcda; }
  .btn.ghost.light { color: #fff; box-shadow: inset 0 0 0 1.5px #fff; }
  .btn.ghost.light:hover { background: #fff; color: var(--ink); }
  @media (max-width: 1000px) { .hero, .proof, .head { grid-template-columns: 1fr; } .tiles { grid-template-columns: repeat(2, 1fr); } .passports { grid-template-columns: 1fr; } .tile { min-height: 300px; } }
  @media (max-width: 620px) { .facts { grid-template-columns: 1fr; } .tiles { grid-template-columns: 1fr; } .stampmark { animation: none; } }
</style>
