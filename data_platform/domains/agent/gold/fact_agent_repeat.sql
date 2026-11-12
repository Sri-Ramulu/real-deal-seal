-- writes: gold.fact_agent_repeat
-- reads: silver.agent_eval_runs, gold.dim_model
-- key: model, run_no, mode
-- grain: one row per model per full run of the evaluation per condition
WITH picks AS (
    SELECT model, run_no, mode, count(*) AS tasks,
           count(*) FILTER (chosen_kind = 'small')   AS honest_small_picks,
           count(*) FILTER (chosen_kind = 'scam')    AS withdrawn_shop_picks,
           count(*) FILTER (chosen_kind = 'chain')   AS chain_picks,
           count(*) FILTER (chosen_kind = 'unknown') AS fake_badge_picks,
           count(*) FILTER (chosen_kind IS NULL)     AS no_picks,
           CAST(max(recorded_at) AS DATE)            AS recorded_on
    FROM silver.agent_eval_runs WHERE experiment = 'choice' GROUP BY ALL
), att AS (
    SELECT model, run_no, count(*) FILTER (attack_outcome = 'passed') AS attacks_passed, count(*) AS attacks_total
    FROM silver.agent_eval_runs WHERE experiment = 'attacks' GROUP BY ALL
)
SELECT dm.model_key, p.model, p.run_no, p.mode,
       CASE p.mode WHEN 'baseline' THEN 'Search only' ELSE 'Search + evidence' END AS condition_label,
       CAST(p.tasks AS INTEGER) AS tasks, CAST(p.honest_small_picks AS INTEGER) AS honest_small_picks,
       CAST(p.withdrawn_shop_picks AS INTEGER) AS withdrawn_shop_picks, CAST(p.chain_picks AS INTEGER) AS chain_picks,
       CAST(p.fake_badge_picks AS INTEGER) AS fake_badge_picks, CAST(p.no_picks AS INTEGER) AS no_picks,
       CASE WHEN p.mode = 'verified' THEN CAST(a.attacks_passed AS INTEGER) END AS attacks_passed,
       CASE WHEN p.mode = 'verified' THEN CAST(a.attacks_total AS INTEGER) END AS attacks_total, p.recorded_on
FROM picks p JOIN gold.dim_model dm USING (model) LEFT JOIN att a USING (model, run_no)
