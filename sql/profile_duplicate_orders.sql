WITH order_counts AS (
    SELECT
        JSON_VALUE(payload, '$.order_id') AS order_id
        ,COUNT(*) AS event_count
    FROM `glamira-pipeline-506706.raw.events`
    WHERE event_type = 'checkout_success'
    GROUP BY order_id
)

SELECT
    COUNT(*) AS duplicated_order_ids
    ,SUM(event_count) AS events_in_duplicate_groups
    ,SUM(event_count - 1) AS extra_event_rows
    ,MAX(event_count) AS max_events_per_order
FROM order_counts
WHERE event_count > 1