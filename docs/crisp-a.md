# The project, phase by phase (PRISM CRISP-A)

How the seven CRISP-A phases map to what is in this repository, and which role would own each part
(data engineer, analytics engineer, data analyst, data scientist). Role duties follow the three Apple supply-chain
job descriptions supplied (analyst, data scientist, analytics engineer); no data engineer description was supplied,
so that column follows the reference data-platform repo instead.

## 01 Business problem framing

- **Problem:** AI shopping assistants favour recognised brands; a reliable small shop has no way to show its record.
- **Stakeholders, in priority order:** PayPal, small merchants, shoppers, AI agent builders.
- **Decision the product supports:** which shop an assistant recommends, and what a merchant fixes next.
- **Out of scope:** lending decisions, credit scores, a marketplace, PayPal endorsement.
- **Success:** the North Star below, with guardrails that stop it being gamed.

## 02 Analytics problem framing

| Business question | Analytics form | Metric |
|---|---|---|
| Does evidence change who gets picked? | paired comparison, same model, same tasks | small-shop share of 50 decisions (North Star) |
| Is it informing or forcing? | paired switches both ways; a price-only task | chain-to-small vs small-to-chain; `cheapest-wins` passes |
| Is it safe? | pre-registered attacks with written pass rules | attacks resisted; forged-badge picks = 0 |
| Is each number true? | reconciliation and contracts | 175 of 175 rules; SQL equals v1 Python |

**Balanced scorecard** (`/scorecard`, `api/rds/scorecard.py`): Value for PayPal, Merchants and shoppers, Evidence quality,
Safety and learning. Targets are demo targets set by the project.

## 03 Data (data engineer, analytics engineer)

- Sources: PayPal sandbox Orders v2 read-back per shop, catalog, merchant directory, recorded eval runs, cached Channel3 prices, rules reference.
- Landed unchanged, hashed, loaded as text (bronze), made canonical across source systems (silver), modelled as a star plus agent-ready tables (gold).
- Businesses created at runtime arrive through the operational store's extract and flow through the same models.
- Quality: four gates; ODCS contracts (303 rules); import validation with per-row reasons; no buyer names, emails or addresses beyond a one-way buyer key (tested).
- Known data limits: simulated dates, shipping speed and dispute outcomes; three shops; one category.

## 04 Methodology selection (data scientist)

- **Rules, not a model, for standing.** Five published thresholds are explainable and checkable; an opaque score would be neither.
- **Recent window of 50 orders** so a shop that improves can earn the seal.
- **Evidence strength, not probability:** high, medium, low by record size. It never claims a chance the shop is safe.
- **Agent evaluation:** code graders on tool trace and end state first (tau-bench style, `pass^k`), then a regression matrix (promptfoo), then simulated multi-turn shoppers (ArkSim).

## 05 Analytics and model development (analytics engineer, data scientist)

- Semantic layer: 4 metric views, 24 measures, each defined once.
- Star schema: 8 dimensions and 9 facts in gold, with every foreign key under contract.
- Rule sets by business type, as data: physical, services, digital.
- Agent: one Claude model, eight tools, plain loop; system prompt states the boundaries.
- Recorded result (first version of the tools, 2026-11-10): Sonnet 5.5 25 of 50 to 37 of 50; Haiku 5.5 28 of 50 to 50 of 50 (possibly over-weighting the seal).

## 06 Deployment (data engineer)

- One container: the image builds the warehouse behind the gates, then serves API, MCP and site.
- CI runs the evidence pack (131 tests and the eval harness check) and the web build.
- Not yet deployed or run against live PayPal. See the README.

## 07 Lifecycle management (all roles)

- **Monitor:** `/api/health` (gates green, last refresh, modes), contract results per run, an audit trail per business.
- **Refresh:** any change to evidence (import, capture, refund, tracking, consent) triggers a refresh; a red pipeline keeps the last good build.
- **Change control:** a threshold or metric change is a new criteria version; a breaking schema change is a new contract major version.
- **Feedback loops (CRISP-A tasks 6.3 and 7.2):** each new eval run is a new landed file; `gold.fact_agent_choice` then holds both, so a prompt or tool change is compared with history rather than replacing it.
- **Retire:** a withdrawn seal stops verifying at once.
