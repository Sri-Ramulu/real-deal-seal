# Agent evaluation

Three layers, cheapest first. Code grades wherever it can; a model grades only what code cannot.

| Layer | Tool | What it answers | Needs a model key |
|---|---|---|---|
| Task success and end state | `evals/tau` (tau-bench style) | Did the agent call the right tools, pick the right product and leave the checkout table in the right state? `pass^k` over repeated trials. | only for `--agent claude` |
| Regression matrix | `evals/promptfoo` | Same requests with and without evidence; attacks; one faithfulness rubric. | yes |
| Simulated shoppers | `evals/arksim` | Multi-turn conversations with pushy, misled and anxious shoppers; per-turn scores and failure labels. | yes |
| Recorded baseline | `data_platform/landing/agent` | The 50 paired shopping tasks and 10 attacks run on 2026-11-10 with the first version of the tools, served from `gold.fact_agent_choice`. | no (already recorded) |

## What has and has not been run

- **Run and checked in this repo:** the tau harness with the scripted `oracle` policy (12 of 12 tasks pass) and the scripted
  `naive` policy (0 of 12 pass). That proves the tasks are solvable and the graders can fail. It says nothing about a model.
- **Recorded earlier, with the first version of the tools:** 50 paired tasks x 2 models and 10 attacks x 2 models
  (`gold.fact_agent_choice`, `gold.fact_attack_run`). Sonnet 5.5 picked a small shop 25 of 50 times without evidence and 37 of 50 with it.
- **Not yet run against this rebuild:** `--agent claude`, promptfoo and ArkSim. They need `ANTHROPIC_API_KEY` on the server
  (and a simulator model for ArkSim). Until they run, no claim in this repo rests on them.

## Run

```bash
python evals/tau/run.py --agent oracle        # harness check, no key
python evals/tau/run.py --agent claude -k 3   # real assistant, pass^3
npx promptfoo@latest eval -c evals/promptfoo/promptfooconfig.yaml
pip install arksim && arksim simulate-evaluate evals/arksim/config.yaml
```

## Design notes

- One agent, eight tools, no framework. Money, prices and seal validity are decided by code.
- Each tau trial gets a fresh operational store, so "exactly one checkout session, status CREATED" is an exact check.
- The simulated shopper never sees the grading rule; the agent never sees the shopper's goal.
- A task that only a sealed small shop can win would reward favouritism, so the suite includes `cheapest-wins`
  (the chain is correct) and `nothing-fits` (no pick is correct).
