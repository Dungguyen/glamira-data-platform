WITH checkout AS (
    SELECT
        JSON_VALUE(payload, '$.store_id') AS store_id
        ,NET.HOST(JSON_VALUE(payload, '$.current_url')) AS current_host
    FROM `glamira-pipeline-506706.raw.events`
    WHERE event_type = 'checkout_success'
)

SELECT
    store_id
    ,COUNT(*) AS checkout_count
    ,COUNT(DISTINCT current_host) AS distinct_hosts
    ,STRING_AGG(
        DISTINCT current_host,
        ', '
        ORDER BY current_host
        LIMIT 10
    ) AS sample_hosts
FROM checkout
GROUP BY store_id
ORDER BY checkout_count DESC