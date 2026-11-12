-- writes: silver.trust_evidence_classes
-- reads: bronze.trust_evidence_classes
-- key: evidence_class
-- grain: one row per evidence class a fact can carry
SELECT payload->>'$.evidence_class' AS evidence_class, payload->>'$.meaning' AS meaning, _row_no AS strength_order
FROM bronze.trust_evidence_classes
