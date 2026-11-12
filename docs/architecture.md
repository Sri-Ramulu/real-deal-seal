# Architecture

```
PayPal sandbox ──read-back──▶ landing/ ─┐
                                        ├─▶ bronze ─▶ silver (canonical) ─▶ gold (star + agent-ready) ─▶ API ─▶ site, MCP, assistant
operational store ──extract──▶ extract/ ┘                                                               │
(accounts, consent, imports, checkouts, events)  ◀── refresh job: export, rebuild, reconcile credentials ┘
buyer ──approves in PayPal──▶ checkout (server asks PayPal for the truth) ──▶ operational store ──▶ refresh
```

Two stores with different jobs. The **operational store** (SQLite, `api/rds/store.py`) is the system of record for
tenants: it changes one transaction at a time. The **warehouse** (DuckDB) is rebuilt from landing plus the
operational extract and is read-only to the API. `refresh.py` connects them: it exports, rebuilds beside the live
warehouse, swaps only if all four gates pass, then issues, supersedes or revokes credentials to match.

## 1. Data mesh x medallion

**Mesh** answers *who owns what*. **Medallion** answers *how clean is it*. Each domain runs its own medallion.

| Domain | Owns | Data product (output ports) | Read by |
|---|---|---|---|
| merchant | who each business is, its type and what it disclosed | Merchant Directory: `gold.dim_merchant` | every other domain |
| commerce | orders, payment and fulfilment events, catalog, web prices | Commerce Record: `fact_orders`, `fact_payment_events`, `fact_fulfillment_events`, `fact_monthly_sales`, `dim_date`, `dim_product`, `dim_source_system` | trust, studio, scorecard |
| trust | rules, metric definitions, facts, standings | Merchant Passport: `merchant_passport`, `agent_offers`, `fact_metric_observations`, `fact_rule_results`, `dim_metric`, `dim_rule`, `dim_evidence_class` | agent tools, signer, every page |
| agent | recorded agent decisions | Agent Decisions: `fact_agent_choice`, `fact_agent_switch`, `fact_attack_run`, `dim_model` | proof lab, scorecard |

The four mesh principles, as built:

- **Domain ownership:** everything a domain owns sits in `data_platform/domains/<domain>/`.
- **Data as a product:** `product.yaml` (purpose, owner, consumers, ports), `metadata.yaml`, `contract.odcs.yaml`, `semantic.yaml`.
- **Self-serve platform:** `data_platform/rdsp/` loads, runs, gates and publishes for every domain the same way.
- **Federated governance:** the same header rules, gates and contract checker apply to all domains.

| Layer | Rule |
|---|---|
| landing | Files as delivered. Never edited. Hashed on every run. |
| bronze | Every delivered row as JSON text plus file, hash, row number, load time. Nothing dropped. |
| silver | Typed, deduplicated and canonical: one shape for orders, payment events and fulfilment events whatever system they came from. |
| gold | A star schema for analytics, and agent-ready tables built on it. The only layer consumers read. |

## 2. The five concepts from the data products course, and where each lives

| Concept | In this repo | Proof it works |
|---|---|---|
| Data product | `domains/*/product.yaml`; shown on `/developers` | `test_every_product_has_a_contract` |
| Metadata | `domains/*/metadata.yaml`: owner, description, every column's meaning and PII flag for agent-facing tables | `test_agent_facing_tables_document_every_column` |
| Semantic layer | `domains/*/semantic.yaml` + `rdsp/semantic.py`; `/api/platform/metric` | `test_unknown_measure_is_refused`, `test_net_sales_agree_between_semantic_layer_and_passport` |
| Lineage | `-- reads:` / `-- writes:` headers parsed by `rdsp/lineage.py` | `test_passport_traces_back_to_the_paypal_files` |
| Data contract | `domains/*/contract.odcs.yaml` (ODCS layout) checked by `rdsp/contracts.py` at gate 4 | `test_a_broken_promise_turns_the_contract_red` |

## 3. Four gates

1. **landing:** every declared source file is present.
2. **bronze:** rows loaded equal rows delivered, per file.
3. **keys:** each model's declared key is unique and never null.
4. **contracts:** every rule of every contract holds (303 on the seed data), including every foreign key of the star.

A red gate stops the build. At runtime a red refresh keeps the last good warehouse serving and records the failure (`test_a_red_pipeline_keeps_the_last_good_warehouse`).

## 3a. The star schema

