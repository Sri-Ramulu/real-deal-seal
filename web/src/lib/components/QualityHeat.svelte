<script>
  // Data quality heatmap: one row per contracted table, one column per kind of promise. A cell shows how many promises of
  // that kind the table makes and whether all of them held on this pipeline run. Built from the contract results, not drawn.
  let { rules = [], onpick = () => {} } = $props();
  const kinds = [
    ['Columns present', (r) => /^column .* exists$/.test(r)],
    ['Right type', (r) => / is (VARCHAR|INTEGER|BIGINT|BOOLEAN|DECIMAL|DATE|TIMESTAMP|DOUBLE)/.test(r)],
    ['Never empty', (r) => / is never null$/.test(r)],
    ['Unique', (r) => / is unique$/.test(r)],
    ['Allowed values', (r) => / in accepted values$/.test(r)],
    ['Business rules', () => true]
  ];
  const kindOf = (rule) => kinds.findIndex(([, test]) => test(rule));
  const rows = $derived.by(() => {
    const by = {};
    for (const r of rules) {
      const row = (by[r.table] ??= kinds.map(() => ({ n: 0, bad: 0, list: [] })));
      const cell = row[kindOf(r.rule)]; cell.n++; if (!r.passed) cell.bad++; cell.list.push(r);
    }
    return Object.entries(by).sort((a, b) => a[0].localeCompare(b[0]));
  });
  const max = $derived(Math.max(1, ...rows.flatMap(([, cells]) => cells.map((x) => x.n))));
  let open = $state(null);
</script>

<div class="heat" role="table" aria-label="Data quality by table and kind of promise">
  <div class="row head" role="row"><span role="columnheader">Table</span>{#each kinds as [k]}<span role="columnheader">{k}</span>{/each}</div>
  {#each rows as [table, cells]}
    <div class="row" role="row">
      <button class="t" role="rowheader" onclick={() => onpick(table)} title="Show this table's lineage and metadata">{table}</button>
      {#each cells as cell, i}
        {#if cell.n}
          <button role="cell" class="cell" class:bad={cell.bad} class:on={open?.table === table && open?.i === i}
            style="--a: {0.5 + 0.5 * (cell.n / max)}" onclick={() => (open = open?.table === table && open?.i === i ? null : { table, i, cell })}
            aria-label="{table}, {kinds[i][0]}: {cell.n - cell.bad} of {cell.n} hold">{cell.n - cell.bad}/{cell.n}</button>
        {:else}<span role="cell" class="cell none" aria-label="{table}, {kinds[i][0]}: no promises">·</span>{/if}
      {/each}
    </div>
  {/each}
</div>
<p class="small key"><i class="sw ok"></i> every promise holds (darker means more promises) <i class="sw bad"></i> at least one broken <span>· no promise of that kind</span></p>
{#if open}
  <div class="card detail">
    <strong>{open.table}: {kinds[open.i][0].toLowerCase()}</strong>
    <ul>{#each open.cell.list as r}<li><span class:x={!r.passed}>{r.passed ? '✓' : '✕'}</span> {r.rule}{#if r.detail && !r.passed} <em>({r.detail})</em>{/if}</li>{/each}</ul>
  </div>
{/if}

<style>
  .heat { display: grid; gap: 2px; overflow-x: auto; }
  .row { display: grid; grid-template-columns: minmax(190px, 1.6fr) repeat(6, minmax(78px, 1fr)); gap: 2px; min-width: 700px; }
  .head span { font-size: 0.78rem; font-weight: 700; color: var(--muted); padding: 6px 8px; }
  .t { text-align: left; border: 0; background: var(--tile); padding: 10px 12px; font: 600 0.84rem ui-monospace, 'SF Mono', Menlo, monospace; cursor: pointer; color: var(--ink); }
  .t:hover { background: var(--ink); color: #fff; }
  .cell { border: 0; padding: 10px 6px; text-align: center; font: 600 0.86rem var(--display); font-variant-numeric: tabular-nums; cursor: pointer;
    background: color-mix(in srgb, var(--ink) calc(var(--a) * 100%), #fff); color: #fff; transition: transform 0.15s var(--ease); }
  .cell:hover, .cell.on { transform: scale(1.06); outline: 2px solid var(--red); outline-offset: -2px; }
  .cell.bad { background: var(--red); }
  .cell.none { background: var(--tile); color: var(--muted); cursor: default; transform: none; outline: 0; }
  .key { margin: 12px 0 0; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; max-width: none; }
  .sw { width: 14px; height: 14px; display: inline-block; } .sw.ok { background: var(--ink); } .sw.bad { background: var(--red); margin-left: 12px; }
  .detail { margin-top: 14px; } .detail ul { list-style: none; padding: 0; margin: 10px 0 0; columns: 2; column-gap: 32px; font-size: 0.9rem; }
  .detail li { break-inside: avoid; padding: 3px 0; } .x { color: var(--red); font-weight: 700; }
  @media (max-width: 760px) { .detail ul { columns: 1; } }
</style>
