-- writes: silver.commerce_catalog_items
-- reads: bronze.commerce_products, bronze.commerce_ops_catalog_items
-- key: sku
-- grain: one row per product or service on offer
SELECT payload->>'$.sku' AS sku, payload->>'$.merchant' AS merchant_id, payload->>'$.name' AS product_name,
       CAST(payload->>'$.price' AS DECIMAL(12,2)) AS price_usd, CAST(payload->'$.tags' AS VARCHAR[]) AS tags,
       payload->>'$.desc' AS seller_description, CAST(payload->>'$.stock' AS INTEGER) AS stock
FROM bronze.commerce_products
UNION ALL
SELECT payload->>'$.sku', payload->>'$.merchant_id', payload->>'$.name', CAST(payload->>'$.price_usd' AS DECIMAL(12,2)),
       coalesce(CAST(payload->'$.tags' AS VARCHAR[]), CAST([] AS VARCHAR[])), payload->>'$.description', CAST(payload->>'$.stock' AS INTEGER)
FROM bronze.commerce_ops_catalog_items
QUALIFY row_number() OVER (PARTITION BY payload->>'$.sku' ORDER BY _row_no DESC) = 1
