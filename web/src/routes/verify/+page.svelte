<script>
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import { api } from '$lib/api.js';
  import Arrow from '$lib/components/Arrow.svelte';

  let text = $state(''), result = $state(null), error = $state(''), busy = $state(false);
  const samples = [['lydia', 'Lydia Linen Co. (genuine)'], ['martha', "Martha's Kitchen (genuine, not sealed)"], ['palace', 'Linen Palace (the badge it displays)']];

  async function load(id) { text = JSON.stringify(await api(`/api/merchants/${id}/seal`), null, 2); await check(); }
  async function check() {
    busy = true; error = ''; result = null;
    try { result = await api('/api/verify', { credential: text }); } catch (e) { error = e.message; }
    busy = false;
  }
  function tamper() {
    try {
      const c = JSON.parse(text);
      const f = c.credentialSubject.facts.find((x) => x.metric === 'tracking_rate');
      f.value = 100; f.numerator = f.denominator;
      text = JSON.stringify(c, null, 2); check();
    } catch { error = 'Load a seal first, then change it.'; }
  }
  onMount(() => { const s = page.url.searchParams.get('shop'); if (s) load(s); });
  const words = { genuine: 'Genuine', edited: 'Edited after signing', forged: 'Forged', expired: 'Expired', withdrawn: 'Withdrawn', superseded: 'Replaced by a newer one', unreadable: 'Not a seal' };
</script>

<svelte:head><title>Check a seal | Real Deal Seal</title></svelte:head>

<section class="wrap section">
  <h1>Check a seal</h1>
  <p class="lede top">Every seal is digitally signed. Paste one in or load a sample, and we’ll check it against our public key, step by step. The check is done in code; no AI model is involved.</p>
  <div class="cols">
    <div>
      <div class="samples">{#each samples as [id, label]}<button class="btn ghost" onclick={() => load(id)}>{label}</button>{/each}</div>
      <textarea bind:value={text} spellcheck="false" placeholder="Paste a seal (credential JSON) here" aria-label="Seal JSON"></textarea>
      <div class="actions">
        <button class="btn" onclick={check} disabled={busy || !text.trim()}>Check this seal <Arrow /></button>
        <button class="btn black" onclick={tamper} disabled={!text.trim()}>Change one number, then check</button>
      </div>
    </div>
    <div class="out" aria-live="polite">
      {#if error}<p class="notice">{error}</p>{/if}
      {#if result}
        {#key result}
          <div class="verdict {result.result}">
            <span class="label">Result</span>
            <strong>{words[result.result]}</strong>
            <p>{result.summary}</p>
          </div>
          <ol>
            {#each result.steps as s, i}
              <li class:fail={!s.ok} style="animation-delay:{i * 0.12}s"><span class="mark">{s.ok ? '✓' : '✕'}</span><div><strong>{s.step}</strong><br /><span class="small">{s.detail}</span></div></li>
            {/each}
          </ol>
          <p class="small">Checked by {result.checked_by}.</p>
        {/key}
      {:else if !error}<p class="hint">The result and each step of the check appear here.</p>{/if}
    </div>
  </div>
</section>

<style>
  .top { margin: 24px 0 40px; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: clamp(24px, 4vw, 56px); align-items: start; }
  .samples { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
  .samples .btn { padding: 10px 14px; font-size: 0.9rem; }
  textarea { width: 100%; height: 420px; font: 0.8rem/1.5 ui-monospace, Menlo, monospace; padding: 16px; border: 0; border-radius: 6px; background: var(--ink); color: #e6e6e6; resize: vertical; }
  .actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }
  .verdict { padding: 26px; border-radius: 6px; background: var(--red); color: #fff; animation: pop 0.4s var(--ease); }
  .verdict.genuine { background: var(--ink); }
  .verdict .label { color: inherit; opacity: 0.75; }
  .verdict strong { display: block; font: 300 clamp(2.2rem, 4.4vw, 3.6rem)/1.05 var(--display); letter-spacing: -0.03em; margin: 4px 0 10px; }
  .verdict p { margin: 0; }
  @keyframes pop { from { transform: scale(0.96); opacity: 0; } }
  ol { list-style: none; padding: 0; margin: 20px 0; display: grid; gap: 2px; }
  li { display: flex; gap: 14px; background: var(--tile); padding: 14px 16px; animation: pop 0.35s var(--ease) backwards; }
  .mark { width: 26px; height: 26px; border-radius: 50%; background: var(--ink); color: #fff; display: grid; place-items: center; font-weight: 700; flex: none; font-size: 0.85rem; }
  li.fail .mark { background: var(--red); }
  .hint { background: var(--tile); padding: 40px; border-radius: 6px; color: var(--muted); }
  @media (max-width: 900px) { .cols { grid-template-columns: 1fr; } textarea { height: 260px; } }
</style>
