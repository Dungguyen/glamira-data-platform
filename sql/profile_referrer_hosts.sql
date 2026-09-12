WITH checkout AS (
    SELECT
        NULLIF(JSON_VALUE(payload, '$.referrer_url'), '') AS referrer_url
    FROM `glamira-pipeline-506706.raw.events`
    WHERE event_type = 'checkout_success'
)

SELECT
    COALESCE(NET.HOST(referrer_url), 'UNKNOWN') AS referrer_host
    ,COUNT(*) AS checkout_count
FROM checkout
GROUP BY referrer_host
ORDER BY checkout_count DESC
LIMIT 30