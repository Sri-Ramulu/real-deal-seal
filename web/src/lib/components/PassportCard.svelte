<script>
  import Standing from './Standing.svelte';
  import SealMark from './SealMark.svelte';
  let { shop, href = null, big = false } = $props();
  // Two fixed-width lines, the same layout on every passport (36 characters each, < as filler):
  //   RDS<<SHOP<NAME<<<<<<<<<<<<<<<<<<<<<
  //   STANDING<<C2<YYYYMMDD<NNNN<<<<<<<<<   standing (9), rule set, data date, completed orders
  const fill = (s, n) => (s + '<'.repeat(n)).slice(0, n);
  const CODE = { sealed: 'SEALED', verified: 'VERIFIED', reported: 'REPORTED', new: 'NEW', withdrawn: 'WITHDRAWN', no_record: 'NORECORD' };
  const mrz = $derived(fill(`RDS<<${shop.merchant_name.toUpperCase().replace(/[^A-Z0-9]+/g, '<')}`, 36));
  const mrz2 = $derived(fill([fill(CODE[shop.standing] ?? 'NORECORD', 9),
    `C${(shop.criteria_version ?? '').match(/\d+$/)?.[0] ?? '0'}`,
    (shop.data_as_of ?? '').replace(/-/g, '') || '00000000',
    String(shop.orders_completed ?? 0).padStart(4, '0')].join('<'), 36));
</script>

<svelte:element this={href ? 'a' : 'div'} {href} class="passport" class:big class:stamped={shop.standing === 'sealed'}>
  <div class="top">
    <span class="issuer">Merchant Passport <small>{shop.business_type_label ?? ''}</small></span>
    <SealMark size={big ? 40 : 30} tone={shop.standing === 'sealed' ? 'red' : 'black'} />
  </div>
  <div class="body">
    <div class="photo" aria-hidden="true">{shop.merchant_name[0]}</div>
    <dl>
      <div><dt>Shop</dt><dd class="name">{shop.merchant_name}</dd></div>
      <div><dt>Sells</dt><dd>{shop.sells ?? shop.category}</dd></div>
      <div><dt>{shop.business_type === 'physical' ? 'Ships from' : 'Based in'}</dt><dd>{shop.ships_from ?? shop.region}</dd></div>
      <div><dt>Record</dt><dd>{shop.standing === 'withdrawn' && !shop.has_record ? 'Withdrawn by the business' : !shop.has_record ? 'No record on file' : `${shop.orders_completed} ${shop.has_paypal_record ? 'PayPal sandbox orders' : 'self-reported orders'} over ${shop.history_days} days`}</dd></div>
    </dl>
  </div>
  <div class="standing"><Standing standing={shop.standing} headline={shop.headline} /></div>
  <p class="verdict">{shop.verdict}</p>
  <div class="mrz" aria-hidden="true">{mrz}<br />{mrz2}</div>
  {#if shop.standing === 'sealed'}<div class="stamp" aria-hidden="true">Sealed</div>{/if}
</svelte:element>

<style>
  .passport { position: relative; display: flex; flex-direction: column; background: #fff; border-radius: 10px; padding: 22px 22px 0; text-decoration: none; overflow: hidden;
    box-shadow: inset 0 0 0 1.5px var(--ink); transition: transform 0.3s var(--ease), box-shadow 0.3s var(--ease); }
  a.passport:hover { transform: translateY(-4px); box-shadow: inset 0 0 0 1.5px var(--ink), 8px 8px 0 var(--red); }
  .top { display: flex; justify-content: space-between; align-items: center; border-bottom: 1.5px solid var(--ink); padding-bottom: 12px; }
  .issuer { font: 600 0.95rem var(--display); letter-spacing: 0.01em; }
  .issuer small { font: 500 0.75rem var(--body); color: var(--muted); margin-left: 6px; }
  .body { display: grid; grid-template-columns: 84px 1fr; gap: 16px; padding: 16px 0 14px; }
  .photo { aspect-ratio: 4/5; background: var(--tile); border-radius: 4px; display: grid; place-items: center; font: 300 3rem var(--display); color: var(--ink);
    background-image: repeating-linear-gradient(135deg, transparent 0 7px, rgba(0, 0, 0, 0.045) 7px 8px); }
  dl { margin: 0; display: grid; gap: 7px; }
  dt { font-size: 0.72rem; color: var(--muted); }
  dd { margin: 0; font-size: 0.92rem; line-height: 1.25; }
  dd.name { font: 600 1.15rem var(--display); letter-spacing: -0.02em; }
  .verdict { font-size: 0.92rem; margin: 10px 0 16px; min-height: 2.8em; }
  .mrz { margin: auto -22px 0; padding: 10px 22px 12px; background: var(--tile); font: 500 0.72rem/1.5 ui-monospace, Menlo, monospace; letter-spacing: 0.12em; color: #777; white-space: nowrap; overflow: hidden; }
  .stamp { position: absolute; right: 18px; bottom: 54px; transform: rotate(-12deg); border: 3px solid var(--red); color: var(--red); border-radius: 6px; padding: 2px 12px;
    font: 700 1.05rem var(--display); letter-spacing: 0.04em; opacity: 0.9; animation: stamp 0.5s var(--ease) 0.5s backwards; }
  @keyframes stamp { from { transform: rotate(-12deg) scale(2.4); opacity: 0; } }
  .big { padding: 30px 30px 0; }
  .big .body { grid-template-columns: 120px 1fr; }
  .big dd.name { font-size: 1.6rem; }
  .big .mrz { margin: auto -30px 0; padding-inline: 30px; font-size: 0.82rem; }
</style>
