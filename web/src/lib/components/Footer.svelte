<script>
  import Scene from './Scene.svelte';
  import SealMark from './SealMark.svelte';
</script>

<footer class="stone">
  <div class="band"></div>
  <div class="wrap inner">
    <Scene>
      <div class="lockup"><SealMark size={76} /><strong>Real Deal Seal</strong><span>Proof beats brand.</span></div>
    </Scene>
    <div class="cols">
      <div>
        <h3>What this is</h3>
        <p class="small">A PayPal AI Hackathon 2026 project. It is not a PayPal product, and PayPal does not issue or endorse the seal. All orders are PayPal sandbox test orders.</p>
      </div>
      <nav aria-label="Footer">
        <a href="/shop">Shop</a>
        <a href="/assistant">Ask the assistant</a>
        <a href="/shops">Passports</a>
        <a href="/studio">Merchant Studio</a>
        <a href="/scorecard">Scorecard</a>
        <a href="/story">The story</a>
        <a href="/business">Why PayPal wins</a>
        <a href="/judges">Judges: start here</a>
      </nav>
      <div>
        <h3>For builders</h3>
        <p class="small">Eight agent tools over MCP, a REST API and four data products with contracts.</p>
        <a class="big" href="/developers">Open the developer pages</a>
      </div>
      <div>
        <h3>Check before you trust</h3>
        <p class="small">Any seal can be checked by anyone with the published key.</p>
        <a class="big" href="/verify">Check a seal</a>
      </div>
    </div>
    <p class="legal small">MIT license. The shopping assistant runs on Anthropic Claude (Sonnet or Haiku). Every shop on this site is fictional: Lydia Linen Co., Martha's Kitchen, Priscilla Canvas Works, Babel Home, Hearthline Home, Linen Palace, Violet &amp; Vine Home, Juniper &amp; Oak Goods, Copper Kettle Supply and Sage &amp; Stone Studio. The last four have real PayPal sandbox accounts and a simulated order history.</p>
  </div>
</footer>

<style>
  .band { height: 44px; background: linear-gradient(90deg, #7c2426, var(--oxblood) 40%, #5e2420); }
  .inner { padding: 64px 0 36px; }
  .lockup { display: grid; justify-items: center; gap: 6px; }
  .lockup strong { font: 600 clamp(1.3rem, 2.4vw, 2rem) var(--display); letter-spacing: -0.03em; color: var(--red); margin-top: 8px; }
  .lockup span { color: var(--oxblood); font-weight: 600; }
  .cols { display: grid; grid-template-columns: 1.3fr 0.8fr 1fr 1fr; gap: 40px; margin-top: 64px; }
  h3 { font: 700 1.05rem var(--body); letter-spacing: 0; margin-bottom: 8px; }
  nav { display: grid; gap: 10px; align-content: start; }
  nav a, .big { font-weight: 700; text-decoration: none; }
  nav a:hover, .big:hover { color: var(--red); }
  .legal { margin: 56px auto 0; text-align: center; max-width: none; }
  @media (max-width: 900px) { .cols { grid-template-columns: 1fr 1fr; } }
  @media (max-width: 560px) { .cols { grid-template-columns: 1fr; } .inner { padding-top: 48px; } }
</style>
