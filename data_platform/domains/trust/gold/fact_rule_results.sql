-- writes: gold.fact_rule_results
-- reads: gold.fact_metric_observations, gold.dim_rule, gold.dim_merchant
-- key: merchant_id, rule
-- grain: one row per business per rule of its own rule set (snapshot fact)
SELECT
    dm.merchant_key,
    r.rule_key,
    o.merchant_id,
    r.ruleset,
    r.rule,
    r.rule_label,
    r.failure_phrase,
    r.metric,
    o.value                                         AS measured_value,
    o.numerator,
    o.denominator,
    o.evidence_class,
    o.value IS NOT NULL                             AS measured,
    coalesce(CASE
        WHEN r.rule = 'enough_history' THEN o.value >= r.threshold AND h.value >= r.threshold_2
        WHEN r.comparison = '>=' THEN o.value >= r.threshold
        WHEN r.comparison = '<=' THEN o.value <= r.threshold
    END, FALSE)                                     AS met,
    r.threshold,
    r.comparison,
    r.criteria_version,
    r.rule_key                                      AS rule_order
FROM gold.dim_merchant dm
JOIN gold.dim_rule r ON r.ruleset = dm.ruleset
JOIN gold.fact_metric_observations o ON o.merchant_id = dm.merchant_id AND o.metric = r.metric
JOIN gold.fact_metric_observations h ON h.merchant_id = dm.merchant_id AND h.metric = 'history_days'
