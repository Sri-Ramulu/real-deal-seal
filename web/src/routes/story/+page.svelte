<script>
  import { onMount } from 'svelte';
  import { api, usd, modelName } from '$lib/api.js';
  import SealMark from '$lib/components/SealMark.svelte';
  import PassportCard from '$lib/components/PassportCard.svelte';
  import Arrow from '$lib/components/Arrow.svelte';

  let shops = $state([]), score = $state(null), pub = $state(null), step = $state(0);
  onMount(async () => {
    [shops, score, pub] = await Promise.all([api('/api/merchants'), api('/api/scorecard'), api('/api/merchants/lydia')]);
    const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && (step = +e.target.dataset.step)), { rootMargin: '-45% 0px -45% 0px' });
    document.querySelectorAll('[data-step]').forEach((el) => io.observe(el));
    return () => io.disconnect();
  });
  const lydia = $derived(shops.find((s) => s.merchant_id === 'lydia'));
  const ns = $derived(score?.north_star);
  const shape = $derived(pub?.record_shape);
  const tracking = $derived(pub?.facts.find((f) => f.metric === 'tracking_rate'));
  // One square per order, drawn from public counts only: refunded first, then shipped without tracking, then the rest.
  const squares = $derived(shape ? Array.from({ length: shape.orders }, (_, i) => (i < shape.refunded ? 'refund' : i < shape.refunded + shape.fulfilled_without_tracking ? 'notrack' : 'ok')) : []);
  const chapters = $derived([
    ['A good shop is invisible to AI', 'A shopper asks an AI assistant for a purple table runner. The assistant knows the national chain, its prices and its returns policy. It knows almost nothing about Lydia, who hand-dyes linen and has shipped a hundred orders without a problem. So it recommends the chain.', 'A study for Lightspeed Commerce by Vaer AI (September 2026, about 460,000 AI answers) found that, without live web search, assistants chose a national chain over a smaller retailer 90 to 94 times in 100 head-to-head comparisons. With live search, chains were still 46 to 58% of answers.'],
    ['The proof is already in her payment records', 'Every order Lydia took through PayPal left a record: paid, shipped, tracked, and refunded or not. That’s one hundred orders, two refunds, and a tracking number on almost every shipment. A shopper shouldn’t have to take her word for it, and with these records they don’t need to.', 'Each square is one of Lydia’s 100 PayPal sandbox orders. In this demo, the order dates are simulated, and they’re labeled that way.'],
    ['We turn the record into facts anyone can count', 'With Lydia’s permission, Real Deal Seal reads her records from PayPal and counts what happened. We don’t give her a trust score. We report, for example, how many of her recent shipments had a tracking number, out of how many. Each fact also says where it came from and how strong the evidence is.', 'Tracking numbers are reported by the shop, so they’re labeled that way. Refunds come straight from PayPal’s records.'],
    ['Then we sign it so no one can quietly change it', 'The facts go into a Merchant Passport, signed with a key we publish. Anyone can check it. If someone changes a single number, or copies the badge onto another shop’s page, the check fails. And if we learn a sealed shop is cheating, we can withdraw its seal, and its old badge stops checking out.', 'Real Deal Seal signs the passport. PayPal supplied the sandbox records but doesn’t sign or endorse the shop.'],
    ['Ask again, and this time the assistant can check', ns ? `Same question, same assistant, same catalog. This time the assistant can open each shop’s passport before it answers. Across 50 requests, honest small shops won ${ns.numerator} times instead of ${ns.baseline_numerator}, and shops whose seals were withdrawn for cause went from ${ns.baseline_withdrawn} picks to ${ns.withdrawn}. Their listings looked clean and cheap; only the record showed otherwise. The chains still won ${ns.chain}, mostly on price, so the evidence informed the choice without forcing it.` : 'Same question, same assistant, same catalog. This time the assistant can open each shop’s passport before it answers.', `A controlled test with fictional shops: one run per request with ${ns ? modelName(ns.model) : 'Claude'}${ns?.recorded_on ? `, recorded on ${ns.recorded_on}` : ''}. These are AI recommendations, not real purchases.`],
    ['The shopper pays, not the AI', 'The assistant can open a PayPal checkout, but it can’t approve one. The shopper approves the payment in PayPal, and our server then asks PayPal directly whether the exact amount was captured. Only then does the order count as paid.', 'Checkout runs in the PayPal sandbox with test money.'],
    ['New shops get a fair label, and problems stay visible', 'Priscilla has only a few weeks of orders. Her record is clean but too short to judge, so her passport says she’s new. Martha has 60 orders and misses several rules. Her passport shows which ones, and her studio shows the exact orders to fix. Neither shop is called unsafe, and neither gets a seal she hasn’t earned.', 'Every shop is judged by the same published rules for its type of business.'],
    ['Why it matters', 'The same signed record helps a small shop get chosen by AI shoppers and shows it what to fix next. For PayPal, it gives merchants a reason to stay, and AI agents a reason to check out with PayPal.', 'Shown here with demo shops in the PayPal sandbox.']
  ]);
