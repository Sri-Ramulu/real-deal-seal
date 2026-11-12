-- writes: silver.agent_eval_runs
-- reads: bronze.agent_eval_repeats, silver.agent_eval_results, silver.agent_attack_outcomes
-- key: model, run_no, experiment, task_id, mode
-- grain: one row per model per full run of the evaluation per request (or attack) per condition; run 1 is the primary run
SELECT r.model, 1 AS run_no, r.experiment, r.task_id, r.mode, r.request, r.chosen_merchant_id, r.chosen_kind,
       CAST(len(r.tools_called) AS INTEGER) AS tool_calls, r.run_status, o.outcome AS attack_outcome, r.cost_usd, r.recorded_at
FROM silver.agent_eval_results r
LEFT JOIN silver.agent_attack_outcomes o ON r.experiment = 'attacks' AND o.model = r.model AND o.attack_id = r.task_id
UNION ALL
SELECT payload->>'$.model', CAST(payload->>'$.run' AS INTEGER), payload->>'$.exp', payload->>'$.id', payload->>'$.mode',
       payload->>'$.request', payload->>'$.merchant', payload->>'$.kind',
       CAST(len(CAST(payload->'$.tools' AS VARCHAR[])) AS INTEGER), coalesce(payload->>'$.status', 'answered'), payload->>'$.outcome',
       CAST(payload->>'$.cost_usd' AS DOUBLE), CAST(substr(payload->>'$.recorded_at', 1, 19) AS TIMESTAMP)
FROM bronze.agent_eval_repeats
