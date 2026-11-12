# Plan coverage

How each of the 40 sections of the master plan, and each of the 12 points of the build brief, lands in this
repository. **Built** means there is code and a passing test or a page you can open. **Written** means a document.
**Not done** means exactly that.

## The 40 sections

| # | Section | Status | Where |
|---|---|---|---|
| 1 | The problem | Built | Home and `/business` show the Lightspeed study with its source; `/story` scene 1 |
| 2 | Beneficiary priority: PayPal first | Built | `/business` "Who gains, in order"; scorecard perspective "Value for PayPal" |
| 3 | Lessons from the verified-records business model | Built | Business Readiness statement (`api/rds/statement.py`); no lending, by design |
| 4 | What the product is: three connected experiences | Built | Merchant Studio (`/studio`), Shop and assistant (`/shop`, `/assistant`), Developers (`/developers`, `/mcp`, REST) on one data foundation |
| 5 | Exact product scope | Built, with gaps | See "Scope table" below |
| 6 | A platform for any merchant | Built | Operational store with a tenant key on every row; four business types, three rule sets; `test_a_service_business_joins_and_is_judged_by_service_rules` |
| 7 | The eight-part narrative | Built | `/story`, eight scenes on live numbers |
| 8 | The three demonstration merchants | Built | Lydia sealed, Martha verified, Priscilla new: `test_standings` |
| 9 | Product design and navigation | Built | All ten product areas exist; mapping below |
| 10 | Merchant onboarding journey (10 steps) | Built, one step simulated | `/join` and `api/rds/onboarding.py`. Step 2 "connect PayPal" verifies configured sandbox credentials; a PayPal sign-in flow for arbitrary merchants (Partner Referrals) is not built |
| 11 | AI shopper journey (10 steps) | Built | Steps 1 to 10 in `agent.py`, `tools.py`, `checkout.py`; step 10 write-back in `checkout.record_order` |
| 12 | Design system | Built, changed on instruction | The brief replaced the linen and purple identity with red and black. Principles kept: states never rely on colour alone, evidence cards link to AG Grid, dates and sources visible, empty states explain, reduced motion |
| 13 | System architecture and six rules | Built | `docs/architecture.md`; rules 1 to 6 each have tests |
| 14 | Engineering stack | Built, three substitutions | SQLite instead of PostgreSQL (portable schema, not run on Postgres); own 2D timeline instead of Bryntum; hand-written client and OpenAPI instead of APIMatic SDKs |
| 15 | Data model (15 entities) | Built | 13 tables in `api/rds/migrations/001_init.sql` plus `metric_definitions` and `metric_observations` in the warehouse as `gold.dim_metric` and `gold.fact_metric_observations` |
| 16 | Evidence ingestion (14 steps) | Built | Import validation, provenance hash (`source_evidence`), canonical silver, dedupe, missingness, versioned metrics, gates, disclosure, signing, refresh on change, audit |
| 17 | Metrics and evidence policy | Built | Layers A, B, C in `gold.dim_metric`; five standing states; fairness contract rules |
| 18 | The Merchant Passport | Built | All 11 credential fields; registry with active, superseded, revoked; key rotation and revocation |
| 19 | MCP and agent tools | Built | Eight tools; `find_faithful_alternative` is named `find_sealed_alternative`, `get_merchant_trust` is `get_merchant_passport` |
| 20 | PayPal transaction lifecycle | Built against a stand-in | All nine steps and the listed financial controls have tests; none has run against the live sandbox |
| 21 | Trust, privacy and reliability | Built, with gaps | Auth, tenant isolation, aggregated public facts, one-way buyer keys, key ring, verified idempotent webhooks, audit, health. Not built: role management beyond owner and staff labels, database-level row security, managed secret storage |
| 22 | What the existing experiment proves | Built | `/proof` with limits stated |
| 23 | Evaluation design | Partly built | Harness for the four questions exists (`evals/`); model runs, repeated trials and blind review are not done |
| 24 | Adversarial evaluation (18 cases) | 17 automated, 1 not | `docs/evidence/README.md`; the receipt-injection case has no receipt reader to attack |
| 25 | Definition of technical completion (12 systems) | 11 met, 1 partly | Table below |
| 26 | Why PayPal would want it | Written and built | `/business`; scorecard |
| 27 | Business model and anti-pay-to-rank | Written and built | `/business`; no code path lets a plan change a standing |
| 28 | Business Readiness Passport | Built | Signed statement, one-recipient share, revoke, access log |
| 29 | Official rules | Checked | Devpost text and video script follow them; see `docs/devpost.md` |
| 30 | Cash prizes | Written | `docs/devpost.md` names the sponsor tools actually used |
| 31 | Sponsor selection | Partly | AG Grid: built and central. Channel3: cached price context. Render: config only, not deployed. APIMatic and Bryntum: not used |
| 32 to 33 | Competitive comparison | Written | Not reproduced as product; the product does not copy a resale marketplace |
| 34 | Independent judge score | Written | Honest scores are in the delivery note, not in the product |
| 35 | Win-probability claim | Declined | No evidence supports a 25 to 35% claim, and none is made anywhere in the repo |
| 36 | Implementation order (15 stages) | Followed | Stages 1 to 14 built in order; stage 15 (final presentation) needs a deployed app and a recorded video |
| 37 | Judge-facing story (10 scenes) | Built | Every scene can be performed in the running app; `docs/video-script.md` |
| 38 | Judge evidence package (10 claims) | Built | `make evidence` writes `docs/evidence/`; 12 claims mapped to tests |
| 39 | Build, retain, exclude | Followed | Excluded items are excluded: no lending, no credit score, no marketplace, no extra agents |
| 40 | The business proposition: three promises | Built | `/business` "Three promises"; each is enforced by a contract rule or test |

