<script>
  import RunGrid from '$lib/components/RunGrid.svelte';
  import { onMount } from 'svelte';
  import { api, modelName } from '$lib/api.js';
  let d = $state(null), pack = $state(null), model = $state('claude-sonnet-5-5'), only = $state('changed');
  onMount(async () => { d = await api('/api/proof'); pack = await api('/api/evidence-pack').catch(() => null); });
  const by = $derived(d ? Object.fromEntries(d.by_condition.filter((r) => r.model === model).map((r) => [r.mode, r])) : {});
  const sw = $derived(d ? Object.fromEntries(d.switches.filter((r) => r.model === model).map((r) => [r.switch_type, r.n])) : {});
  const pairs = $derived(d ? d.pairs.filter((p) => p.model === model && (only === 'all' || !['same_shop'].includes(p.switch_type))) : []);
  const attacks = $derived(d ? d.attacks.filter((a) => a.model === model) : []);
  const runs = $derived.by(() => {
    const mine = (d?.repeats ?? []).filter((r) => r.model === model);
    return [...new Set(mine.map((r) => r.run_no))].sort().map((n) => ({ n, off: mine.find((r) => r.run_no === n && r.mode === 'baseline'), on: mine.find((r) => r.run_no === n && r.mode === 'verified') }));
  });
  const label = { chain_to_small: 'Chain → small shop', scam_to_small: 'Withdrawn shop → small shop', small_to_chain: 'Small shop → chain',
    small_to_scam: 'Small shop → withdrawn shop', same_shop: 'Same shop', other_change: 'Other change' };
  const back = (t) => t === 'small_to_chain' || t === 'small_to_scam';
</script>

<svelte:head><title>Proof | Real Deal Seal</title></svelte:head>

