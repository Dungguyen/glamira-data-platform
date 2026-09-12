WITH source AS (

    SELECT
        *
    FROM {{ source('raw', 'products') }}

)

SELECT
    CAST(product_id AS STRING) AS product_id
    ,NULLIF(TRIM(sku), '') AS sku
    ,NULLIF(TRIM(product_name), '') AS product_name
    ,NULLIF(TRIM(category), '') AS category_name
    ,NULLIF(TRIM(description), '') AS product_description

    ,NULLIF(TRIM(image_url), '') AS image_url
    ,NULLIF(TRIM(representative_url), '') AS representative_url
    ,NULLIF(TRIM(representative_host), '') AS representative_host

    ,NULLIF(TRIM(crawl_url), '') AS crawl_url
    ,NULLIF(TRIM(crawl_host), '') AS crawl_host

    ,SAFE_CAST(source_url_count AS INT64) AS source_url_count
    ,NULLIF(TRIM(source_url_status), '') AS source_url_status
    ,NULLIF(TRIM(product_master_status), '') AS product_master_status

    ,product_master_status = 'ENRICHED' AS is_enriched

FROM source