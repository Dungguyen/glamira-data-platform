select
    checkout_instance_key,
    line_number,
    count(*) as row_count
from {{ ref('int_sales_order_lines') }}
group by
    checkout_instance_key,
    line_number
having count(*) > 1