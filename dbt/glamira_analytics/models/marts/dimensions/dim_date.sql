{{ config(
    materialized='table'
) }}

WITH date_bounds AS (

    SELECT
        MIN(DATE(event_timestamp)) AS min_date
        ,MAX(DATE(event_timestamp)) AS max_date

    FROM {{ ref('int_checkout_deduplicated') }}

    WHERE checkout_environment = 'PRODUCTION'
      AND event_timestamp IS NOT NULL

)

,calendar AS (

    SELECT
        calendar_date AS full_date

    FROM date_bounds

    CROSS JOIN UNNEST(
        GENERATE_DATE_ARRAY(min_date, max_date)
    ) AS calendar_date

)

,dates AS (

    SELECT
        CAST(FORMAT_DATE('%Y%m%d', full_date) AS INT64) AS date_key
        ,full_date

        ,EXTRACT(DAY FROM full_date) AS day_of_month

        ,MOD(
            EXTRACT(DAYOFWEEK FROM full_date) + 5,
            7
        ) + 1 AS day_of_week

        ,FORMAT_DATE('%A', full_date) AS day_name

        ,EXTRACT(ISOWEEK FROM full_date) AS week_of_year

        ,EXTRACT(MONTH FROM full_date) AS month_number
        ,FORMAT_DATE('%B', full_date) AS month_name
        ,FORMAT_DATE('%Y-%m', full_date) AS year_month

        ,EXTRACT(QUARTER FROM full_date) AS quarter_number
        ,CONCAT(
            'Q',
            CAST(EXTRACT(QUARTER FROM full_date) AS STRING)
        ) AS quarter_name

        ,EXTRACT(YEAR FROM full_date) AS year

        ,EXTRACT(DAYOFWEEK FROM full_date) IN (1, 7) AS is_weekend

        ,FALSE AS is_unknown

    FROM calendar

)

,unknown_date AS (

    SELECT
        CAST(0 AS INT64) AS date_key
        ,CAST(NULL AS DATE) AS full_date
        ,CAST(NULL AS INT64) AS day_of_month
        ,CAST(NULL AS INT64) AS day_of_week
        ,'Unknown' AS day_name
        ,CAST(NULL AS INT64) AS week_of_year
        ,CAST(NULL AS INT64) AS month_number
        ,'Unknown' AS month_name
        ,'Unknown' AS year_month
        ,CAST(NULL AS INT64) AS quarter_number
        ,'Unknown' AS quarter_name
        ,CAST(NULL AS INT64) AS year
        ,FALSE AS is_weekend
        ,TRUE AS is_unknown

)

SELECT *
FROM unknown_date

UNION ALL

SELECT *
FROM dates