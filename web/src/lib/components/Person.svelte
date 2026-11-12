<script>
  // A standing person in flat colour and line, feet on (x, y). Original artwork. Use inside an <svg>.
  // arm: 'out' holds something in front at about (74, -164); 'up' waves. flip faces left.
  let { x = 0, y = 0, flip = false, cap = '#d9201f', top = '#fff', apron = null, legs = '#0a0a0a', arm = 'out', hair = false } = $props();
  const d = $derived(arm === 'up' ? 'M40 -214L62 -236L70 -276' : 'M40 -214L46 -172L72 -164');
  const hand = $derived(arm === 'up' ? [71, -280] : [74, -164]);
</script>

<g transform="translate({x} {y}) scale({flip ? -1 : 1} 1)" stroke-linecap="round" stroke-linejoin="round">
  <path d="M14 0h36c0-8-8-12-18-12H14z" fill="#0a0a0a" /><path d="M-4 0h36c0-8-8-12-18-12H-4z" fill="#0a0a0a" />
  <path d="M-2 -134h50l-8 124H2z" fill={legs} stroke="#0a0a0a" stroke-width="3" /><path d="M23 -100l-1 88" stroke="#dddddd" stroke-width="2" />
  <path d="M-6 -212c0-12 8-20 20-20h18c12 0 20 8 20 20l2 84H-8z" fill={top} stroke="#0a0a0a" stroke-width="4" />
  {#if apron}<path d="M6 -196h34l4 104H2z" fill={apron} /><path d="M10 -196l6-34M36 -196l-6-34" stroke={apron} stroke-width="4" />
    <rect x="15" y="-150" width="18" height="20" rx="2" fill="none" stroke="#fff" stroke-width="2.5" />{/if}
  <path d="M16 -236h14v12H16z" fill="#fff" stroke="#0a0a0a" stroke-width="4" />
  {#if hair}<path d="M2 -268c-10 12-10 36 2 48 8-4 10-14 10-24z" fill="#0a0a0a" />{/if}
  <circle cx="24" cy="-256" r="21" fill="#fff" stroke="#0a0a0a" stroke-width="4" />
  {#if cap}<path d="M2 -262c0-16 10-25 23-25s22 9 22 23z" fill={cap} /><path d="M44 -266h22c0 5-5 8-11 8H44z" fill={cap} />
  {:else}<path d="M3 -262c0-16 10-25 22-25s21 8 21 20c-10 4-20-2-24-10-4 8-10 12-19 15z" fill="#0a0a0a" />{/if}
  <g class="eye"><circle cx="33" cy="-252" r="2.6" fill="#0a0a0a" /></g><path d="M29 -243q6 4 11 0" fill="none" stroke="#0a0a0a" stroke-width="2.5" />
  <g class:wave={arm === 'up'}>
    <path {d} fill="none" stroke="#0a0a0a" stroke-width="17" /><path {d} fill="none" stroke={top} stroke-width="9" />
    <circle cx={hand[0]} cy={hand[1]} r="7" fill="#fff" stroke="#0a0a0a" stroke-width="3" />
  </g>
</g>

<style>
  .eye { transform-box: fill-box; transform-origin: center; animation: blink 5.5s infinite; }
  .wave { transform-origin: 40px -214px; animation: wave 1.6s ease-in-out infinite alternate; }
  @keyframes blink { 0%, 46%, 50%, 100% { transform: scaleY(1); } 48% { transform: scaleY(0.1); } }
  @keyframes wave { from { transform: rotate(-7deg); } to { transform: rotate(9deg); } }
</style>
