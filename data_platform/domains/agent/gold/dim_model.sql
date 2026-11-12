-- writes: gold.dim_model
-- reads: silver.agent_eval_results
-- key: model_key
-- grain: one row per AI model that appears in a recorded evaluation (star dimension)
SELECT CAST(row_number() OVER (ORDER BY model) AS INTEGER) AS model_key, model,
       split_part(replace(model, 'claude-', ''), '-', 1) AS model_family
FROM (SELECT DISTINCT model FROM silver.agent_eval_results)
