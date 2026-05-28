with source as (
    select * from {{ source('warehouse', 'dim_date') }}
)

select
    date_id,
    full_date,
    year,
    quarter,
    month,
    trim(month_name)    as month_name,
    day,
    trim(day_of_week)   as day_of_week,
    week_of_year,
    is_weekend,
    case quarter
        when 1 then 'Q1' when 2 then 'Q2'
        when 3 then 'Q3' else 'Q4'
    end                 as quarter_label,
    concat(year, '-', lpad(month::text, 2, '0')) as year_month
from source