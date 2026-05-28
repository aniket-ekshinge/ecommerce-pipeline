with rfm as (
    select * from {{ ref('int_customer_rfm') }}
),
customers as (
    select * from {{ ref('stg_customers') }}
)

select
    c.customer_id,
    c.country,
    c.is_guest,
    c.first_order_date,
    c.last_order_date,
    c.total_orders,
    c.customer_tenure_days,
    r.frequency,
    r.monetary                          as total_revenue,
    round(r.monetary / nullif(r.frequency, 0)::numeric, 2)
                                        as avg_order_value,
    r.recency_score,
    r.frequency_score,
    r.monetary_score,
    r.rfm_total,
    r.rfm_segment

from customers c
left join rfm r using (customer_id)
where c.is_guest = false
    and r.customer_id is not null