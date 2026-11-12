-- writes: silver.agent_eval_attacks
-- reads: bronze.agent_eval_attacks
-- key: attack_id
-- grain: one row per pre-registered attack and its pass rule
SELECT
    payload->>'$.id'                 AS attack_id,
    payload->>'$.request'            AS request,
    payload->>'$.pass_if.rule'       AS pass_rule,
    payload->>'$.pass_if.merchant'   AS pass_rule_merchant,
    payload->>'$.pass_if.why'        AS why
FROM bronze.agent_eval_attacks
