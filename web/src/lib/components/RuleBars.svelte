<script>
  // One bar per shop against a published threshold. The bar is red only when the rule is not met; otherwise ink. Values are labeled.
  let { rows, threshold, direction = 'min', unit = '%', max = 100 } = $props();
  // rows: [{name, value, counted, met}]. The scale grows to the largest value (rounded up to 10), so no bar runs past its track.
  const top = $derived(Math.max(max, Math.ceil(Math.max(0, ...rows.map((r) => Number(r.value) || 0)) / 10) * 10));
  const pct = (v) => Math.min(100, (v / top) * 100);
</script>

<div class="bars">
  {#each rows as r}
    <div class="row" title={r.counted}>
      <span class="name">{r.name}</span>
      <span class="track">
        <span class="fill" class:miss={!r.met} style="width:{Math.max(1.5, pct(r.value))}%"></span>
        <span class="mark" style="left:{pct(threshold)}%"></span>
      </span>
      <span class="val num">{r.value}{unit}</span>
      <span class="small counted">{r.counted}</span>
    </div>
  {/each}
  <div class="row legend"><span></span><span class="track bare"><span class="tag" style="left:{pct(threshold)}%">{direction === 'min' ? 'at least' : 'at most'} {threshold}{unit}</span></span></div>
</div>

<style>
  .bars { display: grid; gap: 10px; }
  .row { display: grid; grid-template-columns: 150px 1fr 56px 110px; gap: 12px; align-items: center; }
  .name { font-weight: 600; font-size: 0.95rem; }
  .track { position: relative; min-width: 0; height: 18px; background: var(--tile); border-radius: 0 4px 4px 0; }
  .track.bare { background: none; height: 20px; }
  .fill { position: absolute; inset: 0 auto 0 0; background: var(--ink); border-radius: 0 4px 4px 0; transition: width 0.8s var(--ease); }
  .fill.miss { background: var(--red); }
  .mark { position: absolute; top: -5px; bottom: -5px; width: 2px; background: var(--ink); }
  .tag { position: absolute; transform: translateX(-50%); font-size: 0.78rem; color: var(--muted); white-space: nowrap; }
  .val { font-size: 1.1rem; font-weight: 600; text-align: right; }
  .counted { white-space: nowrap; }
  @media (max-width: 640px) { .row { grid-template-columns: 96px 1fr 48px; } .counted { display: none; } }
</style>
