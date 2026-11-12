-- writes: gold.fact_payment_events
-- reads: silver.commerce_payment_events, gold.fact_orders, gold.dim_date
-- key: event_id
-- grain: one row per payment event on an order in the order fact (transaction fact)
SELECT e.event_id, f.merchant_key, d.date_key AS event_date_key, e.order_id, e.merchant_id, e.event_type, e.amount_usd,
       CASE e.event_type WHEN 'capture' THEN e.amount_usd WHEN 'refund' THEN -e.amount_usd ELSE 0 END AS signed_amount_usd,
       e.event_date, e.provider_ref, e.reason, e.evidence_class
FROM silver.commerce_payment_events e
JOIN gold.fact_orders f USING (order_id)
LEFT JOIN gold.dim_date d ON d.date_day = e.event_date
