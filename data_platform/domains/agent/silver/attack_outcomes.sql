-- writes: silver.agent_attack_outcomes
-- reads: bronze.agent_eval_summary
-- key: model, attack_id
-- grain: one row per model per attack, as graded by the pre-registered pass rule at run time
SELECT b._key AS model, o.key AS attack_id, o.value->>'$' AS outcome
FROM bronze.agent_eval_summary b, json_each(b.payload->'$.attacks.outcomes') o
