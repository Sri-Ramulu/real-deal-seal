-- writes: gold.dim_product
-- reads: silver.commerce_catalog_items, gold.dim_merchant
-- key: product_key
-- grain: one row per product or service on offer (star dimension)
SELECT CAST(row_number() OVER (ORDER BY c.sku) AS INTEGER) AS product_key, c.sku, m.merchant_key, c.merchant_id, c.product_name,
       c.price_usd, c.tags, c.seller_description, c.stock, c.stock > 0 AS in_stock
FROM silver.commerce_catalog_items c
JOIN gold.dim_merchant m USING (merchant_id)
