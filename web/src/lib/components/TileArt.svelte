<script>
  // Flat 2D tile illustrations, drawn for this product. Red, black, grey; no gradients.
  let { name } = $props();
</script>

<svg viewBox="0 0 320 190" aria-hidden="true">
  <ellipse cx="160" cy="176" rx="120" ry="7" fill="#000" opacity="0.07" />
  {#if name === 'passport'}
    <g transform="rotate(-8 160 95)">
      <rect x="98" y="22" width="124" height="150" rx="8" fill="#b81a19" />
      <rect x="92" y="18" width="124" height="150" rx="8" fill="var(--art, #d9201f)" stroke="var(--art-line, transparent)" stroke-width="2" />
      <circle cx="154" cy="78" r="26" fill="none" stroke="#fff" stroke-width="4" />
      <path d="M140 88c0-10 5-18 14-18 6 0 10 4 10 8s-2 6-4 7l5 5h-18c-4 0-7-1-7-2z" fill="#fff" />
      <path d="M120 126h68M132 140h44" stroke="#fff" stroke-width="5" stroke-linecap="round" />
    </g>
  {:else if name === 'evidence'}
    <rect x="62" y="30" width="196" height="132" rx="6" fill="#fff" stroke="#0a0a0a" stroke-width="3" />
    <rect x="62" y="30" width="196" height="26" rx="6" fill="#0a0a0a" />
    {#each [0, 1, 2, 3] as i}<path d="M74 {76 + i * 24}h{[150, 120, 160, 100][i]}" stroke={i === 1 ? '#d9201f' : '#bdbdbd'} stroke-width="8" stroke-linecap="round" />{/each}
    <circle cx="236" cy="132" r="26" fill="#fff" stroke="var(--art, #d9201f)" stroke-width="7" />
    <path d="M254 152l22 22" stroke="var(--art, #d9201f)" stroke-width="9" stroke-linecap="round" />
  {:else if name === 'seal'}
    <g fill="var(--art, #d9201f)">
      {#each Array(18) as _, i}<circle cx={124 + 58 * Math.cos((i * Math.PI) / 9)} cy={104 + 58 * Math.sin((i * Math.PI) / 9)} r="9" />{/each}
      <circle cx="124" cy="104" r="58" />
    </g>
    <path d="M96 106l20 20 38-44" fill="none" stroke="#fff" stroke-width="11" />
    <rect x="206" y="34" width="46" height="64" rx="10" fill="#0a0a0a" />
    <rect x="192" y="96" width="74" height="18" rx="4" fill="#0a0a0a" />
    <rect x="198" y="118" width="62" height="6" fill="var(--art, #d9201f)" />
  {:else if name === 'assistant'}
    <path d="M52 34h150a12 12 0 0 1 12 12v56a12 12 0 0 1-12 12H104l-28 24v-24H52a12 12 0 0 1-12-12V46a12 12 0 0 1 12-12z" fill="#0a0a0a" />
    <path d="M64 62h112M64 84h76" stroke="#fff" stroke-width="7" stroke-linecap="round" />
    <path d="M168 86h100a10 10 0 0 1 10 10v44a10 10 0 0 1-10 10h-12v20l-24-20h-64a10 10 0 0 1-10-10V96a10 10 0 0 1 10-10z" fill="var(--art, #d9201f)" stroke="#f2f2f2" stroke-width="4" />
    <path d="M186 124l12 12 26-28" fill="none" stroke="#fff" stroke-width="7" />
    <path d="M236 118h26" stroke="#fff" stroke-width="7" stroke-linecap="round" />
  {:else if name === 'checkout'}
    <rect x="56" y="48" width="170" height="104" rx="10" fill="#0a0a0a" />
    <rect x="56" y="70" width="170" height="20" fill="#5c5c5c" />
    <rect x="72" y="112" width="60" height="12" rx="3" fill="#fff" />
    <circle cx="232" cy="118" r="42" fill="var(--art, #d9201f)" stroke="#f2f2f2" stroke-width="5" />
    <path d="M212 118l14 14 28-32" fill="none" stroke="#fff" stroke-width="9" />
  {:else if name === 'coach'}
    <rect x="88" y="26" width="128" height="148" rx="8" fill="#fff" stroke="#0a0a0a" stroke-width="3" />
    <rect x="126" y="16" width="52" height="22" rx="5" fill="#0a0a0a" />
    {#each [0, 1, 2] as i}
      <rect x="104" y={58 + i * 34} width="20" height="20" rx="3" fill={i < 2 ? 'var(--art, #d9201f)' : '#fff'} stroke={i < 2 ? 'none' : '#0a0a0a'} stroke-width="2.5" />
      {#if i < 2}<path d="M108 {68 + i * 34}l5 5 8-10" fill="none" stroke="#fff" stroke-width="3" />{/if}
      <path d="M136 {68 + i * 34}h62" stroke="#bdbdbd" stroke-width="7" stroke-linecap="round" />
    {/each}
    <path d="M236 150V70M214 92l22-24 22 24" fill="none" stroke="var(--art, #d9201f)" stroke-width="10" />
  {:else if name === 'statement'}
    <rect x="76" y="20" width="140" height="156" rx="6" fill="#fff" stroke="#0a0a0a" stroke-width="3" />
    {#each [0, 1, 2, 3, 4] as i}<rect x={96 + i * 22} y={130 - [30, 52, 44, 70, 86][i]} width="14" height={[30, 52, 44, 70, 86][i]} fill={i === 4 ? 'var(--art, #d9201f)' : '#0a0a0a'} />{/each}
    <path d="M92 132h108M92 150h70" stroke="#0a0a0a" stroke-width="3" />
    <g fill="var(--art, #d9201f)">{#each Array(12) as _, i}<circle cx={228 + 24 * Math.cos((i * Math.PI) / 6)} cy={142 + 24 * Math.sin((i * Math.PI) / 6)} r="5" />{/each}<circle cx="228" cy="142" r="24" /></g>
    <path d="M217 143l8 8 15-17" fill="none" stroke="#fff" stroke-width="5" />
  {:else if name === 'developers'}
    <rect x="48" y="34" width="224" height="130" rx="8" fill="#0a0a0a" />
    <circle cx="66" cy="50" r="5" fill="var(--art, #d9201f)" /><circle cx="84" cy="50" r="5" fill="#5c5c5c" /><circle cx="102" cy="50" r="5" fill="#5c5c5c" />
    <path d="M78 96l24 18-24 18" fill="none" stroke="var(--art, #d9201f)" stroke-width="8" />
    <path d="M118 134h56" stroke="#fff" stroke-width="8" stroke-linecap="round" />
    <path d="M196 84h52M196 104h36" stroke="#5c5c5c" stroke-width="7" stroke-linecap="round" />
  {:else}
    <path d="M52 78l22-44h172l22 44z" fill="#0a0a0a" />
    {#each [0, 1, 2, 3, 4, 5] as i}<path d="M{52 + i * 36} 78a18 16 0 0 0 36 0z" fill={i % 2 ? '#fff' : 'var(--art, #d9201f)'} stroke="#0a0a0a" stroke-width="2.5" />{/each}
    <rect x="66" y="94" width="188" height="80" fill="#fff" stroke="#0a0a0a" stroke-width="3" />
    <rect x="84" y="112" width="68" height="40" fill="#dedede" stroke="#0a0a0a" stroke-width="2.5" />
    <rect x="182" y="110" width="50" height="64" fill="var(--art, #d9201f)" />
    <circle cx="222" cy="144" r="3.5" fill="#fff" />
  {/if}
</svg>
