Fact:
fact_sales_order_detail

Grain:
1 product line / deduplicated successful checkout instance

Dimensions:
Who   → dim_customer
What  → dim_product
Where → dim_geo
When  → dim_date
Market→ dim_store
How   → dim_channel (pending profiling)

Fact baseline:
35,019 candidate rows

Dedup identity:
order_id + store_id + cart_hash

Line identity:
checkout_instance + cart line offset