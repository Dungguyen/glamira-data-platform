{{ config(
    materialized='table'
) }}
WITH source AS (

    SELECT
        event_id
        ,event_type
        ,event_timestamp_raw
        ,source_database
        ,source_collection
        ,ingestion_run_id
        ,source_chunk
        ,payload
    FROM {{ source('raw', 'events') }}
    WHERE event_type = 'checkout_success'

)

,parsed AS (

    SELECT
        event_id
        ,event_timestamp_raw
        ,TIMESTAMP_SECONDS(event_timestamp_raw) AS event_timestamp

        ,JSON_VALUE(payload, '$.order_id') AS order_id
        ,NULLIF(JSON_VALUE(payload, '$.user_id_db'), '') AS customer_id
        ,JSON_VALUE(payload, '$.store_id') AS store_id

        ,NULLIF(JSON_VALUE(payload, '$.email_address'), '') AS email_address
        ,NULLIF(JSON_VALUE(payload, '$.ip'), '') AS ip_address

        ,NULLIF(JSON_VALUE(payload, '$.current_url'), '') AS current_url
        ,NET.HOST(
            NULLIF(JSON_VALUE(payload, '$.current_url'), '')
        ) AS current_host

        ,NULLIF(JSON_VALUE(payload, '$.referrer_url'), '') AS referrer_url
        ,NET.HOST(
            NULLIF(JSON_VALUE(payload, '$.referrer_url'), '')
        ) AS referrer_host

        ,NULLIF(JSON_VALUE(payload, '$.device_id'), '') AS device_id
        ,NULLIF(JSON_VALUE(payload, '$.user_agent'), '') AS user_agent
        ,NULLIF(JSON_VALUE(payload, '$.resolution'), '') AS resolution
        ,JSON_VALUE(payload, '$.local_time') AS local_time_raw
        ,JSON_VALUE(payload, '$.api_version') AS api_version

        ,SAFE_CAST(
            JSON_VALUE(payload, '$.show_recommendation')
            AS BOOL
        ) AS show_recommendation

        ,JSON_QUERY(payload, '$.cart_products') AS cart_products

        ,ARRAY_LENGTH(
            JSON_QUERY_ARRAY(payload, '$.cart_products')
        ) AS cart_product_count

        ,source_database
        ,source_collection
        ,ingestion_run_id
        ,source_chunk

    FROM source

)

SELECT
    *

    ,CASE

        WHEN current_url LIKE 'file://%'
            THEN 'LOCAL'
            
        WHEN current_host LIKE 'stage.%'
            THEN 'STAGE'

        WHEN REGEXP_CONTAINS(
            COALESCE(current_host, ''),
            r'^dev[0-9]*\.'
        )
            THEN 'DEV'

        WHEN current_host = 'glamira.local'
             OR current_host LIKE '%.local'
            THEN 'LOCAL'

        WHEN current_host LIKE 'www.%'
            THEN 'PRODUCTION'

        ELSE 'UNKNOWN'
    END AS checkout_environment

    ,CASE
        WHEN user_agent IS NULL
            THEN 'UNKNOWN'

        WHEN REGEXP_CONTAINS(
            LOWER(user_agent),
            r'bot|crawler|spider'
        )
            THEN 'BOT'

        WHEN REGEXP_CONTAINS(
            LOWER(user_agent),
            r'ipad|tablet'
        )
            THEN 'TABLET'

        WHEN REGEXP_CONTAINS(
            LOWER(user_agent),
            r'mobile|iphone|android'
        )
            THEN 'MOBILE'

        ELSE 'DESKTOP'
    END AS device_type

FROM parsed