-- writes: silver.trust_metric_definitions
-- reads: bronze.trust_metrics
-- key: metric
-- grain: one row per published metric definition of the current criteria version
SELECT
    payload->>'$.metric'                     AS metric,
    payload->>'$.label'                      AS metric_label,
    payload->>'$.unit'                       AS unit,
    payload->>'$.layer'                      AS layer,
    CAST(payload->'$.applies_to' AS VARCHAR[]) AS applies_to,
    CAST(payload->>'$.optional' AS BOOLEAN)  AS is_optional_to_disclose,
    payload->>'$.definition'                 AS definition,
    file_meta->>'$.criteria_version'         AS criteria_version,
    _row_no                                  AS display_order
FROM bronze.trust_metrics
