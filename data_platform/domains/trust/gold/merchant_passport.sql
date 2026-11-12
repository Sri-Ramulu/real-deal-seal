-- writes: gold.merchant_passport
-- reads: gold.dim_merchant, gold.fact_metric_observations, gold.fact_rule_results
-- key: merchant_id
-- grain: one row per business: the agent-ready summary every tool and page reads (serving table built on the star)
WITH rules AS (
    SELECT merchant_id,
           count(*)                                              AS rules_total,
           count(*) FILTER (met)                                 AS rules_met,
           bool_and(met) FILTER (rule = 'enough_history')        AS enough_history,
           list(rule ORDER BY rule_order) FILTER (NOT met)       AS failed_rules,
           string_agg(failure_phrase, ', ' ORDER BY rule_order) FILTER (NOT met AND rule <> 'enough_history') AS failure_text,
           any_value(criteria_version)                           AS criteria_version
    FROM gold.fact_rule_results GROUP BY merchant_id
),
obs AS (
    SELECT merchant_id,
           max(value) FILTER (metric = 'orders_completed')        AS orders_completed,
           max(value) FILTER (metric = 'sales_net_usd')           AS net_sales_usd,
           max(value) FILTER (metric = 'history_days')            AS history_days,
           max(value) FILTER (metric = 'tracking_rate')           AS tracking_pct,
           max(value) FILTER (metric = 'fast_ship_rate')          AS fast_ship_pct,
           max(value) FILTER (metric = 'completion_rate')         AS completion_pct,
           max(value) FILTER (metric = 'cancellation_rate')       AS cancellation_pct,
           max(value) FILTER (metric = 'delivery_rate')           AS delivery_pct,
           max(value) FILTER (metric = 'refund_rate')             AS refund_pct,
           max(numerator) FILTER (metric = 'disputes_lost_rate')  AS disputes_lost,
           max(value) FILTER (metric = 'disputes_total')          AS disputes_total,
           max(value) FILTER (metric = 'repeat_buyer_rate')       AS repeat_buyer_pct,
           max(value) FILTER (metric = 'confirmed_payment_share') AS confirmed_payment_pct,
           max(denominator) FILTER (metric = 'refund_rate')       AS recent_orders,
           any_value(as_of)                                       AS as_of,
           any_value(data_as_of)                                  AS data_as_of,
           bool_or(evidence_class = 'simulated')                  AS has_simulated_evidence
    FROM gold.fact_metric_observations GROUP BY merchant_id
),
j AS (
    SELECT d.*, o.* EXCLUDE (merchant_id), r.* EXCLUDE (merchant_id),
        o.merchant_id IS NOT NULL                                                    AS has_record,
        CASE WHEN o.merchant_id IS NULL THEN 'none'
             WHEN o.confirmed_payment_pct = 100 THEN 'paypal_record'
             WHEN o.confirmed_payment_pct > 0 THEN 'mixed' ELSE 'merchant_import' END AS evidence_basis
    FROM gold.dim_merchant d
    LEFT JOIN obs o USING (merchant_id)
    LEFT JOIN rules r USING (merchant_id)
),
s AS (
    SELECT *,
        CASE WHEN seal_withdrawn_by IS NOT NULL THEN 'withdrawn'
             WHEN NOT has_record THEN 'no_record'
             WHEN NOT enough_history THEN 'new'
             WHEN evidence_basis <> 'paypal_record' THEN 'reported'
             WHEN rules_met = rules_total THEN 'sealed'
             ELSE 'verified' END AS standing
    FROM j
)
SELECT
    merchant_key,
    merchant_id,
    merchant_name,
    merchant_kind,
    origin,
    category,
    business_type,
    business_type_label,
    ruleset,
    region,
    sells,
    ships_from,
    returns_policy,
    is_connected,
    passport_published,
    hidden_metrics,
    seal_withdrawn_by,
    seal_withdrawn_at,
    seal_withdrawn_reason,
    has_record,
    evidence_basis,
    evidence_basis = 'paypal_record'                                                    AS has_paypal_record,
    standing,
    CASE standing WHEN 'withdrawn' THEN 'Seal withdrawn'
                  WHEN 'sealed' THEN 'Real Deal: sealed'
                  WHEN 'verified' THEN 'Verified facts, not yet sealed'
                  WHEN 'reported' THEN 'Self-reported record, not yet confirmed'
                  WHEN 'new' THEN 'Not enough history yet'
                  ELSE 'No PayPal record on file' END                                   AS headline,
    CASE standing WHEN 'withdrawn' THEN CASE seal_withdrawn_by
                        WHEN 'issuer' THEN 'Real Deal Seal withdrew this shop''s seal' || coalesce(' on ' || strftime(seal_withdrawn_at, '%Y-%m-%d'), '') || ': ' || seal_withdrawn_reason
                        ELSE 'The business withdrew its passport' || coalesce(' on ' || strftime(seal_withdrawn_at, '%Y-%m-%d'), '') || '. Its record is no longer public, so Real Deal Seal cannot vouch for it.' END
                  WHEN 'sealed' THEN 'Every published rule is met.'
                  WHEN 'verified' THEN 'Buy with care: ' || failure_text || '.'
                  WHEN 'reported' THEN CASE WHEN rules_met = rules_total
                        THEN 'The business''s own records meet every rule, but PayPal records have not confirmed them yet.'
                        ELSE 'From the business''s own records, not yet confirmed: ' || failure_text || '.' END
                  WHEN 'new' THEN 'Clean so far, but the record is too short to judge yet.'
                  ELSE 'Real Deal Seal has no record for this shop, so it can''t vouch for it either way.' END AS verdict,
    CASE WHEN NOT has_record THEN 'none'
         WHEN orders_completed >= 50 THEN 'high'
         WHEN orders_completed >= 30 THEN 'medium' ELSE 'low' END                       AS evidence_strength,
    orders_completed,
    recent_orders,
    net_sales_usd,
    history_days,
    tracking_pct,
    fast_ship_pct,
    completion_pct,
    cancellation_pct,
    delivery_pct,
    refund_pct,
    disputes_lost,
    disputes_total,
    repeat_buyer_pct,
    confirmed_payment_pct,
    coalesce(rules_met, 0)                                                              AS rules_met,
    coalesce(rules_total, 0)                                                            AS rules_total,
    coalesce(failed_rules, [])                                                          AS failed_rules,
    criteria_version,
    as_of,
    data_as_of,
    coalesce(has_simulated_evidence, FALSE)                                             AS has_simulated_evidence,
    shows_unverifiable_badge,
    seller_text_has_instructions
FROM s
