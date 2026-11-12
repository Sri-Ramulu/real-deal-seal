<script>
  // Small line icons, drawn for this site. 24 x 24, stroke follows the text colour.
  let { name, size = 22 } = $props();
  const paths = {
    compare: 'M4 5h7v14H4zM13 5h7v14h-7zM6.5 9h2M6.5 12h2M15.5 9h2M15.5 12l1 1 2-2.5',
    seal: 'M12 3l2.2 1.6 2.7-.2 1 2.5 2.3 1.4-.7 2.6.7 2.6-2.3 1.4-1 2.5-2.7-.2L12 21l-2.2-1.6-2.7.2-1-2.5-2.3-1.4.7-2.6-.7-2.6 2.3-1.4 1-2.5 2.7.2zM8.8 12.2l2.2 2.2 4.2-4.6',
    shop: 'M4 9l1.5-5h13L20 9M4 9v11h16V9M4 9c0 1.7 1.2 3 2.7 3S9.3 10.700 9.300 9c0 1.700 1.200 3 2.700 3s2.700-1.300 2.700-3c0 1.700 1.200 3 2.700 3S20 10.700 20 9M9.500 20v-5h5v5',
    cart: 'M3 4h2.500l2.200 10.500h10.300l2-7.500H6.500M9 19.500a1 1 0 1 0 .01 0M17 19.500a1 1 0 1 0 .01 0',
    chart: 'M4 20V4M4 20h16M8 16v-4M12 16V8M16 16v-6M20 16V6',
    agent: 'M12 3v3M6 6h12v9H6zM9.500 10.500h.01M14.500 10.500h.01M9 18l-2 3M15 18l2 3M3 10v3M21 10v3',
    hand: 'M8 12V5.500a1.500 1.500 0 0 1 3 0V11M11 10.500V4.500a1.500 1.500 0 0 1 3 0V11M14 11V6.500a1.500 1.500 0 0 1 3 0V14c0 4-2.500 7-6 7-2.500 0-4-1.200-5.500-3.500L3 13.500a1.500 1.500 0 0 1 2.500-1.600L8 14.500',
    code: 'M8 7l-5 5 5 5M16 7l5 5-5 5M13.500 4l-3 16',
    real: 'M4 12.500l5 5L20 6.500',
    sim: 'M12 3a9 9 0 1 0 .01 0M12 8v5M12 16.500v.01'
  };
</script>

<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>
