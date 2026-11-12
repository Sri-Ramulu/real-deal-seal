PY ?= .venv/bin/python

.PHONY: setup build test web api dev evals evidence seed clean
setup:            ## one-time: Python env and web dependencies
	python3 -m venv .venv && .venv/bin/pip install -q -r requirements-dev.txt
	cd web && npm install
build:            ## landing -> bronze -> silver -> gold, behind four gates
	$(PY) data_platform/run/build.py
test: build       ## 154 tests: pipeline, star schema, contracts, passports, withdrawals, evidence switch, models, checkout, webhooks, SDK
	$(PY) -m pytest data_platform/tests api/tests -q
	$(PY) evals/tau/run.py --agent oracle
web:              ## build the site into web/build (served by the API)
	cd web && npm run build
api: build        ## run everything on http://localhost:8000 (reads .env by itself)
	.venv/bin/uvicorn rds.main:app --app-dir api --port 8000
dev:              ## hot-reload frontend on :5173, proxying to the API on :8000
	cd web && npm run dev
evidence:         ## run everything and write docs/evidence/ (claims and attack cases mapped to tests), sdk/openapi.json
	$(PY) scripts/evidence_pack.py
seed:             ## onboard the two sample businesses through the running API
	$(PY) scripts/seed_samples.py
test-pg:          ## the API tests on PostgreSQL: DATABASE_URL=postgresql://... make test-pg
	DATABASE_URL=$(DATABASE_URL) $(PY) -m pytest api/tests -q
e2e:              ## browser tests of the main journeys (needs: npx playwright install chromium, or CHROME_PATH)
	cd web && npm run e2e
evals:            ## real-model evals: MODEL=gemini|claude-opus|claude-sonnet (the simulated shopper needs ANTHROPIC_API_KEY)
	$(PY) evals/tau/run.py --agent live --model $(or $(MODEL),gemini) -k 3
clean:
	rm -rf data_platform/warehouse data_platform/build var web/build web/.svelte-kit
