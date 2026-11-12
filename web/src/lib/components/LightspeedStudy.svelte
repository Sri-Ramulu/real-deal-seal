<script>
  // The outside evidence for the problem. Figures are the study's own; the link goes to the publisher.
  // Range bars: the dark band is the reported range, the light bar runs from zero to its lower end.
  let { compact = false } = $props();
  const rows = [
    { label: 'Without live web search', lo: 90, hi: 94, text: '90 to 94%', note: 'of head-to-head picks between a national chain and a smaller retailer went to the chain', hot: true },
    { label: 'With live web search', lo: 46, hi: 58, text: '46 to 58%', note: 'of responses were still national chains', hot: false }
  ];
  const url = 'https://www.lightspeedhq.com/news/ai-favors-big-retailers-over-local-stores-9-out-of-10-times-new-study-finds/';
</script>

<div class="study" class:compact>
  <div class="copy">
    <h2>AI assistants pick the big retailer about nine times in ten</h2>
    <p class="lede">That is the finding of a 2026 study for Lightspeed Commerce, run by the research consultancy Vaer AI. Real Deal Seal is built to fix that.</p>
    {#if !compact}
      <dl>
        <div><dt>Scale</dt><dd>About 20,000 shopping prompts and roughly 460,000 AI answers, analyzed June to August 2026.</dd></div>
        <div><dt>Assistants tested</dt><dd>ChatGPT, Google AI Mode, Google AI Overviews and Gemini.</dd></div>
        <div><dt>Why it happens</dt><dd>With no live search, an assistant answers from what it already knows, and it knows big brands best.</dd></div>
      </dl>
    {/if}
  </div>
  <figure>
    {#each rows as r}
      <div class="row" title="{r.label}: {r.text} {r.note}">
        <span class="lab">{r.label}</span>
        <span class="track"><i class="base" style="width:{r.lo}%"></i><i class="band" class:hot={r.hot} style="left:{r.lo}%;width:{r.hi - r.lo}%"></i></span>
        <span class="val num" class:hot={r.hot}>{r.text}</span>
        <span class="small note">{r.note}</span>
      </div>
    {/each}
    <div class="axis small"><span>0%</span><span>50%</span><span>100%</span></div>
    <figcaption class="source">Source: Lightspeed Commerce and Vaer AI, <a href={url} rel="noopener">“AI favors big retailers over local stores 9 out of 10 times”</a>, 29 September 2026.
      This is their study of general-purpose assistants. It is not Real Deal Seal's own test, which used a different set-up and is reported on the <a href="/proof">proof page</a>.</figcaption>
  </figure>
</div>

<style>
  .study { display: grid; grid-template-columns: 1fr 1fr; gap: clamp(28px, 6vw, 96px); align-items: center; }
  h2 { margin-bottom: 20px; } dl { display: grid; gap: 14px; margin: 26px 0 0; }
  dt { font-size: 0.82rem; font-weight: 700; color: var(--muted); } dd { margin: 2px 0 0; max-width: 52ch; }
  figure { margin: 0; display: grid; gap: 26px; }
  .row { display: grid; grid-template-columns: 1fr auto; gap: 6px 16px; align-items: end; }
  .lab { font-weight: 600; } .val { font-size: 1.9rem; font-weight: 400; color: var(--muted); line-height: 1; } .val.hot { color: var(--ink); font-size: 2.6rem; }
  .track { grid-column: 1 / -1; position: relative; height: 22px; background: var(--tile); }
  .stone .track, :global(.stone) .track { background: #fff; }
  .base { position: absolute; inset: 0 auto 0 0; background: #cfcfcf; } .band { position: absolute; top: 0; bottom: 0; background: var(--chart-context); border-radius: 0 4px 4px 0; } .band.hot { background: var(--red); }
  .note { grid-column: 1 / -1; max-width: 48ch; }
  .axis { display: flex; justify-content: space-between; margin-top: -18px; }
  @media (max-width: 900px) { .study { grid-template-columns: 1fr; } }
</style>
