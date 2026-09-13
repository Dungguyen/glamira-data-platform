{{ config(
    materialized='table',
    cluster_by=['date_key', 'product_key', 'store_key']
) }}

WITH production_lines AS (

    SELECT
        lines.*

        ,CASE
            WHEN NULLIF(TRIM(geo.country_name), '') IS NULL
                THEN CAST(0 AS INT64)

            ELSE FARM_FINGERPRINT(
                CONCAT(
                    'geo|country=',
                    NULLIF(TRIM(geo.country_name), ''),
                    '|region=',
                    COALESCE(
                        NULLIF(TRIM(geo.region_name), ''),
                        '__NULL__'
                    ),
                    '|city=',
                    COALESCE(
                        NULLIF(TRIM(geo.city_name), ''),
                        '__NULL__'
                    )
                )
            )
        END AS resolved_geo_key

    FROM {{ ref('int_sales_order_lines') }} AS lines

    LEFT JOIN {{ ref('stg_geoip') }} AS geo
        ON lines.ip_address = geo.ip_address

    WHERE lines.checkout_environment = 'PRODUCTION'

)

SELECT
    lines.sales_order_line_key AS sales_order_detail_key
    ,lines.checkout_instance_key
    ,lines.order_id
    ,lines.line_number

    ,COALESCE(date_dim.date_key, 0) AS date_key
    ,COALESCE(customer.customer_key, 0) AS customer_key
    ,COALESCE(product.product_key, 0) AS product_key
    ,COALESCE(geo_dim.geo_key, 0) AS geo_key
    ,COALESCE(store.store_key, 0) AS store_key
    ,COALESCE(device.device_key, 0) AS device_key

    ,lines.product_id

    ,lines.quantity
    ,lines.unit_price_local
    ,lines.line_amount_local
    ,lines.currency_symbol

    ,lines.event_timestamp
    ,lines.source_event_id

FROM production_lines AS lines

LEFT JOIN {{ ref('dim_date') }} AS date_dim
    ON DATE(lines.event_timestamp) = date_dim.full_date

LEFT JOIN {{ ref('dim_customer') }} AS customer
    ON TO_HEX(
        SHA256(
            CAST(lines.customer_id AS BYTES)
        )
    ) = customer.customer_id_hash

LEFT JOIN {{ ref('dim_product') }} AS product
    ON lines.product_id = product.product_id

LEFT JOIN {{ ref('dim_geo') }} AS geo_dim
    ON lines.resolved_geo_key = geo_dim.geo_key

LEFT JOIN {{ ref('dim_store') }} AS store
    ON lines.store_id = store.store_id

LEFT JOIN {{ ref('dim_device') }} AS device
    ON lines.device_type = device.device_type
   AND LOWER(TRIM(lines.resolution)) = device.resolution_name