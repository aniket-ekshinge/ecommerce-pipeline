-- Pre-populate dim_date for the full date range of our dataset
-- Covers 2009-01-01 through 2012-12-31 (with buffer)

INSERT INTO dim_date (
    date_id, full_date, year, quarter, month,
    month_name, day, day_of_week, week_of_year, is_weekend
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER                   AS date_id,
    d::DATE                                           AS full_date,
    EXTRACT(YEAR  FROM d)::SMALLINT                   AS year,
    EXTRACT(QUARTER FROM d)::SMALLINT                 AS quarter,
    EXTRACT(MONTH FROM d)::SMALLINT                   AS month,
    TO_CHAR(d, 'Month')                               AS month_name,
    EXTRACT(DAY   FROM d)::SMALLINT                   AS day,
    TO_CHAR(d, 'Day')                                 AS day_of_week,
    EXTRACT(WEEK  FROM d)::SMALLINT                   AS week_of_year,
    EXTRACT(DOW   FROM d) IN (0, 6)                   AS is_weekend
FROM
    GENERATE_SERIES(
        '2009-01-01'::DATE,
        '2012-12-31'::DATE,
        '1 day'::INTERVAL
    ) AS d;

SELECT COUNT(*) AS date_rows_inserted FROM dim_date;