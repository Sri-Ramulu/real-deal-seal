-- writes: silver.commerce_payment_events
-- reads: bronze.commerce_paypal_orders, bronze.commerce_ops_payment_events
-- key: event_id
-- grain: one row per payment event: capture, refund, dispute_lost or dispute_won
WITH snap AS (
    SELECT payload, file_meta->>'$.shop' AS merchant_id, NOT coalesce(CAST(payload->>'$.live' AS BOOLEAN), FALSE) AS sim
    FROM bronze.commerce_paypal_orders
    QUALIFY row_number() OVER (PARTITION BY payload->>'$.order_id' ORDER BY _loaded_at DESC, _row_no DESC) = 1
)
SELECT 'cap:' || (payload->>'$.order_id') AS event_id, payload->>'$.order_id' AS order_id, merchant_id, 'capture' AS event_type,
       CAST(payload->>'$.amount' AS DECIMAL(12,2)) AS amount_usd, CAST(payload->>'$.date' AS DATE) AS event_date,
       payload->>'$.capture_id' AS provider_ref, CAST(NULL AS VARCHAR) AS reason, 'paypal_sandbox_confirmed' AS evidence_class
FROM snap
UNION ALL
SELECT 'ref:' || (payload->>'$.order_id'), payload->>'$.order_id', merchant_id, 'refund',
       CAST(CAST(payload->>'$.refunded' AS DOUBLE) AS DECIMAL(12,2)), CAST(payload->>'$.date' AS DATE),
       payload->>'$.capture_id', CAST(NULL AS VARCHAR), 'paypal_sandbox_confirmed'
FROM snap WHERE CAST(payload->>'$.refunded' AS DOUBLE) > 0
UNION ALL
SELECT 'dsp:' || (payload->>'$.order_id'), payload->>'$.order_id', merchant_id,
       CASE payload->>'$.dispute.outcome' WHEN 'lost' THEN 'dispute_lost' ELSE 'dispute_won' END,
       CAST(0 AS DECIMAL(12,2)), CAST(payload->>'$.date' AS DATE), CAST(NULL AS VARCHAR), payload->>'$.dispute.reason',
       CASE WHEN sim THEN 'simulated' ELSE 'paypal_sandbox_confirmed' END
FROM snap WHERE payload->>'$.dispute.outcome' IS NOT NULL
UNION ALL
SELECT payload->>'$.event_id', payload->>'$.order_id', payload->>'$.merchant_id', payload->>'$.event_type',
       CAST(payload->>'$.amount_usd' AS DECIMAL(12,2)), CAST(payload->>'$.event_date' AS DATE),
       payload->>'$.provider_ref', payload->>'$.reason', payload->>'$.evidence_class'
FROM bronze.commerce_ops_payment_events
QUALIFY row_number() OVER (PARTITION BY payload->>'$.event_id' ORDER BY _row_no DESC) = 1
