with daily as (
    select * from {{ ref('int_revenue_daily') }}
)

select
    order_date,
    year_month,
    order_year,
    order_month,
    month_name,
    quarter_label,
    is_weekend,
    orders_count,
    unique_customers,
    total_revenue,
    avg_order_value,

    sum(total_revenue) over (
        partition by order_year
        order by order_date
        rows between unbounded preceding and current row
    )                                   as ytd_revenue,

    lag(total_revenue, 7) over (
        order by order_date
    )                                   as revenue_7d_ago,

    round(
        (total_revenue - lag(total_revenue, 7) over (order by order_date))
        / nullif(lag(total_revenue, 7) over (order by order_date), 0) * 100
    ::numeric, 1)                       as wow_growth_pct

from daily
order by order_date