<script>
  let { children } = $props();
</script>

<!-- Footer scene: a shop owner ticks off her parcels on the left, the logo sits in the middle, and a courier wheels the
     sealed parcels out on the right. The two illustrations are original artwork made for this project (static/art). -->
<div class="scene">
  <img class="owner" src="/art/shop-owner.png" width="255" height="227" loading="lazy"
    alt="A shop owner in a red cap ticks off stacks of red and black parcels on a clipboard." />
  <div class="mid">{@render children?.()}</div>
  <img class="courier" src="/art/courier.png" width="260" height="224" loading="lazy"
    alt="A courier in a black cap pushes a cart of parcels, each marked with a tick, away to the right." />
</div>

<style>
  .scene { display: grid; grid-template-columns: auto 1fr auto; align-items: end; gap: 24px; border-bottom: 5px solid var(--ink); overflow: hidden; }
  img { display: block; height: auto; margin-bottom: -2px; }
  .owner { width: clamp(170px, 22vw, 300px); }
  .courier { width: clamp(174px, 22.5vw, 306px); animation: push 5s ease-in-out infinite alternate; }
  .mid { text-align: center; align-self: center; padding-bottom: 20px; }
  @keyframes push { from { transform: translateX(-14px); } to { transform: translateX(0); } }
  @media (max-width: 760px) {
    .scene { grid-template-columns: 1fr 1fr; }
    .mid { grid-column: 1 / -1; grid-row: 1; padding-bottom: 8px; }
    .owner { width: min(100%, 220px); } .courier { width: min(100%, 224px); justify-self: end; }
  }
</style>
