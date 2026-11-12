-- writes: gold.fact_agent_choice
-- reads: silver.agent_eval_results, gold.merchant_passport, gold.dim_model
-- key: model, task_id, mode
-- grain: one row per model per shopping task per condition (baseline or with evidence)
SELECT
    dm.model_key,
    p.merchant_key                                 AS chosen_merchant_key,
    r.model,
    CAST(r.task_id AS INTEGER)                     AS task_id,
    r.mode,
    CASE r.mode WHEN 'baseline' THEN 'Search only' ELSE 'Search + evidence' END AS condition_label,
    r.request,
    r.chosen_merchant_id,
    p.merchant_name                                AS chosen_merchant_name,
    p.standing                                     AS chosen_standing,
    r.chosen_kind = 'small'                        AS chose_small_shop,
    r.chosen_kind = 'chain'                        AS chose_chain,
    coalesce(p.shows_unverifiable_badge, FALSE)    AS chose_fake_badge_shop,
    r.chosen_merchant_id IS NULL                   AS no_pick,
    len(r.tools_called)                            AS tool_calls,
    list_contains(r.tools_called, 'get_merchant_trust') AS read_evidence,
    r.cost_usd,
    r.input_tokens,
    r.output_tokens
FROM silver.agent_eval_results r
JOIN gold.dim_model dm USING (model)
LEFT JOIN gold.merchant_passport p ON p.merchant_id = r.chosen_merchant_id
WHERE r.experiment = 'choice'
