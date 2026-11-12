<script>
  import SealFigure from './SealFigure.svelte';
  import Parcel from './Parcel.svelte';
  let { children } = $props();
  const belt = [0, 1, 2, 3];
</script>

<!-- Footer scene, read left to right: a seal checks the incoming stacks, parcels ride the belt under the seal mark and come
     out sealed, and a second seal, facing out, tows the sealed parcels away to the right. Motion stops for people who ask for reduced motion. -->
<div class="scene">
  <svg viewBox="0 0 1200 330" role="img" aria-label="A seal in a red cap checks stacked parcels. Parcels ride a belt under the Real Deal Seal mark and come out sealed. Another seal tows the sealed parcels away.">
    <defs><clipPath id="beltclip"><rect x="486" y="230" width="228" height="70" /></clipPath></defs>

    <!-- far background: warehouse shelving, kept pale so the figures stay in front -->
    <g stroke="#c6c6c6" stroke-width="5" fill="none" stroke-linecap="round">
      <path d="M226 322V30h246v292M226 126h246M226 222h246" opacity="0.7" />
    </g>

    <SealFigure x={10} y={120} holding="clipboard" />
    {#each [0, 1, 2, 3, 4, 5] as i}<Parcel x={236} y={320 - i * 44} w={86} h={42} tone="red" />{/each}
    {#each [0, 1, 2] as i}<Parcel x={326} y={320 - i * 44} w={86} h={42} tone="black" />{/each}
    {#each [0, 1, 2, 3] as i}<Parcel x={416} y={320 - i * 34} w={44} h={32} tone="red" />{/each}
    <!-- the checker's marks land on the stack one by one -->
    {#each [0, 1, 2, 3, 4, 5] as i}
      <g transform="translate(304 {307 - i * 44})"><g class="checked" style="animation-delay: {i * 0.5}s">
        <circle r="8" fill="#fff" /><path d="M-4 0l3 3 5-6" fill="none" stroke="#0a0a0a" stroke-width="2.2" stroke-linecap="round" />
      </g></g>
    {/each}

    <!-- the belt: plain parcels go in, sealed parcels come out -->
    <g clip-path="url(#beltclip)">
      {#each belt as i}
        <g class="ride" style="animation-delay: {-i * 3}s">
          <rect x="430" y="262" width="52" height="36" fill={i % 2 ? '#0a0a0a' : '#d9201f'} />
          <rect x="452" y="262" width="8" height="36" fill="#fff" opacity="0.9" />
          <g class="sealed" style="animation-delay: {-i * 3}s"><circle cx="470" cy="286" r="7" fill="#fff" /><path d="M466.5 286l2.6 2.6 4.4-5" fill="none" stroke="#d9201f" stroke-width="2" stroke-linecap="round" /></g>
        </g>
      {/each}
    </g>
    <rect x="482" y="298" width="236" height="10" rx="5" fill="#0a0a0a" />
    <path class="rollers" d="M490 303h220" stroke="#fff" stroke-width="3" stroke-dasharray="3 17" stroke-linecap="round" />
    <path d="M500 308v14M700 308v14" stroke="#0a0a0a" stroke-width="6" />
    <g class="flash"><circle cx="600" cy="280" r="26" fill="none" stroke="#d9201f" stroke-width="3" /></g>

    <path class="speed" d="M722 250h18M716 270h24M724 290h16" stroke="#9a9a9a" stroke-width="3" stroke-linecap="round" />
    <g class="haul">
      <g transform="translate(760 0)">
        {#each [0, 1, 2] as r}{#each [0, 1] as c}<Parcel x={c * 92} y={296 - r * 50} w={88} h={48} tone={(r + c) % 2 ? 'black' : 'red'} mark />{/each}{/each}
        <path d="M-14 300h206l10-170h22" fill="none" stroke="#9a9a9a" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" />
        {#each [18, 170] as cx}
          <g class="wheel"><circle {cx} cy="306" r="13" fill="#0a0a0a" /><circle {cx} cy="306" r="5" fill="#d9201f" /><path d="M{cx} 297v18M{cx - 9} 306h18" stroke="#fff" stroke-width="1.6" /></g>
        {/each}
      </g>
      <SealFigure x={978} y={120} />
    </g>
    <path d="M0 322h1200" stroke="#0a0a0a" stroke-width="6" />
  </svg>
  <div class="mid">{@render children?.()}</div>
</div>

<style>
  .scene { position: relative; }
  .mid { position: absolute; left: 50%; top: 40%; transform: translate(-50%, -50%); text-align: center; width: min(360px, 34%); }
  .ride { animation: ride 12s linear infinite; }
  .sealed { opacity: 0; animation: sealed 12s linear infinite; }
  .rollers { animation: rollers 0.9s linear infinite; }
  .flash { transform-box: fill-box; transform-origin: center; opacity: 0; animation: flash 3s ease-out infinite; }
  .checked { opacity: 0; transform-box: fill-box; transform-origin: center; animation: checked 8s infinite; }
  .speed { animation: speed 1.2s linear infinite; }
  .haul { animation: haul 6s ease-in-out infinite alternate; }
  .wheel { transform-box: fill-box; transform-origin: center; animation: wheel 2.4s linear infinite; }
  @keyframes ride { from { transform: translateX(0); } to { transform: translateX(312px); } }
  @keyframes sealed { 0%, 44% { opacity: 0; } 50%, 100% { opacity: 1; } }
  @keyframes rollers { to { stroke-dashoffset: -20; } }
  @keyframes flash { 0% { transform: scale(0.4); opacity: 0.9; } 40%, 100% { transform: scale(1.5); opacity: 0; } }
  @keyframes checked { 0%, 28% { opacity: 0; transform: scale(0.2); } 34%, 90% { opacity: 1; transform: scale(1); } 98%, 100% { opacity: 0; } }
  @keyframes speed { from { opacity: 0.9; transform: translateX(6px); } to { opacity: 0; transform: translateX(-10px); } }
  @keyframes haul { from { transform: translateX(0); } to { transform: translateX(6px); } }
  @keyframes wheel { to { transform: rotate(360deg); } }
  @media (max-width: 760px) { .mid { position: static; transform: none; width: auto; margin-top: 24px; } }
</style>
