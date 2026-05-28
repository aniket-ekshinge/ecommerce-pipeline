with orders as (
    select * from {{ ref('stg_orders') }}
),
customers as (
    select * from {{ ref('stg_customers') }}
),
products as (
    select * from {{ ref('stg_products') }}
),
dates as (
    select * from {{ ref('stg_dates') }}
)

select
    o.order_line_id,
    o.invoice_id,
    o.stock_code,
    o.customer_id,
    o.date_id,
    o.country,
    o.quantity,
    o.unit_price,
    o.revenue,
    o.is_cancelled,

    p.product_name,
    p.price_tier,

    d.full_date            as order_date,
    d.year                 as order_year,
    d.month                as order_month,
    d.month_name,
    d.quarter_label,
    d.year_month,
    d.is_weekend,

    c.is_guest,
    c.customer_tenure_days,
    c.total_orders         as customer_total_orders

from orders o
left join products  p on o.stock_code  = p.stock_code
left join dates     d on o.date_id     = d.date_id
left join customers c on o.customer_id = c.customer_id
where o.is_cancelled = false