with quality_metrics as (

    select
        countif(quantity <= 0) as non_positive_quantity_rows,

        countif(
            unit_price_local is not null
            and line_amount_local is not null
            and abs(
                line_amount_local
                - (unit_price_local * quantity)
            ) > 0.01
        ) as inconsistent_line_amount_rows,

        countif(date_key = 0) as unknown_date_rows,
        countif(store_key = 0) as unknown_store_rows,
        countif(device_key = 0) as unknown_device_rows

    from {{ ref('fact_sales_order_detail') }}

)

select
    'non_positive_quantity' as rule_name,
    non_positive_quantity_rows as violation_count
from quality_metrics
where non_positive_quantity_rows > 0

union all

select
    'inconsistent_line_amount',
    inconsistent_line_amount_rows
from quality_metrics
where inconsistent_line_amount_rows > 0

union all

select
    'unknown_date',
    unknown_date_rows
from quality_metrics
where unknown_date_rows > 0

union all

select
    'unknown_store',
    unknown_store_rows
from quality_metrics
where unknown_store_rows > 0

union all

select
    'unknown_device',
    unknown_device_rows
from quality_metrics
where unknown_device_rows > 0