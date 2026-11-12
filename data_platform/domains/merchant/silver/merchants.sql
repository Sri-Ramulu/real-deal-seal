-- writes: silver.merchant_merchants
-- reads: bronze.merchant_merchants, bronze.merchant_external, bronze.merchant_workspaces
-- key: merchant_id
-- grain: one row per business: demo shops, comparison shops with no record, and workspaces created through onboarding
SELECT
    b._key                                 AS merchant_id,
    b.payload->>'$.name'                     AS merchant_name,
    b.payload->>'$.category'                 AS category,
    'physical'                             AS business_type,
    'US'                                   AS region,
    b.payload->>'$.sells'                    AS sells,
    b.payload->>'$.ships_from'               AS ships_from,
    b.payload->>'$.returns'                  AS returns_policy,
    'paypal_merchant'                      AS merchant_kind,
    'demo'                                 AS origin,
    b.payload->>'$.connection.method'        AS connection_method,
    b.payload->>'$.connection.status'        AS connection_status,
    coalesce(CAST(w.payload->>'$.passport_published' AS BOOLEAN), TRUE)                   AS passport_published,
    coalesce(CAST(w.payload->'$.hidden_metrics' AS VARCHAR[]), CAST([] AS VARCHAR[]))    AS hidden_metrics,
    CAST(NULL AS VARCHAR)                  AS self_claim,
    CAST(NULL AS VARCHAR)                  AS displayed_badge,
    w.payload->>'$.seal_withdrawn_by'      AS seal_withdrawn_by,
    CAST(w.payload->>'$.seal_withdrawn_at' AS TIMESTAMP) AS seal_withdrawn_at,
    w.payload->>'$.seal_withdrawn_reason'  AS seal_withdrawn_reason
FROM bronze.merchant_merchants b
LEFT JOIN bronze.merchant_workspaces w ON w.payload->>'$.merchant_id' = b._key AND w.payload->>'$.origin' = 'demo'
UNION ALL
SELECT
    _key, payload->>'$.name', 'Home & Garden', 'physical', 'US', CAST(NULL AS VARCHAR),
    payload->>'$.ships_from', payload->>'$.returns',
    CASE payload->>'$.kind' WHEN 'chain' THEN 'national_chain' ELSE 'unknown_seller' END,
    'external', 'none', 'none', TRUE, CAST([] AS VARCHAR[]),
    payload->>'$.self_claim', payload->>'$.seal',
    CAST(NULL AS VARCHAR), CAST(NULL AS TIMESTAMP), CAST(NULL AS VARCHAR)
FROM bronze.merchant_external
UNION ALL
SELECT
    payload->>'$.merchant_id', payload->>'$.name', payload->>'$.category', payload->>'$.business_type', payload->>'$.region',
    payload->>'$.sells', payload->>'$.ships_from', payload->>'$.returns',
    'paypal_merchant', 'workspace', payload->>'$.connection_provider', payload->>'$.connection_status',
    coalesce(CAST(payload->>'$.passport_published' AS BOOLEAN), FALSE),
    coalesce(CAST(payload->'$.hidden_metrics' AS VARCHAR[]), CAST([] AS VARCHAR[])),
    CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
    payload->>'$.seal_withdrawn_by', CAST(payload->>'$.seal_withdrawn_at' AS TIMESTAMP), payload->>'$.seal_withdrawn_reason'
FROM bronze.merchant_workspaces
WHERE payload->>'$.origin' = 'workspace'
QUALIFY row_number() OVER (PARTITION BY payload->>'$.merchant_id' ORDER BY _row_no DESC) = 1
