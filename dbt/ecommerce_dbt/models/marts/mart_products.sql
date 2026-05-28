with enriched as (
    select * from {{ ref('int_orders_enriched') }}
)

select
    stock_code,
    product_name,
    price_tier,
    count(distinct invoice_id)          as total_orders,
    sum(quantity)                       as total_units_sold,
    round(sum(revenue)::numeric, 2)     as total_revenue,
    round(avg(unit_price)::numeric, 2)  as avg_selling_price,
    count(distinct customer_id)         as unique_customers,
    round(
        sum(revenue) / nullif(count(distinct invoice_id), 0)
    ::numeric, 2)                       as revenue_per_order

from enriched
group by stock_code, product_name, price_tier
order by total_revenue desc