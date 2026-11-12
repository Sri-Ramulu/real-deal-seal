-- writes: silver.commerce_market_offers
-- reads: bronze.commerce_market_offers
-- grain: one row per web offer returned by Channel3 for a cached query
SELECT
    b.payload->>'$.query'                          AS query,
    CAST(to_timestamp(CAST(b.payload->>'$.at' AS DOUBLE)) AS TIMESTAMP) AS fetched_at,
    o.value->>'$.title'                            AS title,
    o.value->>'$.brand'                            AS brand,
    CAST(o.value->>'$.price' AS DECIMAL(12,2))     AS price_usd,
    o.value->>'$.currency'                         AS currency,
    o.value->>'$.store'                            AS store,
    o.value->>'$.url'                              AS url
FROM bronze.commerce_market_offers b, json_each(b.payload->'$.result.offers') o
WHERE CAST(b.payload->>'$.result.available' AS BOOLEAN)
