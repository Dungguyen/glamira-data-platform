{{ config(
    materialized='table'
) }}

WITH products AS (

    SELECT
        FARM_FINGERPRINT(
            CONCAT(
                'product|',
                product_id
            )
        ) AS product_key

        ,product_id
        ,sku
        ,product_name
        ,category_name
        ,product_description
        ,image_url
        ,representative_url
        ,representative_host
        ,source_url_count

        ,FALSE AS is_unknown

    FROM {{ ref('stg_products') }}

)

,unknown_product AS (

    SELECT
        CAST(0 AS INT64) AS product_key

        ,CAST(NULL AS STRING) AS product_id
        ,CAST(NULL AS STRING) AS sku
        ,'Unknown Product' AS product_name
        ,'Unknown' AS category_name
        ,CAST(NULL AS STRING) AS product_description
        ,CAST(NULL AS STRING) AS image_url
        ,CAST(NULL AS STRING) AS representative_url
        ,CAST(NULL AS STRING) AS representative_host
        ,CAST(NULL AS INT64) AS source_url_count

        ,TRUE AS is_unknown

)

SELECT *
FROM unknown_product

UNION ALL

SELECT *
FROM products