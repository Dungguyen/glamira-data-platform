WITH checkout AS (
    SELECT
        event_id
        ,event_timestamp_raw
        ,JSON_VALUE(payload, '$.order_id') AS order_id
        ,JSON_VALUE(payload, '$.store_id') AS store_id
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
    SELECT *
    FROM ranked
    WHERE event_rank = 1
)

,fact_lines AS (
    SELECT
        d.*
        ,product
    FROM deduplicated AS d
    CROSS JOIN UNNEST(
        JSON_QUERY_ARRAY(d.cart_products)
    ) AS product
)

SELECT
    (SELECT COUNT(*) FROM checkout) AS raw_checkout_events
    ,(SELECT COUNT(*) FROM deduplicated) AS business_checkout_instances
    ,(
        SELECT COUNT(*)
        FROM ranked
        WHERE event_rank > 1
    ) AS removed_tracking_events
    ,COUNT(*) AS fact_candidate_rows
FROM fact_lines