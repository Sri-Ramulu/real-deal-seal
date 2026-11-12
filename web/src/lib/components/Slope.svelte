<script>
  // Slopegraph: before and after for one or more series. One series is red; the rest are grey context. Directly labeled.
  let { series, left = 'Search only', right = 'Search + evidence', unit = '%', height = 320, max = 100 } = $props();
  const W = 640, P = { l: 150, r: 190, t: 44, b: 28 };
  const y = (v) => P.t + (1 - v / max) * (height - P.t - P.b);
  let hover = $state(null);
  // Keep the value labels at least 24px apart on each side so close values never collide.
  function spread(key) {
    const order = series.map((s, i) => ({ i, y: y(s[key]) })).sort((a, b) => a.y - b.y);
    for (let k = 1; k < order.length; k++) if (order[k].y - order[k - 1].y < 24) order[k].y = order[k - 1].y + 24;
    return Object.fromEntries(order.map((o) => [o.i, o.y]));
  }
  const ly = $derived(spread('from')), ry = $derived(spread('to'));
</script>

<svg viewBox="0 0 {W} {height}" role="img" aria-label="{left} compared with {right}">
  <text x={P.l} y="18" text-anchor="middle" class="axis">{left}</text>
  <text x={W - P.r} y="18" text-anchor="middle" class="axis">{right}</text>
  <path d="M{P.l} {P.t - 8}V{height - P.b}M{W - P.r} {P.t - 8}V{height - P.b}" stroke="#d4d4d4" stroke-width="1" />
  {#each series as s, i}
    {@const c = s.highlight ? 'var(--red)' : 'var(--chart-context)'}
    <g opacity={hover === null || hover === i ? 1 : 0.35} onpointerenter={() => (hover = i)} onpointerleave={() => (hover = null)} role="presentation">
      <path d="M{P.l} {y(s.from)}L{W - P.r} {y(s.to)}" stroke="transparent" stroke-width="22" />
      <path d="M{P.l} {y(s.from)}L{W - P.r} {y(s.to)}" stroke={c} stroke-width={s.highlight ? 4 : 2} class="draw" />
      <circle cx={P.l} cy={y(s.from)} r={s.highlight ? 7 : 5} fill={c} stroke="#fff" stroke-width="2" />
      <circle cx={W - P.r} cy={y(s.to)} r={s.highlight ? 7 : 5} fill={c} stroke="#fff" stroke-width="2" />
      <text x={P.l - 14} y={ly[i]} text-anchor="end" dominant-baseline="middle" class={s.highlight ? 'val strong' : 'val'}>{s.from}{unit}</text>
      <text x={W - P.r + 14} y={ry[i]} dominant-baseline="middle" class={s.highlight ? 'val strong' : 'val'}>{s.to}{unit} <tspan class="name">{s.name}</tspan></text>
      {#if hover === i && s.detail}<text x={W / 2} y={height - 6} text-anchor="middle" class="tip">{s.detail}</text>{/if}
    </g>
  {/each}
</svg>

<style>
  svg { width: 100%; height: auto; overflow: visible; }
  .axis { font: 600 13px var(--body); fill: var(--muted); }
  .val { font: 500 15px var(--display); fill: var(--muted); }
  .val.strong { font: 600 26px var(--display); fill: var(--ink); }
  .name { font: 500 13px var(--body); fill: var(--muted); }
  .tip { font: 500 13px var(--body); fill: var(--ink); }
  .draw { stroke-dasharray: 600; stroke-dashoffset: 600; animation: draw 1.1s var(--ease) 0.2s forwards; }
  @keyframes draw { to { stroke-dashoffset: 0; } }
</style>
