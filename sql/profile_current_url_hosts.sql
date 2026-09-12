WITH checkout AS (
    SELECT
        NULLIF(JSON_VALUE(payload, '$.current_url'), '') AS current_url
    FROM `glamira-pipeline-506706.raw.events`
    WHERE event_type = 'checkout_success'
)

SELECT
    COALESCE(NET.HOST(current_url), 'UNKNOWN') AS current_host
    ,COUNT(*) AS checkout_count
FROM checkout
GROUP BY current_host
ORDER BY checkout_count DESC
LIMIT 50