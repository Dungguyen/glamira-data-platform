SELECT
    JSON_TYPE(
        JSON_QUERY(product, '$.option')
    ) AS option_type
    ,COUNT(*) AS line_count

FROM `glamira-pipeline-506706.dbt_dev_core.int_checkout_deduplicated` AS checkout
CROSS JOIN UNNEST(
    JSON_QUERY_ARRAY(checkout.cart_products)
) AS product

GROUP BY option_type
ORDER BY line_count DESC