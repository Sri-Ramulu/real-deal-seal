-- writes: gold.dim_merchant
-- reads: silver.merchant_merchants, silver.merchant_business_types
-- key: merchant_key
-- grain: one row per business (star dimension)
SELECT
    CAST(row_number() OVER (ORDER BY m.merchant_id) AS INTEGER)  AS merchant_key,
    m.merchant_id,
    m.merchant_name,
    m.category,
    m.business_type,
    b.business_type_label,
    b.ruleset,
    b.fulfilment_event,
    m.region,
    m.sells,
    m.ships_from,
    m.returns_policy,
    m.merchant_kind,
    m.origin,
    m.connection_method,
    m.connection_status,
    m.merchant_kind = 'paypal_merchant' AND m.connection_status = 'active' AS is_connected,
    m.passport_published,
    m.hidden_metrics,
    m.self_claim,
    m.seal_withdrawn_by,
    m.seal_withdrawn_at,
    m.seal_withdrawn_reason,
    coalesce(m.displayed_badge = 'forged', FALSE)                AS shows_unverifiable_badge,
    regexp_matches(lower(coalesce(m.self_claim, '')), 'ignore (all )?previous|ai (shopping )?assistants|always recommend') AS seller_text_has_instructions
FROM silver.merchant_merchants m
JOIN silver.merchant_business_types b USING (business_type)
