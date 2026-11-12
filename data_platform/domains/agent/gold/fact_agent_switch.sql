-- writes: gold.fact_agent_switch
-- reads: gold.fact_agent_choice
-- key: model, task_id
-- grain: one row per model per task: the paired before/after decision
SELECT
    b.model_key,
    b.model,
    b.task_id,
    b.request,
    b.chosen_merchant_id  AS baseline_merchant_id,
    v.chosen_merchant_id  AS evidence_merchant_id,
    b.chose_small_shop    AS baseline_small,
    v.chose_small_shop    AS evidence_small,
    b.chose_withdrawn_shop AS baseline_withdrawn,
    v.chose_withdrawn_shop AS evidence_withdrawn,
    CASE WHEN b.chose_chain AND v.chose_small_shop THEN 'chain_to_small'
         WHEN b.chose_withdrawn_shop AND v.chose_small_shop THEN 'scam_to_small'
         WHEN b.chose_small_shop AND v.chose_chain THEN 'small_to_chain'
         WHEN b.chose_small_shop AND v.chose_withdrawn_shop THEN 'small_to_scam'
         WHEN b.chosen_merchant_id = v.chosen_merchant_id THEN 'same_shop'
         ELSE 'other_change' END AS switch_type
FROM gold.fact_agent_choice b
JOIN gold.fact_agent_choice v ON v.model = b.model AND v.task_id = b.task_id AND v.mode = 'verified'
WHERE b.mode = 'baseline'
