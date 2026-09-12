WITH checkout AS (
    SELECT
        event_id
        ,event_timestamp_raw
        ,JSON_VALUE(payload, '$.order_id') AS order_id
        ,NULLIF(JSON_VALUE(payload, '$.user_id_db'), '') AS customer_id
        ,JSON_VALUE(payload, '$.ip') AS ip
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

SELECT
    order_id
    ,COUNT(*) AS event_count
    ,COUNT(DISTINCT cart_hash) AS distinct_cart_versions
    ,COUNT(DISTINCT customer_id) AS distinct_customer_ids
    ,COUNT(DISTINCT store_id) AS distinct_store_ids
    ,COUNT(DISTINCT ip) AS distinct_ips
    ,MIN(event_timestamp_raw) AS first_timestamp
    ,MAX(event_timestamp_raw) AS last_timestamp
    ,MAX(event_timestamp_raw) - MIN(event_timestamp_raw) AS gap_seconds
FROM duplicate_events
GROUP BY order_id
ORDER BY event_count DESC, order_id