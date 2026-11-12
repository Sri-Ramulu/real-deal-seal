<script>
  import '../app.css';
  import Nav from '$lib/components/Nav.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import { onMount } from 'svelte';
  let { children } = $props();
  let main;
  // Sections below the fold ease in as they are scrolled to. Anything already on screen, and everything when JavaScript
  // is off or reduced motion is asked for, is simply shown.
  onMount(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) return;
    const seen = new WeakSet();
    const io = new IntersectionObserver((entries) => entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('shown'); io.unobserve(e.target); } }), { rootMargin: '0px 0px -8% 0px' });
    const scan = () => main.querySelectorAll('section, section .card, section article').forEach((el) => {
      if (seen.has(el)) return; seen.add(el);
      if (el.getBoundingClientRect().top > innerHeight * 0.92) { el.classList.add('pre'); io.observe(el); }
    });
    scan();
    const mo = new MutationObserver(scan); mo.observe(main, { childList: true, subtree: true });
    return () => { io.disconnect(); mo.disconnect(); };
  });
</script>

<a class="skip" href="#main">Skip to content</a>
<Nav />
<main id="main" bind:this={main}>{@render children()}</main>
<Footer />

<style>
  .skip { position: absolute; left: -999px; top: 8px; background: var(--ink); color: #fff; padding: 10px 14px; border-radius: 4px; z-index: 100; }
  .skip:focus { left: 12px; }
  main { min-height: 70vh; }
</style>
