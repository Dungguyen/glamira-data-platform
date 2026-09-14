select
    order_id,
    store_id,
    cart_hash,
    count(*) as row_count
from {{ ref('int_checkout_deduplicated') }}
group by
    order_id,
    store_id,
    cart_hash
having count(*) > 1