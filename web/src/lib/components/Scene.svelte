<script>
  import SealFigure from './SealFigure.svelte';
  import Parcel from './Parcel.svelte';
  let { children } = $props();
</script>

<!-- Footer scene: one seal checks the stacks, another wheels sealed parcels out. A single ground line ties it together. -->
<div class="scene">
  <svg viewBox="0 0 1200 330" role="img" aria-label="A seal in a red cap checks stacked parcels; another wheels sealed parcels away.">
    <SealFigure x={10} y={120} holding="clipboard" />
    {#each [0, 1, 2, 3, 4, 5] as i}<Parcel x={236} y={320 - i * 44} w={86} h={42} tone="red" />{/each}
    {#each [0, 1, 2] as i}<Parcel x={326} y={320 - i * 44} w={86} h={42} tone="black" />{/each}
    {#each [0, 1, 2, 3] as i}<Parcel x={416} y={320 - i * 34} w={44} h={32} tone="red" />{/each}

    <g transform="translate(760 0)">
      {#each [0, 1, 2] as r}{#each [0, 1] as c}<Parcel x={c * 92} y={296 - r * 50} w={88} h={48} tone={(r + c) % 2 ? 'black' : 'red'} mark />{/each}{/each}
      <path d="M-14 300h206l10-170h22" fill="none" stroke="#9a9a9a" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" />
      <circle cx="18" cy="306" r="13" fill="#0a0a0a" /><circle cx="18" cy="306" r="5" fill="#d9201f" />
      <circle cx="170" cy="306" r="13" fill="#0a0a0a" /><circle cx="170" cy="306" r="5" fill="#d9201f" />
    </g>
    <SealFigure x={1000} y={120} flip />
    <path d="M0 322h1200" stroke="#0a0a0a" stroke-width="6" />
  </svg>
  <div class="mid">{@render children?.()}</div>
</div>

<style>
  .scene { position: relative; }
  .mid { position: absolute; left: 50%; top: 46%; transform: translate(-50%, -50%); text-align: center; width: min(360px, 34%); }
  @media (max-width: 760px) { .mid { position: static; transform: none; width: auto; margin-top: 24px; } }
</style>
