<script>
  import { page } from '$app/state';
  import { api, usd, evidenceLabel } from '$lib/api.js';
  import PassportCard from '$lib/components/PassportCard.svelte';
  import Arrow from '$lib/components/Arrow.svelte';

  let data = $state(null), error = $state(''), showJson = $state(false);
  $effect(() => { data = null; error = ''; api(`/api/merchants/${page.params.id}`).then((d) => (data = d)).catch((e) => (error = e.message)); });
  const shown = (f) => (f.value == null ? 'Not measured' : f.unit === '%' ? `${f.value}%` : f.unit === 'USD' ? usd(f.value) : `${f.value} ${f.unit}`);
</script>

<svelte:head><title>{data?.passport.merchant_name ?? 'Shop'} | Merchant Passport</title></svelte:head>

<section class="wrap section">
  {#if error}<h1>No record</h1><p class="lede">{error}</p>
  {:else if data}
    {@const p = data.passport}
    <div class="top">
      <PassportCard shop={p} big />
      <div>
        <h1>{p.merchant_name}</h1>
        <p class="lede">{p.verdict}</p>
        {#if p.standing === 'withdrawn'}
          <p class="notice withdrawn"><strong>Seal withdrawn{p.seal_withdrawn_at ? ` on ${String(p.seal_withdrawn_at).slice(0, 10)}` : ''}.</strong>
            {p.seal_withdrawn_by === 'issuer' ? 'Real Deal Seal took this seal away, and the reason above is shown to every shopper and AI assistant.' : 'The business took its record down, so the facts are no longer public.'}
            Checkout is turned off for this shop, and any copy of its old seal now fails the check.</p>
          {#if p.seal_withdrawn_by === 'issuer'}<div class="actions"><a class="btn" href="/verify?shop={p.merchant_id}">See the seal check <Arrow /></a></div>{/if}
        {:else if p.has_record}
          <p>{p.business_type_label}. Based on {p.recent_orders < p.orders_completed ? `the last ${p.recent_orders} of ${p.orders_completed}` : p.orders_completed} {p.has_paypal_record ? 'PayPal sandbox orders, read back' : 'orders from the business\'s own records, imported'} on {p.data_as_of}. Rules version <code>{p.criteria_version}</code>. Evidence strength: <strong>{p.evidence_strength}</strong> (how much record there is, not a probability the shop is safe).</p>
          <div class="actions">
            <a class="btn" href="/verify?shop={p.merchant_id}">Check this seal <Arrow /></a>
            <a class="btn ghost" href="/shop">See what it sells <Arrow /></a>
          </div>
        {:else}
          <p>There's no record for this shop on file, so there's nothing to sign or check. That says nothing bad about the shop.</p>
          {#if p.shows_unverifiable_badge}<p class="notice">This shop displays a trust badge. No published key verifies it. <a href="/verify?shop={p.merchant_id}">See the check fail</a>.</p>{/if}
        {/if}
      </div>
    </div>

    {#if p.has_record}
      <h2>The published rules for {p.business_type_label.toLowerCase()}</h2>
      <table class="plain rules">
        <thead><tr><th>Rule</th><th>Measured</th><th>Counted</th><th>Result</th></tr></thead>
        <tbody>
          {#each data.rules as r}
            <tr>
              <td>{r.rule_label}</td>
              <td class="num">{r.rule === 'enough_history' ? `${p.orders_completed} orders, ${p.history_days} days` : r.measured ? `${r.measured_value}%` : 'Not measured'}</td>
              <td>{r.denominator ? `${r.numerator} of ${r.denominator}` : ''}</td>
              <td><span class="res" class:met={r.met}>{r.met ? 'Met' : 'Not met'}</span></td>
            </tr>
          {/each}
        </tbody>
      </table>

      <h2>Every fact, and where it came from</h2>
      <div class="facts">
        {#each data.facts as f}
          <div class="fact">
            <span class="label">{f.label}</span>
            <span class="num v">{shown(f)}</span>
            <span class="small">{f.denominator ? `${f.numerator} of ${f.denominator}, ` : ''}{f.window_label}</span>
            <span class="small layer">{f.layer.slice(2)}</span>
            <span class="ev {f.evidence_class}">{evidenceLabel[f.evidence_class]}</span>
          </div>
        {/each}
      </div>
      {#if p.hidden_metrics.length}<p class="small">The owner chose not to disclose: {p.hidden_metrics.join(', ').replaceAll('_', ' ')}. Rule results can never be hidden.</p>{/if}
      <p class="notice">Real Deal Seal signs this passport with its own key. PayPal supplied the sandbox records, not the signature, and does not endorse the shop.</p>

      <button class="btn ghost json" onclick={() => (showJson = !showJson)}>{showJson ? 'Hide' : 'Show'} the signed credential</button>
      {#if showJson}<pre>{JSON.stringify(data.seal, null, 2)}</pre>{/if}
    {/if}
  {:else}<p>Loading the passport.</p>{/if}
</section>

<style>
  .top { display: grid; grid-template-columns: minmax(320px, 440px) 1fr; gap: clamp(28px, 5vw, 72px); align-items: start; margin-bottom: 72px; }
  h1 { font-size: clamp(2.6rem, 6vw, 5rem); margin-bottom: 20px; }
  h2 { font-size: clamp(1.8rem, 3.4vw, 2.8rem); margin: 64px 0 22px; }
  .actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 26px; }
  .res { font-weight: 700; color: var(--red); }
  .res.met { color: var(--ink); }
  .res.met::before { content: '✓ '; }
  .res:not(.met)::before { content: '✕ '; }
  .facts { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px; margin-bottom: 28px; }
  .fact { background: var(--tile); padding: 22px; display: grid; gap: 4px; align-content: start; }
  .v { font-size: 2.4rem; font-weight: 300; color: var(--ink); line-height: 1.05; }
  .ev { justify-self: start; margin-top: 10px; font-size: 0.78rem; font-weight: 600; padding: 3px 9px; border-radius: 999px; background: #fff; box-shadow: inset 0 0 0 1.2px var(--ink); }
  .ev.simulated { box-shadow: inset 0 0 0 1.2px var(--muted); color: var(--muted); border-radius: 3px; border: 0; background: repeating-linear-gradient(135deg, #fff 0 6px, #ececec 6px 7px); }
  .ev.merchant_reported { box-shadow: inset 0 0 0 1.2px var(--ink); border-radius: 3px; }
  .ev.paypal_sandbox_confirmed { background: var(--ink); color: #fff; box-shadow: none; }
  .json { margin: 28px 0 14px; }
  .layer { text-transform: capitalize; }
  @media (max-width: 900px) { .top { grid-template-columns: 1fr; } .facts { grid-template-columns: 1fr 1fr; } }
  @media (max-width: 560px) { .facts { grid-template-columns: 1fr; } }
</style>
