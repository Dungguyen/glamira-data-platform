{{ config(
    materialized='table',
    cluster_by=['ip_address']
) }}

WITH source AS (

    SELECT
        *
    FROM {{ source('raw', 'geoip') }}

)

SELECT
    NULLIF(TRIM(ip), '') AS ip_address
    ,SAFE_CAST(ip_version AS INT64) AS ip_version

    ,NULLIF(TRIM(ip_country_code), '') AS country_code
    ,NULLIF(TRIM(ip_country_name), '') AS country_name

    ,NULLIF(TRIM(ip_region_code), '') AS region_code
    ,NULLIF(TRIM(ip_region_name), '') AS region_name

    ,NULLIF(TRIM(ip_city), '') AS city_name

    ,SAFE_CAST(latitude AS FLOAT64) AS latitude
    ,SAFE_CAST(longitude AS FLOAT64) AS longitude
    ,SAFE_CAST(accuracy_radius_km AS INT64) AS accuracy_radius_km

    ,NULLIF(TRIM(geo_status), '') AS geo_status

FROM source