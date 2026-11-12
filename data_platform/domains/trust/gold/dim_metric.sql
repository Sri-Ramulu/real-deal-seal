-- writes: gold.dim_metric
-- reads: silver.trust_metric_definitions
-- key: metric_key
-- grain: one row per published metric definition (star dimension)
SELECT CAST(display_order AS INTEGER) AS metric_key, metric, metric_label, unit, layer, applies_to, is_optional_to_disclose, definition, criteria_version
FROM silver.trust_metric_definitions
