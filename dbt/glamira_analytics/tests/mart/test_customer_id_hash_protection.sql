SELECT
    customer_key
    ,customer_id_hash
    ,customer_type
    ,is_registered

FROM {{ ref('dim_customer') }}

WHERE
    (
        customer_key = 0
        AND customer_id_hash IS NOT NULL
    )

    OR

    (
        customer_key != 0
        AND (
            customer_id_hash IS NULL
            OR NOT REGEXP_CONTAINS(
                customer_id_hash,
                r'^[0-9A-Fa-f]{64}$'
            )
        )
    )