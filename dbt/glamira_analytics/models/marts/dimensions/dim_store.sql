{{ config(
    materialized='table'
) }}

WITH production_store_hosts AS (

    SELECT
        store_id
        ,ANY_VALUE(current_host) AS store_domain

    FROM {{ ref('int_checkout_deduplicated') }}

    WHERE store_id IS NOT NULL
      AND checkout_environment = 'PRODUCTION'

    GROUP BY store_id

)

,stores AS (

    SELECT
        FARM_FINGERPRINT(
            CONCAT(
                'store|',
                store_id
            )
        ) AS store_key

        ,store_id
        ,store_domain
        ,FALSE AS is_unknown

    FROM production_store_hosts

)

,unknown_store AS (

    SELECT
        CAST(0 AS INT64) AS store_key
        ,CAST(NULL AS STRING) AS store_id
        ,'Unknown Store' AS store_domain
        ,TRUE AS is_unknown

)

SELECT *
FROM unknown_store

UNION ALL

SELECT *
FROM stores