<script>
  import { onMount } from 'svelte';
  import { AllCommunityModule, ModuleRegistry, createGrid, themeQuartz } from 'ag-grid-community';
  import { modelName } from '$lib/api.js';

  // AG Grid run explorer: every recorded pick in every full run of the evaluation. Sort, filter, group by eye, export.
  let { rows } = $props();
  let el, grid, quick = $state(''), preset = $state('all');
  const RED = { color: '#d9201f', fontWeight: 600 };
  const PRESETS = { all: null, withdrawn: { pick_kind: { filterType: 'text', type: 'equals', filter: 'Seal withdrawn' } },
    honest: { pick_kind: { filterType: 'text', type: 'equals', filter: 'Honest small shop' } },
    off: { condition_label: { filterType: 'text', type: 'equals', filter: 'Evidence off' } },
    on: { condition_label: { filterType: 'text', type: 'equals', filter: 'Evidence on' } } };

  onMount(() => {
    ModuleRegistry.registerModules([AllCommunityModule]);
    grid = createGrid(el, {
      theme: themeQuartz.withParams({ accentColor: '#d9201f', fontFamily: 'inherit', headerFontWeight: 600, borderRadius: 4, wrapperBorderRadius: 6, headerBackgroundColor: '#f2f2f2' }),
      rowData: rows,
      defaultColDef: { sortable: true, filter: true, resizable: true, floatingFilter: true, minWidth: 100 },
      columnDefs: [
        { field: 'model', headerName: 'Model', valueFormatter: (p) => modelName(p.value), width: 130 },
        { field: 'run_no', headerName: 'Run', width: 110, minWidth: 100, filter: 'agNumberColumnFilter' },
        { field: 'task_id', headerName: 'Request', width: 130, minWidth: 120, filter: 'agNumberColumnFilter' },
        { field: 'request', headerName: 'What the shopper asked', flex: 2, minWidth: 260 },
        { field: 'condition_label', headerName: 'Condition', width: 140 },
        { field: 'chosen_merchant_name', headerName: 'Shop picked', flex: 1, minWidth: 170, valueFormatter: (p) => p.value ?? 'No pick' },
        { field: 'pick_kind', headerName: 'Kind of shop', width: 170, cellStyle: (p) => (p.value === 'Seal withdrawn' || p.value === 'Forged badge' ? RED : p.value === 'Honest small shop' ? { fontWeight: 600 } : null) },
        { field: 'tool_calls', headerName: 'Tool calls', width: 120, filter: 'agNumberColumnFilter', type: 'rightAligned' },
        { field: 'recorded_on', headerName: 'Recorded', width: 130 }
      ],
      pagination: true, paginationPageSize: 20, paginationPageSizeSelector: [20, 50, 100],
      getRowId: (p) => `${p.data.model}|${p.data.run_no}|${p.data.task_id}|${p.data.mode}`,
      initialState: { sort: { sortModel: [{ colId: 'task_id', sort: 'asc' }, { colId: 'run_no', sort: 'asc' }] } }
    });
    return () => grid.destroy();
  });
  $effect(() => { grid?.setGridOption('rowData', rows); });
  $effect(() => { grid?.setGridOption('quickFilterText', quick); });
  function pick(k) { preset = k; grid?.setFilterModel(PRESETS[k]); }
  const exportCsv = () => grid?.exportDataAsCsv({ fileName: 'real-deal-seal-evaluation-runs.csv' });
</script>

<div class="tools">
  <div class="chips" role="group" aria-label="Quick filters">
    {#each [['all', 'All runs'], ['off', 'Evidence off'], ['on', 'Evidence on'], ['withdrawn', 'Picked a withdrawn seal'], ['honest', 'Picked an honest small shop']] as [k, label]}
      <button class:on={preset === k} onclick={() => pick(k)}>{label}</button>{/each}
  </div>
  <input type="search" placeholder="Search requests and shops" bind:value={quick} aria-label="Search the runs" />
  <button class="btn black" onclick={exportCsv}>Export CSV</button>
</div>
<div bind:this={el} class="grid-host"></div>
<p class="source">{rows.length} recorded picks: every model, every full run, every request, both conditions. Built with AG Grid. Source: gold.fact_agent_run.</p>

<style>
  .tools { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 12px; }
  .chips { display: flex; gap: 4px; flex-wrap: wrap; flex: 1; }
  .chips button { border: 0; background: var(--tile); padding: 9px 12px; border-radius: 4px; font: inherit; font-size: 0.9rem; cursor: pointer; color: var(--ink); }
  .chips button.on { background: var(--ink); color: #fff; }
  input { font: inherit; padding: 10px 12px; border: 0; background: var(--tile); border-radius: 4px; min-width: 220px; }
  .tools .btn { padding: 10px 14px; font-size: 0.9rem; }
  .grid-host { height: 620px; width: 100%; }
</style>
