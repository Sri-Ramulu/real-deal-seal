<script>
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import { api } from '$lib/api.js';
  onMount(() => api(`/api/checkout/${page.url.searchParams.get('token')}/cancel`, {}).catch(() => {}));
</script>

<section class="wrap section" style="max-width:760px">
  <h1 style="font-size:clamp(2.4rem,5vw,4rem);margin-bottom:20px">Cancelled</h1>
  <p class="lede">You cancelled the checkout. Nothing was charged.</p>
  <a class="btn ghost" href="/assistant" style="margin-top:20px">Back to the assistant</a>
</section>
