<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import PassportCard from '$lib/components/PassportCard.svelte';
  let shops = $state([]);
  onMount(async () => (shops = await api('/api/merchants')));
</script>

<svelte:head><title>Passports | Real Deal Seal</title></svelte:head>

<section class="wrap section">
  <h1>Passports</h1>
  <p class="lede top">Every shop is judged by the published rules for its type of business. Open a passport to see each fact, what was counted and how strong the evidence is.</p>
  <div class="grid3">
    {#each shops as shop}<PassportCard {shop} href="/shops/{shop.merchant_id}" />{/each}
  </div>
  <p class="notice">Babel Home, Hearthline Home and Linen Palace never joined, so we have no record and can’t vouch for them either way. Violet &amp; Vine Home and Juniper &amp; Oak Goods joined, but their seals were withdrawn for cause. Linen Palace also displays a badge that no published key verifies; <a href="/verify?shop=palace">check it yourself</a>.</p>
</section>

<style>
  .top { margin: 24px 0 44px; }
  .grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; margin-bottom: 36px; }
  @media (max-width: 1000px) { .grid3 { grid-template-columns: 1fr; } }
</style>
