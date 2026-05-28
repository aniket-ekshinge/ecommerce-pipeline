with orders as (
    select * from {{ ref('int_orders_enriched') }}
)

select
    order_date,
    year_month,
    order_year,
    order_month,
    month_name,
    quarter_label,
    is_weekend,
    count(distinct invoice_id)          as orders_count,
    count(distinct customer_id)         as unique_customers,
    count(order_line_id)                as line_items,
    round(sum(revenue)::numeric, 2)     as total_revenue,
    round(avg(revenue)::numeric, 2)     as avg_line_revenue,
    round(
        sum(revenue) /
        nullif(count(distinct invoice_id), 0)
    ::numeric, 2)                       as avg_order_value

from orders
group by
    order_date, year_month, order_year,
    order_month, month_name, quarter_label, is_weekend
order by order_date