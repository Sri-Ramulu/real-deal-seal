<script>
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import { api, usd } from '$lib/api.js';
  import SealMark from '$lib/components/SealMark.svelte';
  let s = $state(null), error = $state('');
  onMount(async () => { try { s = await api(`/api/checkout/${page.url.searchParams.get('token')}/complete`, {}); } catch (e) { error = e.message; } });
</script>

<section class="wrap section narrow">
  {#if error}<h1>Not paid</h1><p class="lede">{error}</p><p>Nothing was charged by this page. You can go back and try again.</p>
  {:else if s?.status === 'CAPTURED'}
    <div class="done"><SealMark size={84} /><div><span class="label">{s.mode === 'simulated' ? 'Simulated capture' : 'Confirmed by PayPal (sandbox)'}</span><h1>Paid: {usd(s.amount_usd, 2)}</h1></div></div>
    <p class="lede">{s.quantity} × {s.product_name} from {s.merchant_name}.</p>
    <table class="plain"><tbody><tr><td>PayPal order</td><td><code>{s.paypal_order_id}</code></td></tr><tr><td>Capture</td><td><code>{s.capture_id}</code></td></tr></tbody></table>
    <p class="notice">{s.note}</p>
  {:else if s}<h1>{s.status === 'CANCELLED' ? 'Cancelled' : 'Not paid yet'}</h1><p class="lede">This checkout is {s.status.toLowerCase()}. Nothing was charged.</p>
  {:else}<p>Asking PayPal whether the payment went through.</p>{/if}
  <a class="btn ghost" href="/assistant">Back to the assistant</a>
</section>

<style>.narrow { max-width: 760px; } h1 { font-size: clamp(2.4rem, 5vw, 4rem); } .done { display: flex; gap: 22px; align-items: center; margin-bottom: 20px; } table, .notice { margin: 20px 0; } .btn { margin-top: 12px; }</style>
