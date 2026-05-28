with orders as (
    select * from {{ ref('stg_orders') }}
    where is_cancelled = false
),

customer_stats as (
    select
        customer_id,
        max(date_id)                    as last_order_date_id,
        count(distinct invoice_id)      as frequency,
        round(sum(revenue)::numeric, 2) as monetary
    from orders
    group by customer_id
),

rfm_scores as (
    select
        customer_id,
        last_order_date_id,
        frequency,
        monetary,
        ntile(5) over (order by last_order_date_id desc) as recency_score,
        ntile(5) over (order by frequency asc)           as frequency_score,
        ntile(5) over (order by monetary asc)            as monetary_score
    from customer_stats
),

final as (
    select
        customer_id,
        frequency,
        monetary,
        recency_score,
        frequency_score,
        monetary_score,
        (recency_score + frequency_score + monetary_score) as rfm_total,
        case
            when (recency_score + frequency_score + monetary_score) >= 13
                then 'Champions'
            when (recency_score + frequency_score + monetary_score) >= 10
                then 'Loyal customers'
            when recency_score >= 4 and frequency_score <= 2
                then 'New customers'
            when recency_score <= 2 and monetary_score >= 4
                then 'At risk'
            when recency_score <= 2 and monetary_score <= 2
                then 'Lost'
            else 'Potential loyalists'
        end as rfm_segment
    from rfm_scores
)

select * from final