-- writes: silver.trust_rules
-- reads: bronze.trust_rules
-- key: ruleset, rule
-- grain: one row per published rule per rule set of the current criteria version
SELECT
    payload->>'$.ruleset'                         AS ruleset,
    payload->>'$.rule'                            AS rule,
    payload->>'$.metric'                          AS metric,
    payload->>'$.comparison'                      AS comparison,
    CAST(payload->>'$.threshold' AS INTEGER)      AS threshold,
    TRY_CAST(payload->>'$.threshold_2' AS INTEGER) AS threshold_2,
    payload->>'$.label'                           AS rule_label,
    payload->>'$.short'                           AS failure_phrase,
    file_meta->>'$.criteria_version'              AS criteria_version,
    CAST(file_meta->>'$.recent_window_orders' AS INTEGER) AS recent_window_orders,
    _row_no                                       AS rule_order
FROM bronze.trust_rules
