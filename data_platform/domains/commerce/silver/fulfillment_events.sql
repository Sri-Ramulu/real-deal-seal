-- writes: silver.commerce_fulfillment_events
-- reads: bronze.commerce_paypal_orders, bronze.commerce_ops_fulfillment_events
-- key: event_id
-- grain: one row per fulfilment event: shipped, tracking_added, service_completed, digital_delivered, booking_kept, cancelled_by_business
WITH snap AS (
    SELECT payload, file_meta->>'$.shop' AS merchant_id, NOT coalesce(CAST(payload->>'$.live' AS BOOLEAN), FALSE) AS sim
    FROM bronze.commerce_paypal_orders
    QUALIFY row_number() OVER (PARTITION BY payload->>'$.order_id' ORDER BY _loaded_at DESC, _row_no DESC) = 1
)
SELECT 'shp:' || (payload->>'$.order_id') AS event_id, payload->>'$.order_id' AS order_id, merchant_id, 'shipped' AS event_type,
       CAST(payload->>'$.ship_days' AS INTEGER) AS days_after_payment, CAST(NULL AS VARCHAR) AS reference,
       CASE WHEN sim THEN 'simulated' ELSE 'merchant_reported' END AS evidence_class
FROM snap WHERE TRY_CAST(payload->>'$.ship_days' AS INTEGER) IS NOT NULL
UNION ALL
SELECT 'trk:' || (payload->>'$.order_id'), payload->>'$.order_id', merchant_id, 'tracking_added',
       TRY_CAST(payload->>'$.ship_days' AS INTEGER), CAST(NULL AS VARCHAR), 'merchant_reported'
FROM snap WHERE CAST(payload->>'$.trackers' AS INTEGER) > 0
UNION ALL
SELECT payload->>'$.event_id', payload->>'$.order_id', payload->>'$.merchant_id', payload->>'$.event_type',
       TRY_CAST(payload->>'$.days_after_payment' AS INTEGER), payload->>'$.reference', payload->>'$.evidence_class'
FROM bronze.commerce_ops_fulfillment_events
QUALIFY row_number() OVER (PARTITION BY payload->>'$.event_id' ORDER BY _row_no DESC) = 1
