<script>
  import Parcel from './Parcel.svelte';
  let { children } = $props();
</script>

<!-- Footer scene, read left to right: a shop owner in a red cap ticks off a stack of parcels on a clipboard, and a courier
     pushes a cart of sealed parcels out to the right. Original line-and-flat-colour artwork in red, black and white.
     Motion stops for people who ask for reduced motion. -->
<div class="scene">
  <svg viewBox="0 0 1200 330" role="img" aria-label="A shop owner in a red cap ticks off a stack of parcels on a clipboard. A courier pushes a cart of sealed parcels away to the right.">
    <!-- the shop owner -->
    <g transform="translate(96 322)" stroke-linecap="round" stroke-linejoin="round">
      <path d="M14 0h36c0-8-8-12-18-12H14z" fill="#0a0a0a" /><path d="M-4 0h36c0-8-8-12-18-12H-4z" fill="#0a0a0a" />
      <path d="M-2 -134h50l-8 124H2z" fill="#0a0a0a" /><path d="M23 -100l-1 88" stroke="#dddddd" stroke-width="2" />
      <path d="M-6 -212c0-12 8-20 20-20h18c12 0 20 8 20 20l2 84H-8z" fill="#fff" stroke="#0a0a0a" stroke-width="4" />
      <path d="M6 -196h34l4 104H2z" fill="#d9201f" /><path d="M10 -196l6-34M36 -196l-6-34" stroke="#d9201f" stroke-width="4" />
      <rect x="15" y="-150" width="18" height="20" rx="2" fill="none" stroke="#fff" stroke-width="2.5" />
      <path d="M16 -236h14v12H16z" fill="#fff" stroke="#0a0a0a" stroke-width="4" />
      <path d="M0 -262c-6 10-6 26 4 36 6-4 8-12 8-20z" fill="#0a0a0a" />
      <circle cx="24" cy="-256" r="21" fill="#fff" stroke="#0a0a0a" stroke-width="4" />
      <path d="M2 -262c0-16 10-25 23-25s22 9 22 23z" fill="#d9201f" /><path d="M44 -266h22c0 5-5 8-11 8H44z" fill="#d9201f" />
      <g class="eye"><circle cx="33" cy="-252" r="2.6" fill="#0a0a0a" /></g><path d="M29 -243q6 4 11 0" fill="none" stroke="#0a0a0a" stroke-width="2.5" />
      <!-- clipboard, held out towards the stack -->
      <g transform="rotate(10 82 -186)">
        <rect x="58" y="-218" width="48" height="62" rx="3" fill="#b9b9b9" stroke="#0a0a0a" stroke-width="3" /><rect x="72" y="-224" width="20" height="10" rx="2" fill="#0a0a0a" />
        <path d="M66 -200h32M66 -188h32M66 -176h18" stroke="#fff" stroke-width="3.5" />
        <path class="tick" d="M84 -172l5 6 12-15" fill="none" stroke="#d9201f" stroke-width="4" pathLength="1" />
      </g>
      <path d="M40 -214L46 -172L72 -164" fill="none" stroke="#0a0a0a" stroke-width="17" /><path d="M40 -214L46 -172L72 -164" fill="none" stroke="#fff" stroke-width="9" />
      <circle cx="74" cy="-164" r="7" fill="#fff" stroke="#0a0a0a" stroke-width="3" />
      <g class="pencil"><path d="M92 -206l12-22" stroke="#d9201f" stroke-width="5" /><circle cx="90" cy="-202" r="6.5" fill="#fff" stroke="#0a0a0a" stroke-width="3" /></g>
    </g>

    {#each [0, 1, 2, 3, 4, 5] as i}<Parcel x={236} y={320 - i * 44} w={86} h={42} tone="red" />{/each}
    {#each [0, 1, 2] as i}<Parcel x={326} y={320 - i * 44} w={86} h={42} tone="black" />{/each}
    {#each [0, 1, 2, 3] as i}<Parcel x={416} y={320 - i * 34} w={44} h={32} tone="red" />{/each}
    <!-- the owner's marks land on the stack one by one -->
    {#each [0, 1, 2, 3, 4, 5] as i}
      <g transform="translate(304 {307 - i * 44})"><g class="checked" style="animation-delay: {i * 0.5}s">
        <circle r="8" fill="#fff" /><path d="M-4 0l3 3 5-6" fill="none" stroke="#0a0a0a" stroke-width="2.2" stroke-linecap="round" />
      </g></g>
    {/each}

    <!-- the courier and the cart, heading out to the right -->
    <path class="speed" d="M786 196h24M776 232h34M790 268h20" stroke="#9a9a9a" stroke-width="3" stroke-linecap="round" />
    <g class="haul">
      <g transform="translate(850 322)" stroke-linecap="round" stroke-linejoin="round">
        <!-- back leg, then front leg, mid-stride -->
        <path d="M22 -128L4 -66L-20 -14" fill="none" stroke="#0a0a0a" stroke-width="21" /><path d="M-34 -4l22-16 10 12-20 16z" fill="#0a0a0a" /><path d="M-30 4l18-13" stroke="#fff" stroke-width="2.5" />
        <path d="M26 -128L52 -70L58 -14" fill="none" stroke="#0a0a0a" stroke-width="21" /><path d="M46 0h40c0-8-8-13-20-13H46z" fill="#0a0a0a" /><path d="M48 -3h34" stroke="#fff" stroke-width="2.5" />
        <!-- red jacket, leaning into the push -->
        <path d="M6 -220c2-10 10-16 20-14l16 3c10 2 16 10 14 20l-10 88H0z" fill="#d9201f" stroke="#0a0a0a" stroke-width="4" />
        <path d="M30 -232l-6 108" stroke="#0a0a0a" stroke-width="2.5" /><rect x="34" y="-176" width="14" height="16" rx="2" fill="#fff" />
        <path d="M30 -244h14v14H30z" fill="#fff" stroke="#0a0a0a" stroke-width="4" />
        <circle cx="42" cy="-262" r="21" fill="#fff" stroke="#0a0a0a" stroke-width="4" />
        <path d="M20 -268c0-16 10-25 23-25s22 9 22 23z" fill="#0a0a0a" /><path d="M62 -272h22c0 5-5 8-11 8H62z" fill="#0a0a0a" />
        <g class="eye"><circle cx="51" cy="-258" r="2.6" fill="#0a0a0a" /></g><path d="M47 -249q6 4 11 0" fill="none" stroke="#0a0a0a" stroke-width="2.5" />
        <!-- arms out to the handle -->
        <path d="M40 -214L70 -184L104 -158" fill="none" stroke="#0a0a0a" stroke-width="17" /><path d="M40 -214L70 -184L104 -158" fill="none" stroke="#d9201f" stroke-width="9" />
        <circle cx="106" cy="-156" r="7.5" fill="#fff" stroke="#0a0a0a" stroke-width="3" />
      </g>
      <!-- parcels on the deck: two, two, and one on top -->
      {#each [0, 1] as r}{#each [0, 1] as c}<Parcel x={986 + c * 98} y={288 - r * 48} w={94} h={46} tone={(r + c) % 2 ? 'black' : 'red'} mark />{/each}{/each}
      <Parcel x={1035} y={192} w={94} h={46} tone="red" mark />
      <!-- cart: push handle with a grip, a flat deck with a toe lip, a big fixed wheel and a small caster -->
      <path d="M950 166h10c10 0 16 6 16 16v106" fill="none" stroke="#9a9a9a" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M968 292h220v-10" fill="none" stroke="#0a0a0a" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M1164 296v6" stroke="#0a0a0a" stroke-width="6" />
      <g class="wheel"><circle cx="998" cy="304" r="15" fill="#0a0a0a" /><circle cx="998" cy="304" r="6" fill="#d9201f" /><path d="M998 291v26M985 304h26" stroke="#fff" stroke-width="1.6" /></g>
      <g class="wheel fast"><circle cx="1164" cy="310" r="9" fill="#0a0a0a" /><circle cx="1164" cy="310" r="3.5" fill="#d9201f" /><path d="M1164 302v16M1156 310h16" stroke="#fff" stroke-width="1.4" /></g>
    </g>
    <path d="M0 322h1200" stroke="#0a0a0a" stroke-width="6" />
  </svg>
  <div class="mid">{@render children?.()}</div>
</div>

<style>
  .scene { position: relative; }
  .mid { position: absolute; left: 51%; top: 50%; transform: translate(-50%, -50%); text-align: center; width: min(360px, 30%); }
  .eye { transform-box: fill-box; transform-origin: center; animation: blink 5.5s infinite; }
  .tick { stroke-dasharray: 1; stroke-dashoffset: 1; animation: tick 8s infinite; }
  .pencil { animation: pencil 8s infinite; }
  .checked { opacity: 0; transform-box: fill-box; transform-origin: center; animation: checked 8s infinite; }
  .speed { animation: speed 1.2s linear infinite; }
  .haul { animation: haul 6s ease-in-out infinite alternate; }
  .wheel { transform-box: fill-box; transform-origin: center; animation: wheel 2.4s linear infinite; }
  .wheel.fast { animation-duration: 1.4s; }
  @keyframes blink { 0%, 46%, 50%, 100% { transform: scaleY(1); } 48% { transform: scaleY(0.1); } }
  @keyframes tick { 0%, 20% { stroke-dashoffset: 1; } 30%, 88% { stroke-dashoffset: 0; } 96%, 100% { stroke-dashoffset: 1; } }
  @keyframes pencil { 0%, 18%, 32%, 100% { transform: translate(0, 0); } 22% { transform: translate(-3px, 5px); } 27% { transform: translate(4px, 1px); } }
  @keyframes checked { 0%, 28% { opacity: 0; transform: scale(0.2); } 34%, 90% { opacity: 1; transform: scale(1); } 98%, 100% { opacity: 0; } }
  @keyframes speed { from { opacity: 0.9; transform: translateX(6px); } to { opacity: 0; transform: translateX(-10px); } }
  @keyframes haul { from { transform: translateX(0); } to { transform: translateX(6px); } }
  @keyframes wheel { to { transform: rotate(360deg); } }
  @media (max-width: 760px) { .mid { position: static; transform: none; width: auto; margin-top: 24px; } }
</style>
