<script>
  import { page } from '$app/state';
  import SealMark from './SealMark.svelte';
  import Arrow from './Arrow.svelte';

  let open = $state(false);
  const links = [
    ['/shop', 'Shop'],
    ['/shops', 'Passports'],
    ['/studio', 'Merchant Studio'],
    ['/scorecard', 'Scorecard'],
    ['/proof', 'Proof'],
    ['/story', 'The story'],
    ['/developers', 'Developers']
  ];
  $effect(() => { page.url.pathname; open = false; });
</script>

<header class="bar wrap">
  <a class="brand" href="/" aria-label="Real Deal Seal, home">
    <SealMark size={34} tone="white" />
    <span>Real Deal Seal</span>
  </a>
  <nav class:open aria-label="Main">
    {#each links as [href, label]}
      <a {href} aria-current={page.url.pathname === href || page.url.pathname.startsWith(href + '/') ? 'page' : undefined}>{label}</a>
    {/each}
  </nav>
  <a class="plain" href="/verify">Check a seal <Arrow size={12} /></a>
  <a class="cta" href="/assistant">Ask the assistant <Arrow size={12} /></a>
  <button class="burger" aria-expanded={open} aria-label="Menu" onclick={() => (open = !open)}><span></span><span></span></button>
</header>

<style>
  .bar { position: sticky; top: 14px; z-index: 50; display: flex; align-items: stretch; background: #fff; border-radius: 6px; margin-top: 14px;
    box-shadow: 0 1px 0 rgba(0, 0, 0, 0.06), 0 12px 32px -18px rgba(0, 0, 0, 0.35); min-height: 62px; }
  .brand { display: flex; align-items: center; gap: 10px; padding: 0 20px 0 14px; background: var(--red); color: #fff; text-decoration: none;
    font: 600 1.1rem var(--display); letter-spacing: -0.02em; border-radius: 6px 0 0 6px; white-space: nowrap; }
  nav { display: flex; align-items: center; gap: 4px; padding: 0 14px; flex: 1; border-right: 1px solid var(--line); }
  nav a { padding: 8px 10px; text-decoration: none; font-size: 0.97rem; border-radius: 4px; white-space: nowrap; }
  nav a:hover { background: var(--tile); }
  nav a[aria-current='page'] { box-shadow: inset 0 -2px 0 var(--red); border-radius: 0; }
  .plain, .cta { display: flex; align-items: center; gap: 12px; padding: 0 20px; text-decoration: none; font-size: 0.97rem; white-space: nowrap; }
  .plain:hover { background: var(--tile); }
  .cta { background: var(--red); color: #fff; border-radius: 0 6px 6px 0; transition: background 0.2s; }
  .cta:hover { background: var(--red-deep); }
  .cta :global(svg), .plain :global(svg) { transition: transform 0.25s var(--ease); }
  .cta:hover :global(svg), .plain:hover :global(svg) { transform: translateX(4px); }
  .burger { display: none; }
  @media (max-width: 1120px) {
    nav { display: none; position: absolute; top: calc(100% + 6px); left: 0; right: 0; background: #fff; border-radius: 6px; flex-direction: column;
      align-items: stretch; padding: 10px; box-shadow: 0 18px 40px -16px rgba(0, 0, 0, 0.4); border: 0; }
    nav.open { display: flex; }
    nav a { padding: 14px; font-size: 1.05rem; }
    .plain { display: none; }
    .brand { flex: 1; border-radius: 6px 0 0 6px; }
    .cta { border-radius: 0; }
    .burger { display: grid; place-content: center; gap: 6px; width: 62px; background: #fff; border: 0; border-radius: 0 6px 6px 0; cursor: pointer; }
    .burger span { display: block; width: 22px; height: 2px; background: var(--ink); }
  }
  @media (max-width: 560px) { .cta { display: none; } .burger { border-left: 1px solid var(--line); } }
</style>