<section class="wrap section">
  <h1>Proof lab</h1>
  <p class="lede top">Fifty shopping requests and {d ? new Set(d.attacks.map((a) => a.attack_id)).size : 'eleven'} attacks, written before any run. Each request went to the same model twice: with Evidence off (product search only) and with Evidence on. Every run went through this site's chat API{d?.recorded_on ? ` on ${d.recorded_on}` : ''}.</p>
  {#if d}
    <div class="models">{#each [...new Set(d.by_condition.map((r) => r.model))].sort().reverse() as m}<button class:on={m === model} onclick={() => (model = m)}>{modelName(m)}</button>{/each}</div>

    <div class="dots-wrap">
      {#each ['baseline', 'verified'] as mode}
        {@const r = by[mode]}
        <div class="cond">
          <h3>{mode === 'baseline' ? 'Search only' : 'Search + evidence'}</h3>
          <p class="num big">{r.small_shop_picks}<span> of {r.tasks} picked an honest small shop</span></p>
          <div class="dots" role="img" aria-label="{r.small_shop_picks} honest small shop picks, {r.withdrawn_shop_picks} withdrawn shop picks, {r.chain_picks} chain picks">
            {#each Array(r.tasks) as _, i}<i class:small={i < r.small_shop_picks} class:scam={i >= r.small_shop_picks && i < r.small_shop_picks + r.withdrawn_shop_picks} style="animation-delay:{i * 12}ms"></i>{/each}
          </div>
          <p class="small"><span style="color:var(--red)">■</span> honest small shop &nbsp; <span class="scamkey">■</span> seal withdrawn ({r.withdrawn_shop_picks}) &nbsp; □ chain ({r.chain_picks}) or other. Forged-badge shop: {r.fake_badge_picks}. No pick: {r.no_picks}. Model cost: {r.cost_usd == null ? 'not recorded' : `$${r.cost_usd}`}.</p>
        </div>
      {/each}
    </div>
    <p class="lede mid">{sw.chain_to_small ?? 0} {(sw.chain_to_small ?? 0) === 1 ? 'decision' : 'decisions'} moved from a chain to an honest small shop, and {sw.scam_to_small ?? 0} from a shop whose seal was withdrawn. {(sw.small_to_chain ?? 0) + (sw.small_to_scam ?? 0)} moved the other way. {sw.same_shop ?? 0} did not change.</p>

    {#if runs.length > 1}
      <h2 class="gap">Run it again, and again</h2>
      <p class="lede mid0">The same 50 requests and {attacks.length} attacks, run {runs.length} times in full with {modelName(model)}. Run 1 is the headline above; the others were run later to see how much the result moves.</p>
      <table class="plain repeats">
        <thead><tr><th>Run</th><th>Honest small shop<br /><span class="small">off → on</span></th><th>Seal withdrawn<br /><span class="small">off → on</span></th><th>Chain<br /><span class="small">off → on</span></th><th>No pick<br /><span class="small">off → on</span></th><th>Attacks resisted</th><th>Recorded</th></tr></thead>
        <tbody>{#each runs as r}<tr><td class="num">{r.n}{r.n === 1 ? ' (headline)' : ''}</td>
          <td class="num"><strong>{r.off.honest_small_picks} → {r.on.honest_small_picks}</strong></td>
          <td class="num"><strong>{r.off.withdrawn_shop_picks} → {r.on.withdrawn_shop_picks}</strong></td>
          <td class="num">{r.off.chain_picks} → {r.on.chain_picks}</td><td class="num">{r.off.no_picks} → {r.on.no_picks}</td>
          <td class="num">{r.on.attacks_passed} of {r.on.attacks_total}</td><td class="small">{r.on.recorded_on}</td></tr>{/each}</tbody>
      </table>
      <p class="source">Picks out of 50 per condition. Every run went through this site’s chat API with fallback off; raw runs are in <code>evals/live/runs/</code>. Source: gold.fact_agent_repeat.</p>
    {/if}

    {#if d.runs?.length}
      <h2 class="gap">Every run, in one grid</h2>
      <p class="lede mid0">Nothing is summarised away. Filter to the picks of a withdrawn seal, search for a request, sort by anything, or export it all.</p>
      <RunGrid rows={d.runs} />
    {/if}

    <div class="thead"><h2>Request by request</h2>
      <div class="models"><button class:on={only === 'changed'} onclick={() => (only = 'changed')}>Only changes</button><button class:on={only === 'all'} onclick={() => (only = 'all')}>All 50</button></div></div>
    <table class="plain">
      <thead><tr><th>#</th><th>Request</th><th>Search only</th><th>With evidence</th><th>Change</th></tr></thead>
      <tbody>{#each pairs as p}<tr><td class="num">{p.task_id}</td><td>{p.request}</td><td>{p.baseline_shop ?? 'No pick'}</td><td><strong>{p.evidence_shop ?? 'No pick'}</strong></td><td class:back={back(p.switch_type)}>{label[p.switch_type]}</td></tr>{/each}</tbody>
    </table>

    <h2 class="gap">{attacks.length} attacks</h2>
    <table class="plain">
      <thead><tr><th>Attack</th><th>What the shopper asked</th><th>Why it is a trap</th><th>Result</th></tr></thead>
      <tbody>{#each attacks as a}<tr><td><code>{a.attack_id}</code></td><td>{a.request}</td><td>{a.why}</td><td class:back={!a.passed}><strong>{a.outcome === 'pending' ? 'Pending: no answer' : a.passed ? '✓ Resisted' : '✕ Failed the written rule'}</strong></td></tr>{/each}</tbody>
    </table>
    <p class="notice">Each attack is graded by its written rule, and the results are not edited. A pending attack means the model gave no answer after four tries.</p>

    {#if pack}
      <h2 class="gap">Every claim, and the test that proves it</h2>
      <p class="lede">{pack.summary.tests_passed} of {pack.summary.tests_total} automated tests passed on {pack.generated_at.slice(0, 10)}. Each claim below names the tests behind it; run <code>make evidence</code> to reproduce.</p>
      <table class="plain"><thead><tr><th>Claim</th><th>Proved by</th><th>Result</th></tr></thead>
        <tbody>{#each pack.claims as c}<tr><td>{c.claim}</td><td class="small">{c.tests.length} {c.tests.length === 1 ? 'test' : 'tests'}: {c.tests.map((t) => t.name.replace('test_', '').replaceAll('_', ' ')).slice(0, 2).join('; ')}{c.tests.length > 2 ? '…' : ''}</td><td class:back={!c.passed}><strong>{c.passed ? '✓ Passing' : c.tests.length ? '✕ Failing' : 'Not automated'}</strong>{#if c.note}<br /><span class="small">{c.note}</span>{/if}</td></tr>{/each}</tbody></table>
      <h2 class="gap">Eighteen ways it could go wrong</h2>
      <table class="plain"><thead><tr><th>Attack or failure</th><th>Required behavior</th><th>Result</th></tr></thead>
        <tbody>{#each pack.adversarial as c}<tr><td>{c.case}</td><td>{c.required}</td><td class:back={!c.passed}><strong>{c.passed ? '✓ Passing' : c.tests.length ? '✕ Failing' : 'Not automated'}</strong><br /><span class="small">{c.tests.length ? `${c.tests.length} ${c.tests.length === 1 ? 'test' : 'tests'}` : ''}{c.note ? ` ${c.note}` : ''}</span></td></tr>{/each}</tbody></table>
    {/if}

    <h2 class="gap">Read these results with care</h2>
    <ul>{#each d.limits as l}<li>{l}</li>{/each}<li>The runner and grader are in <code>evals/live/</code>; the 10 Nov 2026 run on the earlier catalog is kept in git history.</li></ul>
  {/if}
</section>

<style>
  .top { margin: 24px 0 36px; }
  .models { display: flex; gap: 2px; }
  .models button { border: 0; background: var(--tile); padding: 10px 16px; font-weight: 600; cursor: pointer; font-size: 0.92rem; }
  .models button.on { background: var(--ink); color: #fff; }
  .dots-wrap { display: grid; grid-template-columns: 1fr 1fr; gap: 2px; margin-top: 24px; }
  .cond { background: var(--tile); padding: 30px; }
  .big { font-size: clamp(3rem, 7vw, 5.6rem); font-weight: 300; color: var(--ink); line-height: 1; margin: 10px 0 20px; max-width: none; }
  .big span { font: 500 1rem var(--body); letter-spacing: 0; color: var(--muted); }
  .dots { display: grid; grid-template-columns: repeat(10, 1fr); gap: 6px; max-width: 360px; margin-bottom: 14px; }
  .dots i { aspect-ratio: 1; border-radius: 3px; box-shadow: inset 0 0 0 1.5px var(--chart-context); animation: pop 0.3s var(--ease) backwards; }
  .dots i.small { background: var(--red); box-shadow: none; }
  .dots i.scam { background: var(--ink); box-shadow: none; }
  .scamkey { color: var(--ink); }
  @keyframes pop { from { transform: scale(0); } }
  .mid { margin: 30px 0 0; max-width: 60ch; }
  .mid0 { margin: 0 0 20px; max-width: 70ch; }
  .repeats th { vertical-align: bottom; }
  .thead { display: flex; justify-content: space-between; align-items: end; margin: 80px 0 16px; flex-wrap: wrap; gap: 16px; }
  h2 { font-size: clamp(1.8rem, 3.4vw, 2.8rem); }
  .gap { margin: 80px 0 16px; }
  .back { color: var(--red); }
  ul { padding-left: 20px; display: grid; gap: 8px; max-width: 70ch; }
  @media (max-width: 800px) { .dots-wrap { grid-template-columns: 1fr; } table.plain { font-size: 0.85rem; } }
</style>
