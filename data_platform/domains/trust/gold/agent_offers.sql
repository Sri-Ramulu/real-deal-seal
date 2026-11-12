-- writes: gold.agent_offers
-- reads: gold.dim_product, gold.merchant_passport
-- key: sku
-- grain: one row per product on offer from a published business, with its standing beside it; never ranked by trust
SELECT
    p.product_key,
    m.merchant_key,
    p.sku,
    p.product_name,
    p.price_usd,
    p.tags,
    p.seller_description,
    p.stock,
    p.in_stock,
    m.merchant_id,
    m.merchant_name,
    m.merchant_kind,
    m.business_type,
    m.ships_from,
    m.returns_policy,
    m.standing,
    m.headline            AS standing_headline,
    m.has_paypal_record,
    m.is_connected AND m.standing <> 'withdrawn' AS paypal_checkout_available,
    m.shows_unverifiable_badge,
    m.seller_text_has_instructions
FROM gold.dim_product p
JOIN gold.merchant_passport m USING (merchant_id)
WHERE m.passport_published
