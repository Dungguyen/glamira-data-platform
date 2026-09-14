select
    checkout_instance_key,
    line_number,
    count(*) as row_count
from {{ ref('fact_sales_order_detail') }}
group by
    checkout_instance_key,
    line_number
having count(*) > 1