### Scope table (section 5)

| Capability | Status |
|---|---|
| PayPal sandbox payments | Built; tested against a stand-in, not the live sandbox |
| Trust facts and criteria, generalised | Built |
| Signed passport, clearly attributed | Built |
| AI shopping with MCP | Built; not run with a live model |
| Catalog adapters | File import built; store-platform connectors not built |
| Merchant Studio | Built |
| Coaching with measurable plans | Built; one action (add tracking) changes a record, the others list the orders to review |
| Business-readiness evidence | Built |
| Fulfilment visualisation | Built as an own timeline, physical goods aware |
| Market comparison | Cached Channel3 response only |
| Multi-merchant onboarding with consent and identity | Built, except a PayPal sign-in flow for arbitrary merchants |
| Reproducible evaluation | Harness built; model runs not done |
| Lending, marketplace | Excluded on purpose |

### Navigation (section 9)

Home/Discover `/` and `/shop` · Merchant Studio `/studio/{id}` · Merchant Passport `/shops/{id}` and studio "Passport and sharing" ·
Evidence Explorer studio "Evidence" · Growth Coach studio "Coach" · Orders and Operations studio "Orders" · Commerce `/shop`,
`/assistant`, studio "Catalog" · Business Readiness studio "Business readiness" and `/statement` · Proof Lab `/proof` · Developers `/developers`.

### Definition of completion (section 25)

| System | Evidence | Met |
|---|---|---|
| Merchant onboarding | New business added with no code change (API and extract tests) | Yes |
| Data integration | 175 orders reconcile; gates; v1 reconciliation | Yes |
| Metric engine | Every fact has a definition, numerator, denominator, class | Yes |
| Credential service | Genuine verifies; forged, edited, withdrawn, expired, superseded fail | Yes |
| Multi-tenancy | Cross-tenant reads and writes refused and audited | Yes |
| MCP | Eight tools list and answer | Yes |
| AI shopping | Not ranked by trust; a price-only task is won by the chain | Yes in code and harness; not run with a model |
| Checkout | Authoritative state verified, exact amount, once | Against a stand-in only |
| Coach | Add tracking: 39 to 40 of 48, recorded before and after | Yes |
| Business-readiness document | Totals reconcile; limits on the document | Yes |
| Evaluation harness | Fixed tasks, code graders, fresh state per trial | Yes for the harness |
| User experience | Merchant and buyer journeys run in the browser without a developer | Yes, in offline and simulated modes |

## The 12 points of the build brief

| # | Point | Status |
|---|---|---|
| 1 | CRISP-A backend, with analyst, data scientist, analytics engineer and data engineer roles | Built: `docs/crisp-a.md`. No data engineer job description was supplied |
| 2 | Repository structure after the reference data-platform repos | Built: rules in `CONTRIBUTING.md`, domains, headers, gates, contracts. The course video was not watched; the two reference repos were read |
| 3 | Data mesh fused with medallion; data products, metadata, semantic layer, lineage, contracts | Built, with a star schema in gold |
| 4 | Agent evals with tau-bench, promptfoo and ArkSim; Claude only | Harness and configs built; only the scripted harness check has been run |
| 5 | Gold layer shaped for AI agents | Built: `gold.merchant_passport`, `gold.agent_offers`, facts with denominators |
| 6 | Dashboards after Storytelling with Data; North Star and balanced scorecard | Built: `/scorecard`, studio overview |
| 7 | Data and business story for non-technical readers, before Developers | Built: `/story`, placed before Developers in the navigation; `/business` |
| 8 | Frontend inspired by the two reference sites, 2D, seal mascot, passport style | Built. Both sites were inspected with browser DevTools for type scale, radius, colour and easing; no logo, typeface or artwork was copied |
| 9 | Hackathon rules | Followed in the text and script; submission itself is yours to make |
| 10 | Beat the leading entry; cash-only sponsor targeting | Not something code can promise. Sponsor tools used are named honestly |
| 11 | Winning formula applied to the Devpost text | Written: `docs/devpost.md` |
| 12 | Step-by-step build, video script, video, honest scores | Built and written; the video is a silent captioned walkthrough of the local build |
