-- writes: gold.fact_attack_run
-- reads: silver.agent_attack_outcomes, silver.agent_eval_attacks, gold.dim_model
-- key: model, attack_id
-- grain: one row per model per attack
SELECT dm.model_key, o.model, a.attack_id, a.request, a.pass_rule, a.why, o.outcome, o.outcome = 'passed' AS passed
FROM silver.agent_attack_outcomes o
JOIN silver.agent_eval_attacks a USING (attack_id)
JOIN gold.dim_model dm USING (model)
