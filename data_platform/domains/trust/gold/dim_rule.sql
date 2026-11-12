-- writes: gold.dim_rule
-- reads: silver.trust_rules, gold.dim_metric
-- key: rule_key
-- grain: one row per published rule per rule set (star dimension)
SELECT CAST(r.rule_order AS INTEGER) AS rule_key, r.ruleset, r.rule, r.rule_label, r.failure_phrase, m.metric_key, r.metric, r.comparison,
       r.threshold, r.threshold_2, r.criteria_version, r.recent_window_orders
FROM silver.trust_rules r
JOIN gold.dim_metric m USING (metric)
