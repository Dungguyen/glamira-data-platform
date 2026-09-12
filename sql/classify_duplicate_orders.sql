WITH checkout AS (
    SELECT
        event_id
        ,event_timestamp_raw
        ,JSON_VALUE(payload, '$.order_id') AS order_id
        ,NULLIF(JSON_VALUE(payload, '$.user_id_db'), '') AS customer_id
        ,JSON_VALUE(payload, '$.store_id') AS store_id
        ,TO_HEX(
            SHA256(
                TO_JSON_STRING(
                    JSON_QUERY(payload, '$.cart_products')
                )
            )
        ) AS cart_hash
    FROM `glamira-pipeline-506706.raw.events`
    WHERE event_type = 'checkout_success'
)

,duplicate_events AS (
    SELECT
        *
        ,COUNT(*) OVER (
            PARTITION BY order_id
        ) AS events_for_order
    FROM checkout
    QUALIFY events_for_order > 1
)

,order_profile AS (
    SELECT
        order_id
        ,COUNT(*) AS event_count
        ,COUNT(DISTINCT cart_hash) AS cart_versions
        ,COUNT(DISTINCT customer_id) AS customer_versions
        ,COUNT(DISTINCT store_id) AS store_versions
    FROM duplicate_events
    GROUP BY order_id
)

SELECT
    CASE
        WHEN cart_versions = 1
             AND customer_versions <= 1
             AND store_versions = 1
            THEN 'SAME_BUSINESS_ORDER'
        ELSE 'BUSINESS_DIFFERENCE_FOUND'
    END AS duplicate_class
    ,COUNT(*) AS order_count
    ,SUM(event_count - 1) AS extra_event_rows
FROM order_profile
GROUP BY duplicate_class
ORDER BY order_count DESC