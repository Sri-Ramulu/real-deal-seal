-- writes: silver.merchant_business_types
-- reads: bronze.merchant_business_types
-- key: business_type
-- grain: one row per kind of business the platform supports
SELECT payload->>'$.business_type' AS business_type, payload->>'$.ruleset' AS ruleset, payload->>'$.label' AS business_type_label,
       payload->>'$.fulfilment_event' AS fulfilment_event, payload->>'$.examples' AS examples
FROM bronze.merchant_business_types
