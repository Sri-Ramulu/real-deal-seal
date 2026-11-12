-- writes: gold.fact_monthly_sales
-- reads: gold.fact_orders
-- key: merchant_id, year_month
-- grain: one row per business per calendar month (periodic snapshot fact)
SELECT
    merchant_key,
    merchant_id,
    strftime(order_date, '%Y-%m')  AS year_month,
    count(*)                       AS orders,
    sum(amount_usd)                AS captured_usd,
    sum(refunded_usd)              AS refunded_usd,
    sum(net_usd)                   AS net_usd,
    count(*) FILTER (is_refunded)  AS refunded_orders,
    count(*) FILTER (payment_evidence_class = 'paypal_sandbox_confirmed') AS paypal_confirmed_orders
FROM gold.fact_orders
GROUP BY ALL
