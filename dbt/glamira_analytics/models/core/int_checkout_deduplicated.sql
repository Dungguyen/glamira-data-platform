{{ config(
    materialized='table',
    cluster_by=['order_id', 'store_id']
) }}

WITH source AS (

    SELECT
        *
        ,TO_HEX(
            SHA256(
                TO_JSON_STRING(cart_products)
            )
        ) AS cart_hash
    FROM {{ ref('stg_checkout_success') }}

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
                CASE checkout_environment
                    WHEN 'PRODUCTION' THEN 1
                    WHEN 'STAGE' THEN 2
                    WHEN 'DEV' THEN 3
                    WHEN 'LOCAL' THEN 4
                    ELSE 5
                END
                ,event_timestamp_raw
                ,event_id
        ) AS event_rank
    FROM source

)

SELECT
    event_id
    ,event_timestamp_raw
    ,event_timestamp
    ,order_id
    ,customer_id
    ,store_id

    ,email_address
    ,ip_address

    ,current_url
    ,current_host
    ,referrer_url
    ,referrer_host

    ,device_id
    ,user_agent
    ,resolution
    ,device_type

    ,local_time_raw
    ,api_version
    ,show_recommendation

    ,cart_products
    ,cart_product_count
    ,cart_hash

    ,checkout_environment

    ,source_database
    ,source_collection
    ,ingestion_run_id
    ,source_chunk

FROM ranked
WHERE event_rank = 1