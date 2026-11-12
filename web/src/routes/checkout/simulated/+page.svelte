<script>
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { api, usd } from '$lib/api.js';
  let s = $state(null), error = $state('');
  onMount(async () => { try { s = await api(`/api/checkout/session/${page.url.searchParams.get('session')}`); } catch (e) { error = e.message; } });
</script>

<section class="wrap section narrow">
  <span class="label">Simulated checkout</span>
  <h1>This is not PayPal</h1>
  <p class="notice">No PayPal sandbox keys are configured for this shop on this server, so no PayPal call was made. On a configured server, this step is PayPal's own approval page.</p>
  {#if error}<p class="notice">{error}</p>{/if}
  {#if s}
    <p class="lede">{s.quantity} × {s.product_name} from {s.merchant_name}: <strong>{usd(s.amount_usd, 2)}</strong></p>
    <div class="actions">
      <button class="btn" onclick={() => goto(`/checkout/return?token=${s.paypal_order_id}`)}>Approve the simulated payment</button>
      <button class="btn ghost" onclick={() => goto(`/checkout/cancel?token=${s.paypal_order_id}`)}>Cancel</button>
    </div>
  {/if}
</section>

<style>.narrow { max-width: 760px; } h1 { font-size: clamp(2.4rem, 5vw, 4rem); margin: 8px 0 24px; } .actions { display: flex; gap: 12px; margin-top: 28px; flex-wrap: wrap; }</style>
