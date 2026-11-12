<script>
  // The mark: a seal (the animal) inside a seal (the stamp). Original artwork.
  let { size = 44, tone = 'red' } = $props();
  const bg = $derived(tone === 'red' ? '#d9201f' : tone === 'white' ? '#fff' : '#0a0a0a');
  const fg = $derived(tone === 'white' ? '#d9201f' : '#fff');
</script>

<svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-label="Real Deal Seal">
  <g fill={bg}>
    {#each Array(16) as _, i}
      <circle cx={32 + 28 * Math.cos((i * Math.PI) / 8)} cy={32 + 28 * Math.sin((i * Math.PI) / 8)} r="5.2" />
    {/each}
    <circle cx="32" cy="32" r="28" />
  </g>
  <path d="M15 45c0-13 7-25 19-25 8 0 13 5 13 11 0 5-3 8-6 9l8 7H23c-5 0-8-1-8-2z" fill={fg} />
  <circle cx="38" cy="29" r="2.4" fill={bg} />
  <circle cx="46.5" cy="32" r="1.9" fill={bg} />
  <path d="M41 35l9-1M41 37l9 2" stroke={bg} stroke-width="1.2" stroke-linecap="round" />
</svg>
