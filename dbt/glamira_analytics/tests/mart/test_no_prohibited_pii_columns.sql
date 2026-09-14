{% set mart_relation = ref('fact_sales_order_detail') %}

SELECT
    table_name
    ,column_name

FROM `{{ mart_relation.database }}.{{ mart_relation.schema }}.INFORMATION_SCHEMA.COLUMNS`

WHERE LOWER(column_name) IN (
    'email'
    ,'email_address'
    ,'ip'
    ,'ip_address'
    ,'device_id'
    ,'user_agent'
    ,'customer_id'
    ,'user_id_db'
    ,'current_url'
    ,'referrer_url'
)