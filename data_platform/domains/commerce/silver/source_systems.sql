-- writes: silver.commerce_source_systems
-- reads: bronze.commerce_source_systems
-- key: source_system
-- grain: one row per system an order can come from, with the evidence class its payments carry
SELECT payload->>'$.source_system' AS source_system, payload->>'$.payment_evidence_class' AS payment_evidence_class, payload->>'$.description' AS description
FROM bronze.commerce_source_systems
