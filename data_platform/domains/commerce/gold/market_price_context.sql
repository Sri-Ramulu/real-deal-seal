-- writes: gold.market_price_context
-- reads: silver.commerce_market_offers
-- grain: one row per web offer, labelled as having no PayPal record behind it
SELECT query, title, brand, price_usd, currency, store, url, fetched_at,
       'channel3_cached' AS source, FALSE AS has_paypal_record
FROM silver.commerce_market_offers
