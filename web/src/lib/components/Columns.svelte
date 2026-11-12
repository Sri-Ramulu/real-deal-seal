<script>
  // Thin columns over time with a hover readout. Single series, so no legend: the title names it.
  let { points, valueKey, labelKey, format = (v) => v, height = 150, accentLast = false } = $props();
  const max = $derived(Math.max(...points.map((p) => p[valueKey]), 1));
  let hover = $state(null);
</script>

<div class="chart" style="height:{height}px" role="img" aria-label="Columns over time">
  {#each points as p, i}
    <div class="col" onpointerenter={() => (hover = i)} onpointerleave={() => (hover = null)} role="presentation">
      <span class="bar" class:accent={accentLast && i === points.length - 1} class:hot={hover === i} style="height:{(p[valueKey] / max) * 100}%"></span>
    </div>
  {/each}
</div>
<div class="foot small">
  <span>{points[0]?.[labelKey]}</span>
  <strong>{hover !== null ? `${points[hover][labelKey]}: ${format(points[hover][valueKey])}` : ''}</strong>
  <span>{points.at(-1)?.[labelKey]}</span>
</div>

<style>
  .chart { display: flex; align-items: flex-end; gap: 2px; border-bottom: 1.5px solid var(--ink); }
  .col { flex: 1; height: 100%; display: flex; align-items: flex-end; }
  .bar { width: 100%; background: var(--chart-context); border-radius: 4px 4px 0 0; min-height: 2px; transition: background 0.15s; }
  .bar.accent, .bar.hot { background: var(--red); }
  .foot { display: flex; justify-content: space-between; margin-top: 6px; }
  .foot strong { color: var(--ink); }
</style>
