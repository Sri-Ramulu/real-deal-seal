-- writes: gold.dim_evidence_class
-- reads: silver.trust_evidence_classes
-- key: evidence_class_key
-- grain: one row per evidence class, strongest first (star dimension)
SELECT CAST(strength_order AS INTEGER) AS evidence_class_key, evidence_class, meaning,
       evidence_class = 'paypal_sandbox_confirmed' AS is_authoritative
FROM silver.trust_evidence_classes
