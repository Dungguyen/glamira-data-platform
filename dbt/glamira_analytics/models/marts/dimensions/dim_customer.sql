{{ config(
    materialized='table'
) }}

WITH known_customers AS (

    SELECT DISTINCT
        customer_id

    FROM {{ ref('int_checkout_deduplicated') }}

    WHERE customer_id IS NOT NULL

)

,unknown_customer AS (

    SELECT
        CAST(0 AS INT64) AS customer_key
        ,CAST(NULL AS STRING) AS customer_id_hash
        ,'UNKNOWN' AS customer_type
        ,FALSE AS is_registered

)

,registered_customers AS (

    SELECT
        FARM_FINGERPRINT(
            CONCAT(
                'customer|',
                customer_id
            )
        ) AS customer_key

        ,TO_HEX(
            SHA256(
                CAST(customer_id AS BYTES)
            )
        ) AS customer_id_hash

        ,'REGISTERED' AS customer_type
        ,TRUE AS is_registered

    FROM known_customers

)

SELECT *
FROM unknown_customer

UNION ALL

SELECT *
FROM registered_customers