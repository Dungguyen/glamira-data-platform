{{ config(materialized='view') }}

select
    -- Fact identity / lineage
    fact.sales_order_detail_key,
    fact.checkout_instance_key,
    fact.source_event_id,
    fact.order_id,
    fact.line_number,

    -- Date
    fact.date_key,
    date.full_date as checkout_date,
    date.day_name,
    date.month_name,
    date.quarter_name,
    date.year_month,
    date.is_weekend,

    -- Customer
    fact.customer_key,
    customer.customer_type,
    customer.is_registered,
    fact.customer_key = 0 as is_unknown_customer,

    -- Product
    fact.product_key,
    fact.product_id,
    product.product_name,
    product.category_name,
    fact.product_key = 0 as is_unknown_product,

    -- Store / currency
    fact.store_key,
    store.store_id,
    store.store_domain,
    fact.currency_symbol,

    -- Geography
    fact.geo_key,
    geo.country_name,
    geo.region_name,
    geo.city_name,
    geo.geo_level,
    fact.geo_key = 0 as is_unknown_geo,

    -- Device
    fact.device_key,
    device.device_type,
    device.resolution_name,
    device.is_bot,

    -- Measures
    fact.quantity,
    fact.unit_price_local,
    fact.line_amount_local,

    -- BI quality flags
    fact.quantity > 10 as is_high_quantity,
    fact.currency_symbol is null as is_missing_currency,

    -- Event time
    fact.event_timestamp

from {{ ref('fact_sales_order_detail') }} as fact

left join {{ ref('dim_date') }} as date
    on fact.date_key = date.date_key

left join {{ ref('dim_customer') }} as customer
    on fact.customer_key = customer.customer_key

left join {{ ref('dim_product') }} as product
    on fact.product_key = product.product_key

left join {{ ref('dim_store') }} as store
    on fact.store_key = store.store_key

left join {{ ref('dim_geo') }} as geo
    on fact.geo_key = geo.geo_key

left join {{ ref('dim_device') }} as device
    on fact.device_key = device.device_key