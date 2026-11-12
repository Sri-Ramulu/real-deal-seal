-- writes: gold.dim_date
-- reads: silver.commerce_orders
-- key: date_key
-- grain: one row per calendar day covered by the order history (star dimension)
SELECT
    CAST(strftime(d, '%Y%m%d') AS INTEGER) AS date_key,
    CAST(d AS DATE)                        AS date_day,
    CAST(date_trunc('week', d) AS DATE)    AS week_start,
    strftime(d, '%Y-%m')                   AS year_month,
    monthname(d)                           AS month_name,
    'Q' || quarter(d) || ' ' || year(d)    AS quarter_label,
    dayname(d)                             AS day_name,
    isodow(d) >= 6                         AS is_weekend
FROM generate_series((SELECT min(order_date) FROM silver.commerce_orders),
                     (SELECT max(order_date) FROM silver.commerce_orders), INTERVAL 1 DAY) AS t(d)
