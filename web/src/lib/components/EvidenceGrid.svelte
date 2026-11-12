<script>
  import { onMount } from 'svelte';
  import { AllCommunityModule, ModuleRegistry, createGrid, themeQuartz } from 'ag-grid-community';

  // AG Grid evidence explorer: every order behind a fact. `filter` narrows to the orders a metric counted.
  let { rows, filter = null } = $props();
  let el, grid;
  const yes = (p) => (p.value === true ? 'Yes' : p.value === false ? 'No' : '');
  const money = (p) => (p.value == null ? '' : '$' + Number(p.value).toFixed(2));
  const FILTERS = {
    tracking_rate: (r) => r.in_recent_window && r.is_fulfilled,
    fast_ship_rate: (r) => r.in_recent_window && r.is_fulfilled,
    refund_rate: (r) => r.in_recent_window,
    disputes_lost_rate: (r) => r.in_recent_window,
    disputes_total: (r) => r.in_recent_window && r.has_dispute,
    repeat_buyer_rate: (r) => r.in_recent_window,
    missing_tracking: (r) => r.in_recent_window && r.is_fulfilled && !r.has_tracking,
    slow: (r) => r.in_recent_window && r.is_fulfilled && !r.fulfilled_within_2_days,
    refunded: (r) => r.in_recent_window && r.is_refunded,
    lost: (r) => r.in_recent_window && r.dispute_lost,
    completion_rate: (r) => r.in_recent_window,
    cancellation_rate: (r) => r.in_recent_window,
    delivery_rate: (r) => r.in_recent_window,
    not_fulfilled: (r) => r.in_recent_window && !r.is_fulfilled,
    cancelled: (r) => r.in_recent_window && r.cancelled_by_business,
    confirmed_payment_share: (r) => r.in_recent_window
  };
  const shown = $derived(filter && FILTERS[filter] ? rows.filter(FILTERS[filter]) : rows);

  onMount(() => {
    ModuleRegistry.registerModules([AllCommunityModule]);
    grid = createGrid(el, {
      theme: themeQuartz.withParams({ accentColor: '#d9201f', fontFamily: 'inherit', headerFontWeight: 600, borderRadius: 4, wrapperBorderRadius: 6, headerBackgroundColor: '#f2f2f2' }),
      rowData: shown,
      defaultColDef: { sortable: true, filter: true, resizable: true, floatingFilter: true, minWidth: 110 },
      columnDefs: [
        { field: 'order_no', headerName: 'No.', width: 90, minWidth: 80, filter: 'agNumberColumnFilter', pinned: 'left' },
        { field: 'order_date', headerName: 'Order date', filter: 'agDateColumnFilter' },
        { field: 'order_id', headerName: 'Order ID', minWidth: 190 },
        { field: 'amount_usd', headerName: 'Captured', valueFormatter: money, filter: 'agNumberColumnFilter', type: 'rightAligned' },
        { field: 'refunded_usd', headerName: 'Refunded', valueFormatter: money, filter: 'agNumberColumnFilter', type: 'rightAligned',
          cellStyle: (p) => (p.value > 0 ? { color: '#d9201f', fontWeight: 600 } : null) },
        { field: 'capture_status', headerName: 'Capture' },
        { field: 'fulfil_days', headerName: 'Days to fulfil', filter: 'agNumberColumnFilter', type: 'rightAligned',
          cellStyle: (p) => (p.value > 2 ? { color: '#d9201f', fontWeight: 600 } : null) },
        { field: 'has_tracking', headerName: 'Tracking', valueFormatter: yes, cellStyle: (p) => (p.data.is_fulfilled && !p.value ? { color: '#d9201f', fontWeight: 600 } : null) },
        { field: 'has_dispute', headerName: 'Dispute', valueFormatter: yes },
        { field: 'dispute_lost', headerName: 'Lost', valueFormatter: yes, cellStyle: (p) => (p.value ? { color: '#d9201f', fontWeight: 600 } : null) },
        { field: 'is_returning_buyer', headerName: 'Returning buyer', valueFormatter: yes },
        { field: 'in_recent_window', headerName: 'In last 50', valueFormatter: yes },
        { field: 'history_is_simulated', headerName: 'Date simulated', valueFormatter: yes },
        { field: 'payment_evidence_class', headerName: 'Payment evidence', minWidth: 190, valueFormatter: (p) => ({ paypal_sandbox_confirmed: 'PayPal sandbox record', merchant_reported: 'Reported by the business' })[p.value] ?? p.value },
        { field: 'cancelled_by_business', headerName: 'Cancelled by business', valueFormatter: yes, cellStyle: (p) => (p.value ? { color: '#d9201f', fontWeight: 600 } : null) },
        { field: 'capture_id', headerName: 'PayPal capture ID', minWidth: 190 }
      ],
      pagination: true, paginationPageSize: 20, paginationPageSizeSelector: [20, 50, 100],
      getRowId: (p) => p.data.order_id
    });
    return () => grid.destroy();
  });
  $effect(() => { grid?.setGridOption('rowData', shown); });
  export function exportCsv() { grid?.exportDataAsCsv({ fileName: 'evidence.csv' }); }
</script>

<p class="small count"><strong>{shown.length}</strong> of {rows.length} orders shown{filter ? ' (the orders this fact counted)' : ''}. Sort, filter or export any column.</p>
<div bind:this={el} class="grid-host"></div>

<style>
  .grid-host { height: 560px; width: 100%; }
  .count { margin-bottom: 10px; }
  .count strong { color: var(--ink); }
</style>
