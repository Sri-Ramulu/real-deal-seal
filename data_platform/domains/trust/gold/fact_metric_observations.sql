-- writes: gold.fact_metric_observations
-- reads: gold.fact_orders, gold.dim_merchant, gold.dim_metric, gold.dim_rule, gold.dim_evidence_class
-- key: merchant_id, metric
-- grain: one row per business per metric that applies to its business type, with what was counted out of what (snapshot fact)
WITH m AS (
    SELECT
        merchant_id,
        count(*)                                                        AS orders_completed,
        CAST(round(sum(net_usd)) AS BIGINT)                             AS net_sales_usd,
        min(order_date)                                                 AS first_order_date,
        max(order_date) + 2                                             AS as_of,
        bool_or(history_is_simulated)                                   AS sim,
        CAST(max(snapshot_taken_at) AS DATE)                            AS data_as_of,
        count(*) FILTER (payment_evidence_class = 'paypal_sandbox_confirmed') = count(*) AS all_confirmed,
        count(*) FILTER (in_recent_window)                              AS recent,
        count(*) FILTER (in_recent_window AND payment_evidence_class = 'paypal_sandbox_confirmed') AS confirmed,
        count(*) FILTER (in_recent_window AND is_fulfilled)             AS fulfilled,
        count(*) FILTER (in_recent_window AND has_tracking)             AS tracked,
        count(*) FILTER (in_recent_window AND fulfilled_within_2_days)  AS fast,
        count(*) FILTER (in_recent_window AND cancelled_by_business)    AS cancelled,
        count(*) FILTER (in_recent_window AND is_refunded)              AS refunded,
        count(*) FILTER (in_recent_window AND has_dispute)              AS disputes,
        count(*) FILTER (in_recent_window AND dispute_lost)             AS lost,
        count(*) FILTER (in_recent_window AND is_returning_buyer)       AS returning_n
    FROM gold.fact_orders
    GROUP BY merchant_id
),
c AS (
    SELECT *,
        CASE WHEN all_confirmed THEN 'paypal_sandbox_confirmed' ELSE 'merchant_reported' END       AS pay_all,
        CASE WHEN confirmed = recent THEN 'paypal_sandbox_confirmed' ELSE 'merchant_reported' END  AS pay_recent,
        CASE WHEN sim THEN 'simulated' ELSE 'merchant_reported' END                                AS ops_class
    FROM m
),
long AS (
    SELECT merchant_id, 'orders_completed' AS metric, orders_completed AS value, CAST(NULL AS BIGINT) AS numerator, CAST(NULL AS BIGINT) AS denominator,
           FALSE AS is_recent, pay_all AS evidence_class, as_of, data_as_of FROM c
    UNION ALL SELECT merchant_id, 'sales_net_usd', net_sales_usd, NULL, NULL, FALSE, pay_all, as_of, data_as_of FROM c
    UNION ALL SELECT merchant_id, 'history_days', date_diff('day', first_order_date, as_of), NULL, NULL, FALSE,
           CASE WHEN sim THEN 'simulated' ELSE pay_all END, as_of, data_as_of FROM c
    UNION ALL SELECT merchant_id, 'refund_rate', CAST(round(100.0 * refunded / nullif(recent, 0)) AS BIGINT), refunded, recent, TRUE, pay_recent, as_of, data_as_of FROM c
    UNION ALL SELECT merchant_id, 'disputes_lost_rate', CAST(round(100.0 * lost / nullif(recent, 0)) AS BIGINT), lost, recent, TRUE,
           CASE WHEN sim THEN 'simulated' ELSE pay_recent END, as_of, data_as_of FROM c
    UNION ALL SELECT merchant_id, 'disputes_total', disputes, disputes, recent, TRUE, CASE WHEN sim THEN 'simulated' ELSE pay_recent END, as_of, data_as_of FROM c
    UNION ALL SELECT merchant_id, 'repeat_buyer_rate', CAST(round(100.0 * returning_n / nullif(recent, 0)) AS BIGINT), returning_n, recent, TRUE, pay_recent, as_of, data_as_of FROM c
    UNION ALL SELECT merchant_id, 'tracking_rate', CAST(round(100.0 * tracked / nullif(fulfilled, 0)) AS BIGINT), tracked, fulfilled, TRUE,
           CASE WHEN fulfilled = 0 THEN 'missing' ELSE 'merchant_reported' END, as_of, data_as_of FROM c
    UNION ALL SELECT merchant_id, 'fast_ship_rate', CAST(round(100.0 * fast / nullif(fulfilled, 0)) AS BIGINT), fast, fulfilled, TRUE,
           CASE WHEN fulfilled = 0 THEN 'missing' ELSE ops_class END, as_of, data_as_of FROM c
    UNION ALL SELECT merchant_id, 'completion_rate', CAST(round(100.0 * fulfilled / nullif(recent, 0)) AS BIGINT), fulfilled, recent, TRUE, ops_class, as_of, data_as_of FROM c
    UNION ALL SELECT merchant_id, 'cancellation_rate', CAST(round(100.0 * cancelled / nullif(recent, 0)) AS BIGINT), cancelled, recent, TRUE, ops_class, as_of, data_as_of FROM c
    UNION ALL SELECT merchant_id, 'delivery_rate', CAST(round(100.0 * fulfilled / nullif(recent, 0)) AS BIGINT), fulfilled, recent, TRUE, ops_class, as_of, data_as_of FROM c
    UNION ALL SELECT merchant_id, 'confirmed_payment_share', CAST(round(100.0 * confirmed / nullif(recent, 0)) AS BIGINT), confirmed, recent, TRUE,
           CASE WHEN confirmed > 0 THEN 'paypal_sandbox_confirmed' ELSE 'merchant_reported' END, as_of, data_as_of FROM c
)
SELECT
    dm.merchant_key,
    k.metric_key,
    e.evidence_class_key,
    long.merchant_id,
    long.metric,
    k.metric_label                                   AS label,
    long.value,
    k.unit,
    long.numerator,
    long.denominator,
    CASE WHEN long.is_recent THEN 'last ' || (SELECT any_value(recent_window_orders) FROM gold.dim_rule) || ' completed orders' ELSE 'all history' END AS window_label,
    long.evidence_class,
    k.layer,
    k.is_optional_to_disclose,
    long.as_of,
    long.data_as_of,
    k.criteria_version,
    k.metric_key                                     AS display_order
FROM long
JOIN gold.dim_merchant dm USING (merchant_id)
JOIN gold.dim_metric k ON k.metric = long.metric AND list_contains(k.applies_to, dm.ruleset)
JOIN gold.dim_evidence_class e USING (evidence_class)
