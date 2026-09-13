WITH lines AS (

    SELECT
        checkout.event_id
        ,checkout.order_id
        ,checkout.store_id
        ,checkout.checkout_environment
        ,line_number
        ,product

    FROM `glamira-pipeline-506706.dbt_dev_core.int_checkout_deduplicated` AS checkout
    CROSS JOIN UNNEST(
        JSON_QUERY_ARRAY(checkout.cart_products)
    ) AS product
    WITH OFFSET AS line_number

)

SELECT
    COUNT(*) AS total_lines
    ,COUNTIF(JSON_VALUE(product, '$.product_id') IS NULL) AS null_product_id
    ,COUNTIF(JSON_VALUE(product, '$.amount') IS NULL) AS null_amount
    ,COUNTIF(JSON_VALUE(product, '$.price') IS NULL) AS null_price
    ,COUNTIF(JSON_VALUE(product, '$.currency') IS NULL) AS null_currency
    ,MIN(SAFE_CAST(JSON_VALUE(product, '$.amount') AS INT64)) AS min_quantity
    ,MAX(SAFE_CAST(JSON_VALUE(product, '$.amount') AS INT64)) AS max_quantity
    ,COUNTIF(
        SAFE_CAST(JSON_VALUE(product, '$.amount') AS INT64) IS NULL
    ) AS invalid_quantity
FROM lines