<script>
  let { standing, headline } = $props();
</script>

<span class="chip {standing}">
  <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
    {#if standing === 'sealed'}<path d="M2 7.5l3.2 3L12 3.5" fill="none" stroke="currentColor" stroke-width="2.2" />
    {:else if standing === 'verified'}<path d="M7 2v6M7 10.5v1.5" stroke="currentColor" stroke-width="2.2" />
    {:else if standing === 'reported'}<path d="M3 3h8v8H3z" fill="none" stroke="currentColor" stroke-width="1.8" /><path d="M5 7h4" stroke="currentColor" stroke-width="1.8" />
    {:else if standing === 'withdrawn'}<path d="M3.5 3.5l7 7M10.5 3.5l-7 7" stroke="currentColor" stroke-width="2.2" />
    {:else if standing === 'new'}<circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-dasharray="2.4 2" />
    {:else}<path d="M3 7h8" stroke="currentColor" stroke-width="2" />{/if}
  </svg>
  {headline}
</span>
