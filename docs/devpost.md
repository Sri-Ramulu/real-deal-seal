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

An AI shopping assistant (Google Gemini by default, or Claude Sonnet or Haiku) reads the passport before it recommends a
shop. An Evidence switch turns that off, so you can see what the same assistant picks from listings alone. The
assistant can open a PayPal checkout, but only the shopper can approve it, and the server confirms the capture with
PayPal before anything counts as paid.

Shop owners get a private studio that shows the exact orders behind every number and what to fix to earn the seal. If a
sealed shop turns out to be a scam, Real Deal Seal can withdraw its seal: the old badge fails the check, the assistant
warns shoppers, and checkout is turned off for that shop.

## How we built it

- **PayPal:** Orders v2 in the sandbox (create, approve, capture, track, refund) across three sandbox merchant accounts
  with 175 orders, plus webhooks verified with PayPal before they're processed.
- **AI:** one tool-using assistant with eight tools, on Google Gemini or Anthropic Claude. Code, not the model, decides
  prices, seal validity and payment status. The same tools are available to any agent over MCP.
- **Data:** a data mesh of four domains on DuckDB, each with bronze, silver and gold layers, column metadata, an ODCS
  data contract and governed metrics. Gold is a star schema. Four quality gates and 322 contract rules run on every build.
- **App:** Python and FastAPI, SvelteKit, AG Grid for the evidence explorer, Docker on Render.

## Challenges we ran into

Keeping simulated, shop-reported and PayPal-confirmed facts labeled all the way from the data to the AI's answer, so
nothing quietly gets upgraded. Making sure the Evidence Off baseline carries no trust information at all, so the
comparison is fair. Making sure a shop that loses its seal is never shown as merely "unknown."

## Accomplishments we're proud of

- In a controlled test with a fictional chain, small shops won 37 of 50 AI shopping recommendations with evidence, up
  from 25 without it (Claude Sonnet, same 50 requests, one run each, recorded 10 Nov 2026). The chain still won 13,
  mostly on price.
- In 200 recorded runs, the assistant never picked the shop with the forged badge.
- 147 automated tests, with every claim and attack case mapped to the tests that check it (`docs/evidence/`).

## What we learned

A trust signal only helps an AI shopper if it's small, countable and checkable. "96% trusted" means nothing to a model;
"46 of 48 shipments tracked, according to PayPal and the shop" does.

## What's next

A "Connect PayPal" button so any shop can join with its own account, carrier-confirmed delivery, repeated evaluation
runs across more models, and a pilot with real small shops.

## Limits

This is a controlled test on one fictional catalog: AI recommendations, not sales. Order dates, shipping speed and past
dispute outcomes are simulated in the sandbox, and labeled that way. Real Deal Seal is not a PayPal product; PayPal
supplies the sandbox records and doesn't sign or endorse the seal.

## Updates during the submission period

> Write this yourself: when the project started and what was built when, during 1 Oct to 12 Nov 2026.
