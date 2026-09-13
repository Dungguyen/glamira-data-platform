WITH lines AS (

    SELECT
        checkout.order_id
        ,checkout.store_id
        ,checkout.current_host
        ,JSON_VALUE(product, '$.price') AS price_raw
        ,NULLIF(
            TRIM(JSON_VALUE(product, '$.currency')),
            ''
        ) AS currency_symbol

    FROM `glamira-pipeline-506706.dbt_dev_core.int_checkout_deduplicated` AS checkout

    CROSS JOIN UNNEST(
        JSON_QUERY_ARRAY(checkout.cart_products)
    ) AS product

)

,classified AS (

    SELECT
        *
        ,CASE
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
        END AS original_format

    FROM lines

)

SELECT
    CASE
        WHEN TRIM(price_raw) = ''
            THEN 'EMPTY'

        WHEN STRPOS(price_raw, "'") > 0
             AND SAFE_CAST(
                 REPLACE(price_raw, "'", '')
                 AS NUMERIC
             ) IS NOT NULL
            THEN 'APOSTROPHE_THOUSANDS_DECIMAL_DOT'

        WHEN STRPOS(price_raw, '٫') > 0
            THEN 'ARABIC_DECIMAL_SEPARATOR'

        WHEN REGEXP_CONTAINS(
            price_raw,
            r'^[0-9]+,[0-9]{3}$'
        )
            THEN 'COMMA_THREE_DIGITS'

        ELSE 'UNCLASSIFIED'
    END AS edge_format

    ,currency_symbol
    ,store_id
    ,current_host
    ,COUNT(*) AS line_count

FROM classified

WHERE original_format = 'OTHER'

GROUP BY
    edge_format
    ,currency_symbol
    ,store_id
    ,current_host

ORDER BY
    edge_format
    ,line_count DESC