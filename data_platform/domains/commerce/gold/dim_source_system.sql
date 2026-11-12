-- writes: gold.dim_source_system
-- reads: silver.commerce_source_systems
-- key: source_system_key
-- grain: one row per system an order can come from (star dimension)
SELECT CAST(row_number() OVER (ORDER BY source_system) AS INTEGER) AS source_system_key, source_system, payment_evidence_class, description
FROM silver.commerce_source_systems
