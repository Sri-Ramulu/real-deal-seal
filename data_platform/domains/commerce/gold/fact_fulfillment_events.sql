-- writes: gold.fact_fulfillment_events
-- reads: silver.commerce_fulfillment_events, gold.fact_orders
-- key: event_id
-- grain: one row per fulfilment event on an order in the order fact (transaction fact)
SELECT e.event_id, f.merchant_key, f.order_date_key, e.order_id, e.merchant_id, e.event_type, e.days_after_payment,
       f.order_date + coalesce(e.days_after_payment, 0) AS event_date, e.reference, e.evidence_class
FROM silver.commerce_fulfillment_events e
JOIN gold.fact_orders f USING (order_id)
