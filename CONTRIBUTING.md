# Contributing to Real Deal Seal

Real Deal Seal turns a shop's PayPal record into a signed Merchant Passport that AI shopping assistants can read and
check. Read `docs/architecture.md` before changing anything.

## Working agreements

- Back every claim about data with the query or test that shows it, and say what you didn't run.
- Discuss a change to a data contract, a metric definition or a rule threshold before making it. Those are promises
  to the people and agents who read them.
- Keep scratch files out of the repository.

## Rules of the codebase

- **`data_platform/landing/` is what the sources sent.** It is never edited. A correction is a new file.
- **The operational store is the system of record for tenants.** Accounts, consent, imports, checkouts and events live in
  `api/rds/store.py` (schema in `api/rds/migrations/`). `refresh.py` exports it to an extract; the pipeline reads the extract.
- **Every tenant-owned route goes through `auth.require_merchant`.** A new private route without it is a bug.
- **Gold is a star.** Facts point at dimensions through surrogate keys; a new fact needs its foreign keys in the contract.
- **Bronze keeps everything, silver cleans, gold models.** The API, the agent tools and every page read gold
  (or two silver reference tables). Nothing reads bronze except silver.
- **A domain owns its tables.** SQL, metadata, contract and metrics live in `data_platform/domains/<domain>/`.
  The shared code in `data_platform/rdsp/` knows nothing about any one domain.
- **Lineage is read, never drawn.** Every SQL file starts with `-- writes:`, `-- reads:`, `-- key:`, `-- grain:`.
- **A number has one definition**, in the domain's `semantic.yaml`. Ask for the measure; never retype the formula.
- **The contract is a promise.** A change that breaks `contract.odcs.yaml` is a new major version.
- **Code decides money and trust.** Seal validity, prices, stock and payment state are plain Python with tests.
  The model reads, compares and explains. It never declares a payment complete or a seal genuine.
- **Nothing is upgraded.** Simulated, merchant-reported and PayPal-confirmed facts keep their labels end to end.
  Imported records can never earn the seal; a simulated checkout is never exported as evidence.
- **A business is judged only by the rule set of its type.** Adding a rule means adding it to `criteria.json`, not to SQL.
- **PayPal is the evidence source, not the issuer.** Never write copy that implies PayPal signs or endorses a seal.

- **Evidence off means no evidence.** With the Evidence switch off, nothing from Real Deal Seal (standing, seal,
  passport hint, warning) may reach the model or the page. The `evidence` flag is set by the server, never by a model.
- **A withdrawn seal is never an unknown shop.** Every reader (tools, pages, checkout, seal check) shows the withdrawal
  and its reason.

## Commands

`make setup`, `make build`, `make test`, `make evidence`, `make web`, `make api`, `make evals MODEL=gemini`. See the README.
