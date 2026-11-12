<script>
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import { api, usd } from '$lib/api.js';
  import SealMark from '$lib/components/SealMark.svelte';
  let d = $state(null), error = $state('');
  onMount(async () => { try { d = await api(`/api/statements/${page.url.searchParams.get('token')}`); } catch (e) { error = e.message; } });
  const s = $derived(d?.statement.credentialSubject);
</script>

<svelte:head><title>Shared statement | Real Deal Seal</title></svelte:head>

<section class="wrap section narrow">
  {#if error}<h1>This statement is not available</h1><p class="lede">{error}</p><p>The business controls who can see its statement and can take a link back at any time.</p>
  {:else if d}
    <div class="doc">
      <header><SealMark size={56} /><div><span class="label">Statement of commercial records · shared with {d.recipient} for {d.purpose.toLowerCase()}</span><h1>{s.name}</h1></div></header>
      <p class="check" class:ok={d.check.genuine}>{d.check.genuine ? '✓' : '✕'} {d.check.summary} Checked by code against the issuer's published key.</p>
      <div class="totals"><div><span class="num">{usd(s.totals.netUsd)}</span><span class="small">net sales</span></div><div><span class="num">{s.totals.orders}</span><span class="small">completed orders</span></div>
        <div><span class="num">{s.totals.paypalConfirmedOrders} of {s.totals.orders}</span><span class="small">payments confirmed by PayPal records</span></div><div><span class="num">{s.standing}</span><span class="small">standing, data as of {s.dataAsOf}</span></div></div>
      <table class="plain"><thead><tr><th>Month</th><th>Orders</th><th>Captured</th><th>Refunded</th><th>Net</th></tr></thead>
        <tbody>{#each s.months as m}<tr><td>{m.month}</td><td class="num">{m.orders}</td><td class="num">{usd(m.capturedUsd)}</td><td class="num">{usd(m.refundedUsd)}</td><td class="num">{usd(m.netUsd)}</td></tr>{/each}</tbody></table>
      <h2>Rules</h2><ul>{#each s.rules as r}<li>{r.met ? '✓' : '✕'} {r.rule}</li>{/each}</ul>
      {#if s.correctiveActions.length}<h2>Improvements on record</h2><ul>{#each s.correctiveActions as a}<li>{a.action.replace('_', ' ')}: {a.before} → {a.after}</li>{/each}</ul>{/if}
      <h2>Read this before relying on it</h2><ul class="small">{#each s.limitations as l}<li>{l}</li>{/each}</ul>
    </div>
  {:else}<p>Opening the statement.</p>{/if}
</section>

<style>
  .narrow { max-width: 900px; } .doc { background: #fff; box-shadow: inset 0 0 0 1.5px var(--ink); padding: clamp(24px, 5vw, 56px); display: grid; gap: 22px; border-radius: 6px; }
  header { display: flex; gap: 18px; align-items: center; border-bottom: 1.5px solid var(--ink); padding-bottom: 22px; } h1 { font-size: clamp(2rem, 5vw, 3.4rem); } h2 { font-size: 1.4rem; font-weight: 500; }
  .check { background: var(--red); color: #fff; padding: 12px 16px; margin: 0; font-weight: 600; max-width: none; } .check.ok { background: var(--ink); }
  .totals { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2px; } .totals div { background: var(--tile); padding: 16px; display: grid; gap: 4px; } .totals .num { font-size: 1.5rem; color: var(--ink); line-height: 1.15; }
  ul { margin: 0; padding-left: 20px; display: grid; gap: 6px; }
  @media (max-width: 700px) { .totals { grid-template-columns: 1fr 1fr; } }
</style>
