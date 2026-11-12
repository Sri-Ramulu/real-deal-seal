-- writes: silver.commerce_orders
-- reads: bronze.commerce_paypal_orders, bronze.commerce_ops_orders
-- key: order_id
-- grain: one row per order in the canonical shape, whatever system it came from; latest delivery wins
WITH readback AS (
    SELECT
        payload->>'$.order_id'                                   AS order_id,
        file_meta->>'$.shop'                                     AS merchant_id,
        payload->>'$.invoice_id'                                 AS invoice_id,
        CAST(payload->>'$.date' AS DATE)                         AS order_date,
        CAST(payload->>'$.no' AS INTEGER)                        AS source_seq,
        payload->>'$.status'                                     AS order_status,
        CAST(payload->>'$.amount' AS DECIMAL(12,2))              AS amount_usd,
        payload->>'$.capture_id'                                 AS capture_id,
        payload->>'$.capture_status'                             AS capture_status,
        payload->>'$.payer'                                      AS payer_key,
        CAST(payload->>'$.item_count' AS INTEGER)                AS item_count,
        NOT coalesce(CAST(payload->>'$.live' AS BOOLEAN), FALSE) AS history_is_simulated,
        CAST(substr(file_meta->>'$.taken_at', 1, 19) AS TIMESTAMP) AS snapshot_taken_at,
        'paypal_sandbox_readback'                                AS source_system,
        _source_file AS source_file, _loaded_at, _row_no
    FROM bronze.commerce_paypal_orders
),
ops AS (
    SELECT
        payload->>'$.order_id', payload->>'$.merchant_id', payload->>'$.invoice_id',
        CAST(payload->>'$.order_date' AS DATE), CAST(payload->>'$.seq' AS INTEGER), payload->>'$.status',
        CAST(payload->>'$.amount_usd' AS DECIMAL(12,2)), payload->>'$.capture_id', payload->>'$.capture_status',
        payload->>'$.payer_key', coalesce(CAST(payload->>'$.item_count' AS INTEGER), 1),
        coalesce(CAST(payload->>'$.simulated' AS BOOLEAN), FALSE),
        CAST(substr(payload->>'$.recorded_at', 1, 19) AS TIMESTAMP),
        payload->>'$.source_system', _source_file, _loaded_at, _row_no
    FROM bronze.commerce_ops_orders
)
SELECT * EXCLUDE (_loaded_at, _row_no)
FROM (SELECT * FROM readback UNION ALL SELECT * FROM ops)
QUALIFY row_number() OVER (PARTITION BY order_id ORDER BY _loaded_at DESC, _row_no DESC) = 1
