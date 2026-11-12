-- writes: gold.fact_agent_run
-- reads: silver.agent_eval_runs, gold.dim_model, gold.merchant_passport
-- key: model, run_no, task_id, mode
-- grain: one row per model per full run per shopping request per condition (every recorded pick, all runs)
SELECT dm.model_key, r.model, r.run_no, CAST(r.task_id AS INTEGER) AS task_id, r.mode,
       CASE r.mode WHEN 'baseline' THEN 'Evidence off' ELSE 'Evidence on' END AS condition_label,
       r.request, r.chosen_merchant_id, m.merchant_name AS chosen_merchant_name,
       CASE r.chosen_kind WHEN 'small' THEN 'Honest small shop' WHEN 'scam' THEN 'Seal withdrawn' WHEN 'chain' THEN 'Chain'
                          WHEN 'unknown' THEN 'Forged badge' ELSE 'No pick' END AS pick_kind,
       r.tool_calls, r.run_status = 'answered' AS answered, r.cost_usd, CAST(r.recorded_at AS DATE) AS recorded_on
FROM silver.agent_eval_runs r
JOIN gold.dim_model dm USING (model)
LEFT JOIN gold.merchant_passport m ON m.merchant_id = r.chosen_merchant_id
WHERE r.experiment = 'choice'
