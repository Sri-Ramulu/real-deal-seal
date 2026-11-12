<script>
  import '../app.css';
  import Nav from '$lib/components/Nav.svelte';
  import Footer from '$lib/components/Footer.svelte';
  let { children } = $props();
</script>

<a class="skip" href="#main">Skip to content</a>
<Nav />
<main id="main">{@render children()}</main>
<Footer />

<style>
  .skip { position: absolute; left: -999px; top: 8px; background: var(--ink); color: #fff; padding: 10px 14px; border-radius: 4px; z-index: 100; }
  .skip:focus { left: 12px; }
  main { min-height: 70vh; }
</style>
