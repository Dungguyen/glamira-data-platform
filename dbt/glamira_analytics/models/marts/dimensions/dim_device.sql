{{ config(
    materialized='table'
) }}

WITH device_signatures AS (

    SELECT DISTINCT
        device_type
        ,LOWER(TRIM(resolution)) AS resolution_name

    FROM {{ ref('int_checkout_deduplicated') }}

    WHERE device_type IS NOT NULL
      AND resolution IS NOT NULL
      AND TRIM(resolution) != ''

)

,devices AS (

    SELECT
        FARM_FINGERPRINT(
            CONCAT(
                'device|',
                device_type,
                '|',
                resolution_name
            )
        ) AS device_key

        ,device_type
        ,resolution_name

        ,SAFE_CAST(
            SPLIT(resolution_name, 'x')[SAFE_OFFSET(0)]
            AS INT64
        ) AS screen_width

        ,SAFE_CAST(
            SPLIT(resolution_name, 'x')[SAFE_OFFSET(1)]
            AS INT64
        ) AS screen_height

        ,device_type = 'BOT' AS is_bot
        ,FALSE AS is_unknown

    FROM device_signatures

)

,unknown_device AS (

    SELECT
        CAST(0 AS INT64) AS device_key
        ,'UNKNOWN' AS device_type
        ,'Unknown' AS resolution_name
        ,CAST(NULL AS INT64) AS screen_width
        ,CAST(NULL AS INT64) AS screen_height
        ,FALSE AS is_bot
        ,TRUE AS is_unknown

)

SELECT *
FROM unknown_device

UNION ALL

SELECT *
FROM devices