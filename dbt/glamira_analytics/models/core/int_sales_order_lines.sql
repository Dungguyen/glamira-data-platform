{{ config(
    materialized='table',
    cluster_by=['order_id', 'product_id']
) }}

WITH unnested AS (

    SELECT
        checkout.*
        ,line_number
        ,product

        ,FARM_FINGERPRINT(
            CONCAT(
                'checkout|'
                ,order_id
                ,'|'
                ,store_id
                ,'|'
                ,cart_hash
            )
        ) AS checkout_instance_key

    FROM {{ ref('int_checkout_deduplicated') }} AS checkout

    CROSS JOIN UNNEST(
        JSON_QUERY_ARRAY(checkout.cart_products)
    ) AS product
    WITH OFFSET AS line_number

)

,parsed AS (

    SELECT
        event_id AS source_event_id
        ,event_timestamp_raw
        ,event_timestamp

        ,checkout_instance_key
        ,order_id
        ,store_id
        ,cart_hash
        ,line_number

        ,JSON_VALUE(product, '$.product_id') AS product_id

        ,JSON_VALUE(product, '$.amount') AS quantity_raw
        ,SAFE_CAST(
            JSON_VALUE(product, '$.amount')
            AS INT64
        ) AS quantity

        ,JSON_VALUE(product, '$.price') AS price_raw

        ,NULLIF(
            TRIM(JSON_VALUE(product, '$.currency')),
            ''
        ) AS currency_symbol

        ,JSON_TYPE(
            JSON_QUERY(product, '$.option')
        ) AS option_type

        ,CASE
            WHEN JSON_TYPE(
                JSON_QUERY(product, '$.option')
            ) = 'array'
                THEN JSON_QUERY(product, '$.option')

            ELSE NULL
        END AS option_json

        ,customer_id
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

        ,checkout_environment

        ,source_database
        ,source_collection
        ,ingestion_run_id
        ,source_chunk

    FROM unnested

)

,price_normalized AS (

    SELECT
        *

        ,CASE
            WHEN NULLIF(TRIM(price_raw), '') IS NULL
                THEN 'MISSING'

            WHEN STRPOS(price_raw, CHR(39)) > 0
                 AND SAFE_CAST(
                     REPLACE(price_raw, CHR(39), '')
                     AS NUMERIC
                 ) IS NOT NULL
                THEN 'APOSTROPHE_THOUSANDS_DECIMAL_DOT'

            WHEN STRPOS(price_raw, '٫') > 0
                THEN 'ARABIC_DECIMAL_SEPARATOR'

            WHEN currency_symbol = '￥'
                 AND REGEXP_CONTAINS(
                     price_raw,
                     r'^[0-9]+,[0-9]{3}$'
                 )
                THEN 'THOUSANDS_COMMA_INTEGER'

            WHEN REGEXP_CONTAINS(
                price_raw,
                r'^[0-9]+$'
            )
                THEN 'INTEGER'

            WHEN REGEXP_CONTAINS(
                price_raw,
                r'^[0-9]+\.[0-9]{1,2}$'
            )
                THEN 'DECIMAL_DOT'

            WHEN REGEXP_CONTAINS(
                price_raw,
                r'^[0-9]+,[0-9]{1,2}$'
            )
                THEN 'DECIMAL_COMMA'

            WHEN REGEXP_CONTAINS(
                price_raw,
                r'^[0-9]{1,3}(,[0-9]{3})+\.[0-9]{1,2}$'
            )
                THEN 'THOUSANDS_COMMA_DECIMAL_DOT'

            WHEN REGEXP_CONTAINS(
                price_raw,
                r'^[0-9]{1,3}(\.[0-9]{3})+,[0-9]{1,2}$'
            )
                THEN 'THOUSANDS_DOT_DECIMAL_COMMA'

            ELSE 'UNSUPPORTED'
        END AS price_format

        ,CASE
            WHEN NULLIF(TRIM(price_raw), '') IS NULL
                THEN NULL

            -- Switzerland:
            -- 1'321.00 -> 1321.00
            WHEN STRPOS(price_raw, CHR(39)) > 0
                 AND SAFE_CAST(
                     REPLACE(price_raw, CHR(39), '')
                     AS NUMERIC
                 ) IS NOT NULL
                THEN REPLACE(price_raw, CHR(39), '')

            -- Kuwait:
            -- 61٫00 -> 61.00
            WHEN STRPOS(price_raw, '٫') > 0
                THEN REPLACE(price_raw, '٫', '.')

            -- Japan:
            -- 85,294 -> 85294
            WHEN currency_symbol = '￥'
                 AND REGEXP_CONTAINS(
                     price_raw,
                     r'^[0-9]+,[0-9]{3}$'
                 )
                THEN REPLACE(price_raw, ',', '')

            -- 331
            WHEN REGEXP_CONTAINS(
                price_raw,
                r'^[0-9]+$'
            )
                THEN price_raw

            -- 331.00
            WHEN REGEXP_CONTAINS(
                price_raw,
                r'^[0-9]+\.[0-9]{1,2}$'
            )
                THEN price_raw

            -- 754,00 -> 754.00
            WHEN REGEXP_CONTAINS(
                price_raw,
                r'^[0-9]+,[0-9]{1,2}$'
            )
                THEN REPLACE(price_raw, ',', '.')

            -- 1,725.00 -> 1725.00
            WHEN REGEXP_CONTAINS(
                price_raw,
                r'^[0-9]{1,3}(,[0-9]{3})+\.[0-9]{1,2}$'
            )
                THEN REPLACE(price_raw, ',', '')

            -- 4.990,00 -> 4990.00
            WHEN REGEXP_CONTAINS(
                price_raw,
                r'^[0-9]{1,3}(\.[0-9]{3})+,[0-9]{1,2}$'
            )
                THEN REPLACE(
                    REPLACE(price_raw, '.', ''),
                    ',',
                    '.'
                )

            ELSE NULL
        END AS normalized_price_string

    FROM parsed

)

,typed AS (

    SELECT
        *

        ,SAFE_CAST(
            normalized_price_string AS NUMERIC
        ) AS unit_price_local

    FROM price_normalized

)

SELECT
    FARM_FINGERPRINT(
        CONCAT(
            CAST(checkout_instance_key AS STRING)
            ,'|'
            ,CAST(line_number AS STRING)
        )
    ) AS sales_order_line_key

    ,checkout_instance_key
    ,order_id
    ,store_id
    ,line_number

    ,product_id

    ,quantity_raw
    ,quantity

    ,price_raw
    ,price_format
    ,unit_price_local

    ,SAFE_CAST(quantity AS NUMERIC)
        * unit_price_local AS line_amount_local

    ,currency_symbol

    ,option_type
    ,option_json

    ,customer_id
    ,email_address
    ,ip_address

    ,event_timestamp_raw
    ,event_timestamp

    ,current_url
    ,current_host
    ,referrer_url
    ,referrer_host

    ,device_id
    ,user_agent
    ,resolution
    ,device_type

    ,checkout_environment

    ,source_event_id
    ,source_database
    ,source_collection
    ,ingestion_run_id
    ,source_chunk

FROM typed