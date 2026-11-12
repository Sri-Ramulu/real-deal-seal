<script>
  // A parcel standing on its base line. tone: red | black | line
  let { x = 0, y = 0, w = 80, h = 56, tone = 'red', mark = false } = $props();
  const fill = $derived(tone === 'red' ? '#d9201f' : tone === 'black' ? '#0a0a0a' : '#dedede');
  const ink = $derived(tone === 'line' ? '#0a0a0a' : '#fff');
</script>

<g transform="translate({x} {y - h})">
  <rect width={w} height={h} fill={fill} stroke="#0a0a0a" stroke-width={tone === 'line' ? 2.5 : 0} />
  <rect x={w / 2 - 5} width="10" height={h} fill={ink} opacity={tone === 'line' ? 1 : 0.9} />
  <path d="M0 {h * 0.38}h{w}" stroke={ink} stroke-width="2" opacity="0.5" />
  {#if mark}<circle cx={w - 16} cy={h - 14} r="7" fill="none" stroke={ink} stroke-width="2" /><path d="M{w - 19.5} {h - 14}l2.6 2.6 4.4-5" fill="none" stroke={ink} stroke-width="1.8" />{/if}
</g>
