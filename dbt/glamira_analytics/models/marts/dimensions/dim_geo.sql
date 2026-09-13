{{ config(
    materialized='table'
) }}

WITH production_geographies AS (

    SELECT DISTINCT
        NULLIF(TRIM(geo.country_name), '') AS country_name
        ,NULLIF(TRIM(geo.region_name), '') AS region_name
        ,NULLIF(TRIM(geo.city_name), '') AS city_name

    FROM {{ ref('int_checkout_deduplicated') }} AS checkout

    LEFT JOIN {{ ref('stg_geoip') }} AS geo
        ON checkout.ip_address = geo.ip_address

    WHERE checkout.checkout_environment = 'PRODUCTION'

)

,known_geographies AS (

    SELECT
        FARM_FINGERPRINT(
            CONCAT(
                'geo|country=',
                country_name,
                '|region=',
                COALESCE(region_name, '__NULL__'),
                '|city=',
                COALESCE(city_name, '__NULL__')
            )
        ) AS geo_key

        ,country_name
        ,region_name
        ,city_name

        ,CASE
            WHEN city_name IS NOT NULL THEN 'CITY'
            WHEN region_name IS NOT NULL THEN 'REGION'
            ELSE 'COUNTRY'
        END AS geo_level

        ,FALSE AS is_unknown

    FROM production_geographies

    WHERE country_name IS NOT NULL

)

,unknown_geography AS (

    SELECT
        CAST(0 AS INT64) AS geo_key
        ,'Unknown' AS country_name
        ,CAST(NULL AS STRING) AS region_name
        ,CAST(NULL AS STRING) AS city_name
        ,'UNKNOWN' AS geo_level
        ,TRUE AS is_unknown

)

SELECT *
FROM unknown_geography

UNION ALL

SELECT *
FROM known_geographies