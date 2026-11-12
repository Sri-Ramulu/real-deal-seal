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
    coalesce(r.chosen_kind = 'small', FALSE)       AS chose_small_shop,        -- an honest small shop: its seal is not withdrawn
    coalesce(r.chosen_kind = 'chain', FALSE)       AS chose_chain,
    coalesce(r.chosen_kind = 'scam', FALSE)        AS chose_withdrawn_shop,    -- a shop whose seal Real Deal Seal withdrew
    coalesce(p.shows_unverifiable_badge, FALSE)    AS chose_fake_badge_shop,
    r.chosen_merchant_id IS NULL                   AS no_pick,
    len(r.tools_called)                            AS tool_calls,
    list_has_any(r.tools_called, ['get_merchant_passport', 'get_merchant_trust']) AS read_evidence,
    r.cost_usd,
    r.input_tokens,
    r.output_tokens
FROM silver.agent_eval_results r
JOIN gold.dim_model dm USING (model)
LEFT JOIN gold.merchant_passport p ON p.merchant_id = r.chosen_merchant_id
WHERE r.experiment = 'choice'
