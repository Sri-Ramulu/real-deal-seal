<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api, session, setSession } from '$lib/api.js';
  import Arrow from '$lib/components/Arrow.svelte';

  let email = $state(''), password = $state(''), error = $state(''), demo = $state(null), busy = $state(false);
  onMount(async () => {
    const s = session();
    if (s?.merchant_id) { goto(`/studio/${s.merchant_id}`); return; }
    demo = await api('/api/auth/demo').catch(() => null);
  });
  async function signIn(e, p) {
    busy = true; error = '';
    try { const s = await api('/api/auth/login', { email: e ?? email, password: p ?? password }); setSession(s); goto(`/studio/${s.merchant_id}`); }
    catch (err) { error = err.message; }
    busy = false;
  }
  const names = { lydia: ['Lydia Linen Co.', 'Sealed. See what a full record looks like.'], martha: ["Martha's Kitchen", 'Four rules to fix. Try the coach.'], priscilla: ['Priscilla Canvas Works', 'Too new to judge. See how that is shown.'] };
</script>

<svelte:head><title>Merchant Studio | Real Deal Seal</title></svelte:head>

<section class="wrap section cols">
  <div>
    <h1>Merchant Studio</h1>
    <p class="lede">Each shop's private workspace: what's verified, what to fix next to earn the seal, and what shoppers and AI assistants see.</p>
    {#if demo}
      <h2>Open a demo shop</h2>
      <p class="small">These demo logins are public, and their studios hold PayPal sandbox data only.</p>
      <div class="demos">
        {#each demo.accounts as a}
          {@const id = a.split('@')[0]}
          <button onclick={() => signIn(a, demo.password)} disabled={busy}><strong>{names[id][0]}</strong><span>{names[id][1]}</span><Arrow size={12} /></button>
        {/each}
      </div>
    {/if}
  </div>
  <form class="card" onsubmit={(e) => { e.preventDefault(); signIn(); }}>
    <h3>Sign in</h3>
    <label class="field">Email <input class="input" type="email" bind:value={email} autocomplete="username" required /></label>
    <label class="field">Password <input class="input" type="password" bind:value={password} autocomplete="current-password" required /></label>
    {#if error}<p class="err">{error}</p>{/if}
    <button class="btn black" disabled={busy}>Sign in <Arrow /></button>
  </form>
</section>

<style>
  .cols { display: grid; grid-template-columns: 1.3fr 0.7fr; gap: clamp(28px, 6vw, 96px); align-items: start; }
  h1 { margin-bottom: 22px; } .lede { margin-bottom: 28px; }
  h2 { font-size: 1.8rem; margin: 64px 0 8px; }
  .demos { display: grid; gap: 2px; margin-top: 16px; }
  .demos button { display: grid; grid-template-columns: 220px 1fr auto; gap: 16px; align-items: center; text-align: left; padding: 18px 20px; border: 0; background: var(--tile); cursor: pointer; transition: 0.25s var(--ease); }
  .demos button:hover { background: var(--red); color: #fff; }
  form { display: grid; gap: 16px; } form .input { background: #fff; }
  @media (max-width: 900px) { .cols { grid-template-columns: 1fr; } .demos button { grid-template-columns: 1fr auto; } .demos span { display: none; } }
</style>
