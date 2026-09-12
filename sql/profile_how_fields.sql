WITH checkout AS (
    SELECT
        NULLIF(JSON_VALUE(payload, '$.referrer_url'), '') AS referrer_url
        ,NULLIF(JSON_VALUE(payload, '$.current_url'), '') AS current_url
        ,NULLIF(JSON_VALUE(payload, '$.user_agent'), '') AS user_agent
        ,NULLIF(JSON_VALUE(payload, '$.resolution'), '') AS resolution
        ,NULLIF(JSON_VALUE(payload, '$.device_id'), '') AS device_id
    FROM `glamira-pipeline-506706.raw.events`
    WHERE event_type = 'checkout_success'
)

SELECT
    COUNT(*) AS total_checkout_events
    ,COUNTIF(referrer_url IS NULL) AS null_referrer_url
    ,APPROX_COUNT_DISTINCT(referrer_url) AS distinct_referrer_url
    ,COUNTIF(current_url IS NULL) AS null_current_url
    ,APPROX_COUNT_DISTINCT(current_url) AS distinct_current_url
    ,COUNTIF(user_agent IS NULL) AS null_user_agent
    ,APPROX_COUNT_DISTINCT(user_agent) AS distinct_user_agent
    ,COUNTIF(resolution IS NULL) AS null_resolution
    ,APPROX_COUNT_DISTINCT(resolution) AS distinct_resolution
    ,COUNTIF(device_id IS NULL) AS null_device_id
    ,APPROX_COUNT_DISTINCT(device_id) AS distinct_device_id
FROM checkout