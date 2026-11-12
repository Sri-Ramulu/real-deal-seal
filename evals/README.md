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
- **Recorded live on 12 Nov 2026** (`evals/live/`): 50 paired requests and 11 attacks for Claude Sonnet and Claude Haiku,
  run through the deployed site's chat API with fallback off, graded by `evals/live/grade.py` into
  `data_platform/landing/agent/` (`gold.fact_agent_choice`, `gold.fact_attack_run`). Sonnet picked an honest small shop
  9 of 50 times without evidence and 35 of 50 with it; shops whose seals were withdrawn fell from 34 picks to 0. Two
  full repeat runs the same day gave 11 to 37 and 9 to 38 (withdrawn: 33 to 0 both times). `grade.py --repeats` lands
  them in `repeat_results.jsonl`; `gold.fact_agent_repeat` counts them and `gold.fact_agent_run` lists every pick.
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
