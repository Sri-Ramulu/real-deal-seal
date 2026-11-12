-- writes: gold.fact_orders
-- reads: silver.commerce_orders, silver.commerce_payment_events, silver.commerce_fulfillment_events, gold.dim_merchant, gold.dim_date, gold.dim_source_system
-- key: order_id
-- grain: one row per order with a completed payment (transaction fact)
WITH pay AS (
    SELECT order_id,
           coalesce(sum(amount_usd) FILTER (event_type = 'refund'), 0)             AS refunded_usd,
           coalesce(bool_or(event_type IN ('dispute_lost', 'dispute_won')), FALSE) AS has_dispute,
           coalesce(bool_or(event_type = 'dispute_lost'), FALSE)                   AS dispute_lost,
           max(reason)                                                             AS dispute_reason
    FROM silver.commerce_payment_events GROUP BY order_id
),
ful AS (
    SELECT order_id,
           min(days_after_payment) FILTER (event_type IN ('shipped', 'service_completed', 'digital_delivered', 'booking_kept')) AS fulfil_days,
           coalesce(bool_or(event_type IN ('shipped', 'service_completed', 'digital_delivered', 'booking_kept')), FALSE)       AS is_fulfilled,
           count(*) FILTER (event_type = 'tracking_added')                         AS tracker_count,
           coalesce(bool_or(event_type = 'cancelled_by_business'), FALSE)          AS cancelled_by_business
    FROM silver.commerce_fulfillment_events GROUP BY order_id
),
o AS (
    SELECT s.*,
        row_number() OVER (PARTITION BY merchant_id ORDER BY order_date DESC, source_seq DESC, order_id DESC) AS recency_rank,
        row_number() OVER (PARTITION BY merchant_id ORDER BY order_date, source_seq, order_id)                AS order_no,
        row_number() OVER (PARTITION BY merchant_id, payer_key ORDER BY order_date, source_seq, order_id)     AS buyer_order_seq
    FROM silver.commerce_orders s
    WHERE order_status = 'COMPLETED'
)
SELECT
    o.order_id,
    m.merchant_key,
    d.date_key                                        AS order_date_key,
    ss.source_system_key,
    o.merchant_id,
    CAST(o.order_no AS INTEGER)                       AS order_no,
    o.invoice_id,
    o.order_date,
    o.amount_usd,
    coalesce(pay.refunded_usd, 0)                     AS refunded_usd,
    o.amount_usd - coalesce(pay.refunded_usd, 0)      AS net_usd,
    o.capture_id,
    CASE WHEN coalesce(pay.refunded_usd, 0) >= o.amount_usd THEN 'REFUNDED'
         WHEN coalesce(pay.refunded_usd, 0) > 0 THEN 'PARTIALLY_REFUNDED' ELSE 'COMPLETED' END AS capture_status,
    o.item_count,
    ful.fulfil_days,
    coalesce(ful.tracker_count, 0)                    AS tracker_count,
    coalesce(ful.is_fulfilled, FALSE)                 AS is_fulfilled,
    coalesce(ful.is_fulfilled, FALSE) AND coalesce(ful.tracker_count, 0) > 0 AS has_tracking,
    coalesce(ful.is_fulfilled, FALSE) AND ful.fulfil_days <= 2               AS fulfilled_within_2_days,
    coalesce(ful.cancelled_by_business, FALSE)        AS cancelled_by_business,
    coalesce(pay.refunded_usd, 0) > 0                 AS is_refunded,
    coalesce(pay.has_dispute, FALSE)                  AS has_dispute,
    coalesce(pay.dispute_lost, FALSE)                 AS dispute_lost,
    pay.dispute_reason,
    o.buyer_order_seq > 1                             AS is_returning_buyer,
    CAST(o.recency_rank AS INTEGER)                   AS recency_rank,
    o.recency_rank <= 50                              AS in_recent_window,
    o.history_is_simulated,
    ss.payment_evidence_class,
    o.snapshot_taken_at,
    o.source_system
FROM o
JOIN gold.dim_merchant m USING (merchant_id)
JOIN gold.dim_date d ON d.date_day = o.order_date
JOIN gold.dim_source_system ss USING (source_system)
LEFT JOIN pay USING (order_id)
LEFT JOIN ful USING (order_id)