| Kind | Tables |
|---|---|
| Dimensions (8) | `dim_merchant`, `dim_date`, `dim_product`, `dim_source_system`, `dim_metric`, `dim_rule`, `dim_evidence_class`, `dim_model` |
| Transaction facts | `fact_orders` (one row per completed order), `fact_payment_events`, `fact_fulfillment_events` |
| Snapshot facts | `fact_monthly_sales` (business x month), `fact_metric_observations` (business x metric), `fact_rule_results` (business x rule) |
| Evaluation facts | `fact_agent_choice`, `fact_agent_switch`, `fact_attack_run` |
| Agent-ready, on top of the star | `merchant_passport`, `agent_offers`, `market_price_context` |

- Surrogate keys are assigned per build; the natural key (`merchant_id`, `sku`, `order_id`) is the stable identifier and stays on every fact.
- `dim_merchant` is conformed: commerce, trust and agent facts all join to it.
- Net sales agree from three directions: `fact_orders.net_usd`, signed `fact_payment_events`, and `fact_monthly_sales` (a contract rule and a test).
- A business is measured only on metrics whose `dim_metric.applies_to` includes its rule set (a contract rule).

## 3b. The universal model and business types

Every business uses the same tables. What differs is which fulfilment event counts and which rules apply:

| Business type | Fulfilment event | Rule set | Type-specific rules |
|---|---|---|---|
| physical | `shipped` (+ `tracking_added`) | physical | tracking 90%+, shipped within 2 days 80%+ |
| services | `service_completed` | services | completion 90%+, cancellations by the business 10% or fewer |
| digital | `digital_delivered` | digital | delivery 95%+ |
| local | `booking_kept` | services | same as services |

All types share: enough history (30 orders over 60 days), disputes lost 2% or fewer, refunds 8% or fewer.
Rules and metric definitions are data (`landing/reference/criteria.json`), versioned as `rds-criteria-2`.

## 4. Why gold is shaped for an agent

An agent does badly with wide raw tables and well with small, meaningful, pre-joined answers.

- `gold.merchant_passport`: one row per shop; standing, plain-language headline and verdict, counts, flags.
- `gold.fact_metric_observations`: one row per fact with numerator, denominator, window and evidence class, so a tool can say "47 of 49".
- `gold.agent_offers`: one row per product with the shop's standing beside it and two safety flags (`seller_text_has_instructions`, `shows_unverifiable_badge`). Never ranked by trust.
- Shops without a record get `no_record`, never an invented score. A short record gets `new`, never `verified` (a contract rule enforces both).

## 5. Agent design

One model, eight tools, a plain loop (`api/rds/agent.py`). No framework and no second agent, following Anthropic's
published guidance: start with the simplest thing, invest in the tools, and measure.

| Decision | Who decides |
|---|---|
| Which product fits, how to explain it | the model |
| Price, stock, which shop sells it | server-side catalog |
| Whether a seal is genuine | `passport.verify` (Ed25519) |
| Whether a payment happened | PayPal's API response, checked in `checkout.complete` |

Seller text is wrapped as `{"untrusted": true, ...}` with a flag when it addresses AI assistants. Tool results are small,
use names and plain words, and say what to do next on errors.

## 6. Checkout state machine and the commerce loop

`CREATED ─▶ CAPTURING ─▶ CAPTURED` or `FAILED`; `CREATED ─▶ CANCELLED`. Transitions are compare-and-set, so ten
simultaneous returns capture once. The idempotency key maps to one PayPal order (`PayPal-Request-Id`). Stock is
re-checked at the moment of capture, so two buyers cannot both take the last unit. A PayPal-confirmed capture is
written to `orders` and `payment_events` and triggers a refresh; a simulated one is stored but never exported.
Webhooks are processed only after PayPal confirms the signature, and once per event; a refund is recorded once per
provider reference.

## 7. Accounts, consent and credentials

- **Accounts:** scrypt password hashes, bearer sessions stored as hashes, 12-hour expiry, rate-limited sign-in.
- **Isolation:** every `/api/studio/{merchant_id}` route depends on `auth.require_merchant`; a wrong-tenant call returns 403 and is audited.
- **Consent:** publishing the passport is a `consent_grants` row; so is each statement share (one recipient, one purpose, a token stored as a hash). Withdrawing revokes.
- **Disclosure:** optional facts (net sales, returning buyers) can be hidden; a fact a rule depends on cannot.
- **Credentials:** the id is derived from the signed content. A changed fact means a new credential and the old one is superseded; withdrawal revokes; unchanged facts re-published bring the same credential back.
- **Keys:** a key ring. Rotation retires the old key (still verifies), revocation fails everything it signed.

## 8. Known gaps

SQLite rather than PostgreSQL, so no database-level row security. No PayPal sign-in flow for arbitrary merchants.
No managed secret store: the key ring is a file under `RDS_VAR_DIR` with owner-only permissions. Roles are owner
and staff labels without separate permissions. The refresh job runs in-process and rebuilds the whole warehouse,
which is right for this size and wrong for a large one.
