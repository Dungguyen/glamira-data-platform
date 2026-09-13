WITH lines AS (

    SELECT
        JSON_VALUE(product, '$.currency') AS currency_symbol

    FROM `glamira-pipeline-506706.dbt_dev_core.int_checkout_deduplicated` AS checkout
    CROSS JOIN UNNEST(
        JSON_QUERY_ARRAY(checkout.cart_products)
    ) AS product

)

SELECT
    currency_symbol
    ,COUNT(*) AS line_count
FROM lines
GROUP BY currency_symbol
ORDER BY line_count DESC