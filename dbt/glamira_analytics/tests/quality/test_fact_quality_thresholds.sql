with quality_metrics as (

    select
        count(*) as total_rows,

        countif(currency_symbol is null) as null_currency_rows,

        countif(
            unit_price_local is null
            or line_amount_local is null
        ) as missing_price_rows,

        countif(product_key = 0) as unknown_product_rows,

        countif(geo_key = 0) as unknown_geo_rows,

        countif(quantity > 10) as high_quantity_rows

    from {{ ref('fact_sales_order_detail') }}

),

quality_rates as (

    select
        safe_divide(null_currency_rows, total_rows) as null_currency_rate,
        safe_divide(missing_price_rows, total_rows) as missing_price_rate,
        safe_divide(unknown_product_rows, total_rows) as unknown_product_rate,
        safe_divide(unknown_geo_rows, total_rows) as unknown_geo_rate,
        safe_divide(high_quantity_rows, total_rows) as high_quantity_rate

    from quality_metrics

)

select
    'null_currency_rate' as rule_name,
    null_currency_rate as observed_rate,
    0.05 as maximum_rate
from quality_rates
where null_currency_rate > 0.05

union all

select
    'missing_price_rate',
    missing_price_rate,
    0.0001
from quality_rates
where missing_price_rate > 0.0001

union all

select
    'unknown_product_rate',
    unknown_product_rate,
    0.25
from quality_rates
where unknown_product_rate > 0.25

union all

select
    'unknown_geo_rate',
    unknown_geo_rate,
    0.001
from quality_rates
where unknown_geo_rate > 0.001

union all

select
    'high_quantity_rate',
    high_quantity_rate,
    0.001
from quality_rates
where high_quantity_rate > 0.001