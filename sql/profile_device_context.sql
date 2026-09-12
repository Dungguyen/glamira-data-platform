WITH checkout AS (
    SELECT
        NULLIF(JSON_VALUE(payload, '$.user_agent'), '') AS user_agent
        ,NULLIF(JSON_VALUE(payload, '$.resolution'), '') AS resolution
    FROM `glamira-pipeline-506706.raw.events`
    WHERE event_type = 'checkout_success'
)

SELECT
    CASE
        WHEN user_agent IS NULL THEN 'UNKNOWN'
        WHEN REGEXP_CONTAINS(LOWER(user_agent), r'bot|crawler|spider') THEN 'BOT'
        WHEN REGEXP_CONTAINS(LOWER(user_agent), r'ipad|tablet') THEN 'TABLET'
        WHEN REGEXP_CONTAINS(LOWER(user_agent), r'mobile|iphone|android') THEN 'MOBILE'
        ELSE 'DESKTOP'
    END AS device_type
    ,COUNT(*) AS checkout_count
FROM checkout
GROUP BY device_type
ORDER BY checkout_count DESC