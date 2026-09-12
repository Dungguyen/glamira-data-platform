WITH checkout AS (
    SELECT
        event_id
        ,event_timestamp_raw
        ,JSON_VALUE(payload, '$.order_id') AS order_id
        ,JSON_VALUE(payload, '$.store_id') AS store_id
        ,NET.HOST(JSON_VALUE(payload, '$.current_url')) AS current_host
        ,JSON_QUERY(payload, '$.cart_products') AS cart_products
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

,ranked AS (
    SELECT
        *
        ,ROW_NUMBER() OVER (
            PARTITION BY
                order_id
                ,store_id
                ,cart_hash
            ORDER BY
                event_timestamp_raw
                ,event_id
        ) AS event_rank
    FROM checkout
)

,deduplicated AS (
    SELECT
        *
        ,CASE
            WHEN current_host LIKE 'stage.%'
                THEN 'STAGE'

            WHEN REGEXP_CONTAINS(
                current_host,
                r'^dev[0-9]*\.'
            )
                THEN 'DEV'

            WHEN current_host LIKE '%.local'
                 OR current_host = 'glamira.local'
                THEN 'LOCAL'

            ELSE 'PRODUCTION'
        END AS checkout_environment
    FROM ranked
    WHERE event_rank = 1
)

SELECT
    checkout_environment
    ,COUNT(*) AS checkout_instances
    ,SUM(
        ARRAY_LENGTH(
            JSON_QUERY_ARRAY(cart_products)
        )
    ) AS product_line_count
    ,COUNT(DISTINCT order_id) AS distinct_order_ids
FROM deduplicated
GROUP BY checkout_environment
ORDER BY checkout_instances DESC