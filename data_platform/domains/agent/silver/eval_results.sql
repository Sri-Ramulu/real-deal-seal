-- writes: silver.agent_eval_results
-- reads: bronze.agent_eval_results
-- grain: one row per recorded agent run (a re-run of the same task is a new row)
SELECT
    _row_no                                    AS run_no,
    payload->>'$.exp'                          AS experiment,
    payload->>'$.id'                           AS task_id,
    payload->>'$.mode'                         AS mode,
    payload->>'$.model'                        AS model,
    payload->>'$.request'                      AS request,
    payload->>'$.choice'                       AS choice_line,
    payload->>'$.merchant'                     AS chosen_merchant_id,
    payload->>'$.kind'                         AS chosen_kind,
    payload->>'$.answer'                       AS answer,
    CAST(payload->'$.tools' AS VARCHAR[])      AS tools_called,
    CAST(payload->>'$.cost_usd' AS DOUBLE)     AS cost_usd,
    CAST(payload->>'$.input_tokens' AS INTEGER)  AS input_tokens,
    CAST(payload->>'$.output_tokens' AS INTEGER) AS output_tokens
FROM bronze.agent_eval_results
