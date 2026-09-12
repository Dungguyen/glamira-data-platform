WITH checkout AS (
    SELECT
        NULLIF(JSON_VALUE(payload, '$.resolution'), '') AS resolution
    FROM `glamira-pipeline-506706.raw.events`
    WHERE event_type = 'checkout_success'
)

SELECT
    COALESCE(resolution, 'UNKNOWN') AS resolution
    ,COUNT(*) AS checkout_count
FROM checkout
GROUP BY resolution
ORDER BY checkout_count DESC
LIMIT 30