<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import Arrow from '$lib/components/Arrow.svelte';
  import Icon from '$lib/components/Icon.svelte';
  let ns = $state(null);
  onMount(async () => { try { ns = (await api('/api/scorecard')).north_star; } catch { ns = null; } });
  const icons = ['compare', 'seal', 'shop', 'cart', 'chart'];
  const steps = [
    ['30 seconds', 'See the difference', '/#difference', 'Run it live',
      'One question, answered twice at the same moment. With listings only, the assistant picks a shop whose seal was withdrawn. With evidence, it picks an honest one and says why.'],
    ['45 seconds', 'Check a seal yourself', '/verify', 'Open the seal check',
      'Load Lydia’s seal: genuine. Press “Change one number, then check”: edited. Load Linen Palace: forged. Load Violet & Vine Home: withdrawn. Plain code decides, never a model.'],
    ['45 seconds', 'Open a shop’s studio', '/studio', 'Open Merchant Studio',
      'Pick Martha’s Kitchen. Her studio shows the four rules she misses and the exact orders behind each number. In Coach, add one tracking number and watch her count change.'],
    ['30 seconds', 'Start a PayPal checkout', '/shop', 'Open the shop',
      'Choose a product from Lydia Linen Co. (or any shop with a Buy with PayPal button) and press it. PayPal’s sandbox opens. Only the buyer can approve, and the server confirms the capture with PayPal. To approve, sign in with the PayPal sandbox buyer login in our Devpost testing instructions. The video shows this step too.'],
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
        <div><h2><span class="ico"><Icon name={icons[i]} size={26} /></span>{title}</h2><p>{text}</p></div>
        <div class="go"><span class="small">{time}</span><a class="btn" {href}>{cta} <Arrow size={12} /></a></div>
      </li>
    {/each}
  </ol>

  <h2 class="how">Who does what</h2>
  <div class="roles">
    <div><Icon name="agent" size={30} /><h3>The agent leads</h3><p>It searches ten shops, reads each passport, checks the seal, picks a shop and opens the PayPal checkout. Eight tools, also served over MCP for any other agent.</p></div>
    <div><Icon name="hand" size={30} /><h3>The human approves</h3><p>Only the buyer can approve a payment, on PayPal’s own page. Only the shop owner can share a statement of the record, and can take the link back.</p></div>
    <div><Icon name="seal" size={30} /><h3>Plain code proves</h3><p>No model decides who earns a seal or whether one is genuine. Published rules count PayPal records, and a signature check gives the verdict.</p></div>
  </div>

  <div class="two">
    <div class="card">
      <h3><span class="ico ok"><Icon name="real" size={20} /></span>What is real</h3>
      <ul>
        <li>PayPal sandbox orders, captures and refunds for Lydia, Martha and Priscilla, read back from PayPal.</li>
        <li>PayPal sandbox checkout at five shops (Lydia, Martha, Priscilla, Copper Kettle and Sage &amp; Stone), each with its own sandbox account: the buyer approves, the server verifies the capture.</li>
        <li>Signed seals, checked with a published key.</li>
        <li>The assistant’s answers: live calls to Claude Sonnet or Claude Haiku, nothing scripted.</li>
        <li>The experiment: every run recorded on this site and published.</li>
      </ul>
    </div>
    <div class="card">
      <h3><span class="ico"><Icon name="sim" size={20} /></span>What is simulated, and labelled</h3>
      <ul>
        <li>All ten shops are fictional.</li>
        <li>Order dates, shipping speed and dispute outcomes (the sandbox can’t backdate or dispute on its own).</li>
        <li>The order history of the four shops that joined later (Copper Kettle, Sage &amp; Stone, Violet &amp; Vine, Juniper &amp; Oak). Their PayPal sandbox accounts are real; their past orders are not.</li>
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
  .ico { display: inline-flex; vertical-align: -4px; margin-right: 10px; color: var(--red); } .ico.ok { color: var(--ok); }
  .steps li:first-child .ico { color: #fff; }
  .how { font-size: clamp(1.9rem, 3.6vw, 3rem); margin: 0 0 20px; }
  .roles { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px; margin-bottom: 40px; }
  .roles div { background: var(--ink); color: #d6d6d6; padding: clamp(20px, 2.6vw, 32px); } .roles :global(svg) { color: var(--red); }
  .roles h3 { color: #fff; margin: 14px 0 8px; } .roles p { margin: 0; }
  @media (max-width: 760px) { .roles { grid-template-columns: 1fr; } }
  @media (max-width: 760px) { .steps li { grid-template-columns: auto 1fr; } .go { grid-column: 1 / -1; justify-items: start; } .two { grid-template-columns: 1fr; } }
</style>