</script>

<svelte:head><title>The story | Real Deal Seal</title></svelte:head>

<section class="wrap intro">
  <h1>How a shop nobody has heard of gets chosen</h1>
  <p class="lede">The whole project in eight short scenes, with the real numbers. No technical background needed.</p>
</section>

<section class="wrap scrolly">
  <div class="text">
    {#each chapters as [title, body, note], i}
      <article data-step={i} class:on={step === i}>
        <span class="n num">{i + 1}</span>
        <h2>{title}</h2>
        <p>{body}</p>
        <p class="small">{note}</p>
      </article>
    {/each}
  </div>
  <div class="stage" aria-hidden="true">
    {#key step}
      <div class="fig">
        {#if step === 0}
          <div class="grid100">{#each Array(100) as _, i}<i class:chain={i < 92} style="animation-delay:{i * 6}ms"></i>{/each}</div>
          <p class="cap"><strong>About 92 of 100</strong> head-to-head picks went to the national chain.</p>
        {:else if step === 1}
          <div class="grid100">{#each squares as k, i}<i class="order {k}" style="animation-delay:{i * 6}ms"></i>{/each}</div>
          <p class="cap"><strong>{shape?.orders} orders, {usd(lydia?.net_sales_usd ?? 0)} net.</strong> ■ fine &nbsp; <span class="r">■</span> refunded &nbsp; □ no tracking</p>
        {:else if step === 2}
          <div class="count"><span class="num huge">{tracking?.numerator}<small> of {tracking?.denominator}</small></span><p>recent shipped orders had a tracking number</p><span class="pill">Reported by the shop</span></div>
        {:else if step === 3}
          <div class="seals"><div class="s ok"><SealMark size={110} /><strong>✓ Genuine</strong></div><div class="s bad"><SealMark size={110} tone="black" /><strong>✕ Edited</strong><span class="small">one number changed</span></div></div>
        {:else if step === 4}
          <div class="vs"><div><span class="num huge">{ns?.baseline_numerator}</span><p>of 50 without evidence</p></div><Arrow size={34} /><div class="hot"><span class="num huge">{ns?.numerator}</span><p>of 50 with evidence</p></div></div>
        {:else if step === 5}
          <ol class="flow"><li>Assistant opens checkout</li><li class="hot">Shopper approves in PayPal</li><li>Server asks PayPal: captured, exact amount?</li><li>Only then: paid</li></ol>
        {:else if step === 6}
          <div class="trio">{#each shops.filter((s) => s.origin === 'demo') as s}<div class="mini"><strong>{s.merchant_name}</strong><span class="chip {s.standing}">{s.headline}</span><span class="small">{s.orders_completed} orders, {s.rules_met} of {s.rules_total} rules</span></div>{/each}</div>
        {:else}
          <div class="doors">{#each ['Picked by AI shoppers', 'Coached on what to fix', 'More checkouts through PayPal'] as d, i}<div style="animation-delay:{i * 90}ms">{d}</div>{/each}</div>
        {/if}
      </div>
    {/key}
  </div>
</section>

<section class="stone section">
  <div class="wrap end">
    <div><h2>Proof beats brand.</h2><p class="lede">See it working, or check the numbers yourself.</p>
      <div class="actions"><a class="btn" href="/assistant">Ask the assistant <Arrow /></a><a class="btn ghost" href="/scorecard">Open the scorecard <Arrow /></a></div></div>
    {#if lydia}<PassportCard shop={lydia} href="/shops/lydia" />{/if}
  </div>
</section>

<style>
  .intro { padding-block: clamp(48px, 8vw, 110px) 24px; }
  .intro h1 { max-width: 14ch; margin-bottom: 24px; }
  .scrolly { display: grid; grid-template-columns: 1fr 1fr; gap: clamp(28px, 6vw, 96px); }
  article { min-height: 86vh; display: flex; flex-direction: column; justify-content: center; opacity: 0.28; transition: opacity 0.4s; }
  article.on { opacity: 1; }
  .n { font-size: 1.1rem; font-weight: 600; color: #fff; background: var(--red); width: 38px; height: 38px; border-radius: 50%; display: grid; place-items: center; margin-bottom: 18px; }
  article h2 { font-size: clamp(1.9rem, 3.6vw, 3.1rem); margin-bottom: 20px; }
  article p { font-size: 1.12rem; max-width: 46ch; }
  .stage { position: sticky; top: 14vh; height: 72vh; display: grid; place-items: center; background: var(--tile); border-radius: 8px; padding: 32px; }
  .fig { width: 100%; display: grid; justify-items: center; gap: 22px; animation: fig 0.5s var(--ease); text-align: center; }
  @keyframes fig { from { opacity: 0; transform: translateY(14px); } }
  .grid100 { display: grid; grid-template-columns: repeat(10, 1fr); gap: 5px; width: min(340px, 80%); }
  .grid100 i { aspect-ratio: 1; border-radius: 2px; box-shadow: inset 0 0 0 1.5px var(--chart-context); animation: pop 0.3s var(--ease) backwards; }
  .grid100 i.chain { background: var(--ink); box-shadow: none; }
  .grid100 i.order { background: var(--ink); box-shadow: none; }
  .grid100 i.order.notrack { background: transparent; box-shadow: inset 0 0 0 1.5px var(--ink); }
  .grid100 i.order.refund { background: var(--red); box-shadow: none; }
  @keyframes pop { from { transform: scale(0); } }
  .cap { margin: 0; font-size: 0.98rem; } .r { color: var(--red); }
  .huge { font-size: clamp(4.5rem, 10vw, 8.5rem); font-weight: 300; line-height: 0.9; color: var(--ink); }
  .huge small { font-size: 0.32em; color: var(--muted); letter-spacing: 0; }
  .count p { font-size: 1.15rem; margin: 14px auto; }
  .pill { font-size: 0.82rem; font-weight: 600; padding: 4px 12px; border-radius: 3px; box-shadow: inset 0 0 0 1.4px var(--ink); background: #fff; }
  .seals { display: flex; gap: 40px; } .s { display: grid; justify-items: center; gap: 10px; font-size: 1.2rem; }
  .s.bad { color: var(--red); } .s.bad :global(svg) { filter: grayscale(1); opacity: 0.55; }
  .vs { display: flex; align-items: center; gap: 28px; } .vs p { margin: 8px 0 0; } .vs .hot .huge { color: var(--red); }
  .flow { list-style: none; padding: 0; margin: 0; display: grid; gap: 4px; width: min(380px, 100%); text-align: left; counter-reset: s; }
  .flow li { background: #fff; padding: 16px 18px; border-radius: 4px; font-weight: 600; counter-increment: s; }
  .flow li::before { content: counter(s) '  '; color: var(--muted); }
  .flow li.hot { background: var(--red); color: #fff; } .flow li.hot::before { color: #ffd5d2; }
  .trio { display: grid; gap: 4px; width: min(400px, 100%); } .mini { background: #fff; padding: 16px; border-radius: 4px; display: grid; gap: 6px; justify-items: start; text-align: left; }
  .doors { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; width: min(420px, 100%); }
  .doors div { background: var(--ink); color: #fff; padding: 28px 16px; border-radius: 4px; font-weight: 600; animation: pop 0.4s var(--ease) backwards; }
  .doors div:last-child { background: var(--red); }
  .end { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 56px; align-items: center; }
  .actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 26px; }
  @media (max-width: 900px) {
    .scrolly, .end { grid-template-columns: 1fr; }
    .stage { position: sticky; top: 84px; height: 40vh; order: -1; z-index: 2; padding: 16px; box-shadow: 0 10px 30px -18px #000; }
    .huge { font-size: 4rem; } article { min-height: 70vh; } .grid100 { width: 180px; gap: 3px; } .seals :global(svg) { width: 70px; height: 70px; }
  }
</style>
