<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import Arrow from '$lib/components/Arrow.svelte';
  let ns = $state(null);
  onMount(async () => { try { ns = (await api('/api/scorecard')).north_star; } catch { ns = null; } });
  const steps = [
    ['30 seconds', 'See the difference', '/#difference', 'Run it live',
      'One question, answered twice at the same moment. With listings only, the assistant picks a shop whose seal was withdrawn. With evidence, it picks an honest one and says why.'],
    ['45 seconds', 'Check a seal yourself', '/verify', 'Open the seal check',
      'Load Lydia’s seal: genuine. Press “Change one number, then check”: edited. Load Linen Palace: forged. Load Violet & Vine Home: withdrawn. Plain code decides, never a model.'],
    ['45 seconds', 'Open a shop’s studio', '/studio', 'Open Merchant Studio',
      'Pick Martha’s Kitchen. Her studio shows the four rules she misses and the exact orders behind each number. In Coach, add one tracking number and watch her count change.'],
    ['30 seconds', 'Start a PayPal checkout', '/shop', 'Open the shop',
      'Choose a Lydia Linen Co. product and press Buy with PayPal. PayPal’s sandbox opens. Only the buyer can approve, and the server confirms the capture with PayPal. Approving needs a sandbox buyer login; the video shows that step.'],
    ['30 seconds', 'Read the evidence', '/proof', 'Open the proof lab',
      'Fifty requests and eleven attacks, written before any run, on two models. Every run is listed, including the ones re-run after we fixed our own bug.']
  ];
</script>

<svelte:head><title>Judges: start here | Real Deal Seal</title></svelte:head>

<section class="wrap section">
  <span class="label">PayPal AI Hackathon 2026</span>
  <h1>Three minutes, five clicks</h1>
  <p class="lede top">Real Deal Seal turns a small shop’s PayPal payment history into a signed record that AI shopping assistants can check before they recommend it.{#if ns}{' '}In our test, shops with a withdrawn seal went from {ns.baseline_withdrawn} of 50 AI picks to {ns.withdrawn}, and honest small shops from {ns.baseline_numerator} to {ns.numerator}.{/if}</p>

  <ol class="steps">
    {#each steps as [time, title, href, cta, text], i}
      <li>
        <span class="num n">{i + 1}</span>
        <div><h2>{title}</h2><p>{text}</p></div>
        <div class="go"><span class="small">{time}</span><a class="btn" {href}>{cta} <Arrow size={12} /></a></div>
      </li>
    {/each}
  </ol>

  <div class="two">
    <div class="card">
      <h3>What is real</h3>
      <ul>
        <li>PayPal sandbox orders, captures and refunds for Lydia, Martha and Priscilla, read back from PayPal.</li>
        <li>PayPal sandbox checkout: the buyer approves, the server verifies the capture.</li>
        <li>Signed seals, checked with a published key.</li>
        <li>The assistant’s answers: live calls to Claude or Gemini, nothing scripted.</li>
        <li>The experiment: every run recorded on this site and published.</li>
      </ul>
    </div>
    <div class="card">
      <h3>What is simulated, and labelled</h3>
      <ul>
        <li>All ten shops are fictional.</li>
        <li>Order dates, shipping speed and dispute outcomes (the sandbox can’t backdate or dispute on its own).</li>
        <li>The records of the four shops that joined later, including the two whose seals were withdrawn.</li>
        <li>Tracking numbers are reported by the shop.</li>
      </ul>
    </div>
  </div>
  <p class="more">Want more? <a href="/business">Why PayPal wins</a> · <a href="/story">The story</a> · <a href="/scorecard">Scorecard</a> · <a href="/developers">Developers: MCP tools and data products</a> · <a href="https://github.com/Sri-Ramulu/real-deal-seal">Source on GitHub</a></p>
</section>

<style>
  h1 { margin: 10px 0 0; } .top { margin: 24px 0 40px; }
  .steps { list-style: none; padding: 0; margin: 0 0 40px; display: grid; gap: 2px; }
  .steps li { background: var(--tile); padding: clamp(18px, 2.4vw, 28px); display: grid; grid-template-columns: auto 1fr auto; gap: clamp(14px, 2.4vw, 32px); align-items: center; }
  .steps li:first-child { background: var(--ink); color: #e9e9e9; } .steps li:first-child h2 { color: #fff; } .steps li:first-child .small { color: #bbb; }
  .n { width: 44px; height: 44px; border-radius: 50%; background: var(--red); color: #fff; display: grid; place-items: center; font-size: 1.2rem; font-weight: 600; }
  .steps h2 { font-size: clamp(1.3rem, 2.2vw, 1.8rem); margin: 0 0 6px; } .steps p { margin: 0; max-width: 70ch; }
  .go { display: grid; gap: 8px; justify-items: end; } .go .btn { white-space: nowrap; }
  .two { display: grid; grid-template-columns: 1fr 1fr; gap: 2px; }
  .two ul { margin: 12px 0 0; padding-left: 18px; display: grid; gap: 8px; }
  .more { margin-top: 28px; }
  @media (max-width: 760px) { .steps li { grid-template-columns: auto 1fr; } .go { grid-column: 1 / -1; justify-items: start; } .two { grid-template-columns: 1fr; } }
</style>
