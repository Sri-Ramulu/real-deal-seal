# Devpost submission text

**Name:** Real Deal Seal
**Tagline:** Proof beats brand: signed proof from a shop's own PayPal record that any AI shopping assistant can check.

## Inspiration

Ask an AI assistant for a purple table runner and it will probably send you to a big chain. A September 2026 study for
Lightspeed Commerce by Vaer AI, covering about 460,000 AI shopping answers, found that without live web search,
assistants picked a national chain over a smaller retailer 90 to 94% of the time. Small shops aren't worse. The
assistant just can't tell which ones deliver. A shop's PayPal record can.

## What it does

Real Deal Seal reads a shop's orders back from PayPal and turns them into facts anyone can count, like "46 of 48 recent
shipments had tracking." Each fact says where it came from: PayPal's records, the shop itself, or simulated for the
demo. The facts are judged against published rules and signed as a Merchant Passport, so changing a single number makes
the seal fail.

An AI shopping assistant (Claude Sonnet or Claude Haiku) reads the passport before it recommends a
shop. An Evidence switch turns that off, so you can see what the same assistant picks from listings alone. The
assistant can open a PayPal checkout, but only the shopper can approve it, and the server confirms the capture with
PayPal before anything counts as paid.

Shop owners get a private studio that shows the exact orders behind every number and what to fix to earn the seal. If a
sealed shop turns out to be a scam, Real Deal Seal can withdraw its seal: the old badge fails the check, the assistant
warns shoppers, and checkout is turned off for that shop.

## How we built it

- **PayPal:** Orders v2 in the sandbox (create, approve, capture, track, refund) across seven sandbox merchant accounts:
  three with 175 recorded orders, two more that take live sandbox payments, and two whose checkout is switched off because their seal is withdrawn, plus webhooks verified with PayPal before they're processed.
- **AI:** one tool-using assistant with eight tools, on Anthropic Claude (Sonnet or Haiku). Code, not the model, decides
  prices, seal validity and payment status. The same tools are available to any agent over MCP.
- **Data:** a data mesh of four domains on DuckDB, each with bronze, silver and gold layers, column metadata, an ODCS
  data contract and governed metrics. Gold is a star schema. Four quality gates and 379 contract rules run on every build.
- **App:** Python and FastAPI, SvelteKit, Docker on Render. AG Grid powers two explorers: every order behind a shop's
  facts (in the Merchant Studio) and every recorded evaluation run (public, on the proof page).

## Challenges we ran into

Keeping simulated, shop-reported and PayPal-confirmed facts labeled all the way from the data to the AI's answer, so
nothing quietly gets upgraded. Making sure the Evidence Off baseline carries no trust information at all, so the
comparison is fair. Making sure a shop that loses its seal is never shown as merely "unknown."

## Accomplishments we're proud of

- On the live site, we ran the same 50 shopping requests with Evidence off and then on, three full times, with two
  models (12 Nov 2026). Convincing scam shops whose seals were withdrawn won 33 or 34 of 50 picks without evidence
  and 0 with it, in every run and for both models. Honest small shops went from 9-11 to 35-38 (Claude Sonnet) and
  from 7-8 to 37-43 (Claude Haiku). The catalog is fictional and the scam shops' records are simulated.
- Across 66 attack runs (forged and edited seals, hidden instructions, fake badges, social pressure), 65 passed. The
  one failure is a keyword-rule false alarm that we left standing and explained. The runs also caught two of our own
  bugs, which we fixed and disclosed.
- All 600 recorded picks are public in an AG Grid explorer on the proof page: filter, sort, search or export them.
- A side-by-side demo on the home page asks one question both ways, live, so anyone can see the difference in 20
  seconds.
- 172 automated tests and 9 browser tests, with every claim and attack case mapped to the tests that check it (`docs/evidence/`).

## What we learned

A trust signal only helps an AI shopper if it's small, countable and checkable. "96% trusted" means nothing to a model;
"46 of 48 shipments tracked, according to PayPal and the shop" does.

## What's next

A "Connect PayPal" button so any shop can join with its own account, carrier-confirmed delivery, dispute outcomes
read from PayPal, requests written by outside shoppers, more models, and a pilot with real small shops.

## Limits

This is a controlled test on one fictional catalog that we wrote, including the scam shops: AI recommendations, not
sales. The requests were written before any run, but by us. Order dates, shipping speed and past
dispute outcomes are simulated in the sandbox, and labeled that way. Real Deal Seal is not a PayPal product; PayPal
supplies the sandbox records and doesn't sign or endorse the seal.

## Updates during the submission period

> Write this yourself: when the project started and what was built when, during 1 Oct to 12 Nov 2026.

## Testing instructions (paste into the Devpost "testing instructions" field)

Live site: https://real-deal-seal.onrender.com (free to use, no sign-up, kept online through 15 December 2026).
Start at https://real-deal-seal.onrender.com/judges for a three-minute, five-click tour.

1. **See the difference.** On the home page, press "Run it live". One question is answered twice: with listings only,
   and with evidence.
2. **Check a seal.** Open "Check a seal". Load Lydia's seal (genuine), press "Change one number, then check" (edited),
   then load Linen Palace (forged) and Violet & Vine Home (withdrawn).
3. **Open a shop's studio.** Open "Studio" and pick Martha's Kitchen. The demo password is filled in for you
   (`demo-owner`; it is public on purpose and guards sandbox data only).
4. **Pay with PayPal (sandbox).** Open "Shop", choose a Lydia Linen Co. product and press "Buy with PayPal". On PayPal's
   sandbox page, sign in as the test buyer:
   - Email: `[PASTE THE SANDBOX BUYER EMAIL HERE]`
   - Password: `[PASTE THE SANDBOX BUYER PASSWORD HERE]`
   This is a PayPal sandbox personal account with test money. No real payment is possible.
5. **Read the evidence.** Open "Proof" for every recorded run, and "Developers" for the MCP tools and data platform.

To run it yourself: `make setup && make test && make api` (see the README). Source: https://github.com/Sri-Ramulu/real-deal-seal (MIT license).
