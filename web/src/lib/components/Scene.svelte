<script>
  let { children } = $props();
</script>

<!-- Footer scene, the owner's own artwork (static/art/scene), cut into layers so parts of it can move: three small shops in
     front of a faded chain, a shop owner showing her passport to an AI assistant, checked parcels, the seal holding one, a
     courier wheeling the sealed parcels out, and a shopper waving at the door. The logo and tagline are part of the art;
     the same words are kept as hidden text for screen readers. Motion stops for reduced-motion users. -->
<div class="scene">
  <div class="sr">{@render children?.()}</div>
  <div class="art" role="img" aria-label="Real Deal Seal. Proof beats brand. Three small shops stand in front of a faded chain store. A shop owner in a red cap shows her passport to a robot assistant holding a magnifying glass. Beside them are stacks of ticked parcels, a seal in a red cap holding a sealed parcel, a courier pushing a cart of sealed parcels, and a shopper waving from a red front door.">
    <img class="street" src="/art/scene/street.webp" alt="" width="2172" height="676" loading="lazy" />
    <img class="mark" src="/art/scene/mark.webp" alt="" loading="lazy" style="left: 45.442%; top: 3.254%; width: 9.116%" />
    <img class="robot" src="/art/scene/robot.webp" alt="" loading="lazy" style="left: 27.716%; top: 51.036%; width: 8.794%" />
    <img class="seal" src="/art/scene/seal.webp" alt="" loading="lazy" style="left: 46.593%; top: 57.988%; width: 12.615%" />
    <span class="speed" aria-hidden="true"><i></i><i></i><i></i></span>
    <img class="courier" src="/art/scene/courier.webp" alt="" loading="lazy" style="left: 60.083%; top: 34.467%; width: 25.368%" />
  </div>
</div>

<style>
  .scene { border-bottom: 5px solid var(--ink); }
  .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
  .art { position: relative; aspect-ratio: 2172 / 676; overflow: hidden; }
  .art img { position: absolute; display: block; height: auto; max-width: none; }
  .street { left: 0; top: 0; width: 100%; }
  .mark { transform-origin: 50% 50%; animation: mark 5s ease-in-out infinite; }
  .robot { transform-origin: 55% 100%; animation: scan 3.4s ease-in-out infinite alternate; }
  .seal { transform-origin: 40% 100%; animation: breathe 2.8s ease-in-out infinite alternate; }
  .courier { animation: push 5s ease-in-out infinite alternate; }
  .speed { position: absolute; left: 58.9%; top: 72%; width: 1.9%; height: 20%; display: grid; align-content: space-around; }
  .speed i { display: block; height: 3px; border-radius: 2px; background: #9a9a9a; animation: speed 1.2s linear infinite; }
  .speed i:nth-child(2) { width: 70%; animation-delay: 0.3s; } .speed i:nth-child(3) { width: 85%; animation-delay: 0.6s; }
  @keyframes mark { 0%, 78%, 100% { transform: scale(1) rotate(0); } 84% { transform: scale(1.08) rotate(-6deg); } 90% { transform: scale(0.98) rotate(3deg); } }
  @keyframes scan { from { transform: rotate(-2.2deg); } to { transform: rotate(1.6deg); } }
  @keyframes breathe { from { transform: scale(1, 1); } to { transform: scale(1.012, 1.03); } }
  @keyframes push { from { transform: translateX(-2.2%); } to { transform: translateX(1.2%); } }
  @keyframes speed { from { opacity: 0.9; transform: translateX(40%); } to { opacity: 0; transform: translateX(-60%); } }
</style>
