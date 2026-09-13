WITH lines AS (

    SELECT
        JSON_VALUE(product, '$.price') AS price_raw

    FROM `glamira-pipeline-506706.dbt_dev_core.int_checkout_deduplicated` AS checkout
    CROSS JOIN UNNEST(
        JSON_QUERY_ARRAY(checkout.cart_products)
    ) AS product

)

SELECT
    CASE
        WHEN price_raw IS NULL
            THEN 'NULL'

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

        ELSE 'OTHER'
    END AS price_format
    ,COUNT(*) AS line_count

FROM lines
GROUP BY price_format
ORDER BY line_count DESC