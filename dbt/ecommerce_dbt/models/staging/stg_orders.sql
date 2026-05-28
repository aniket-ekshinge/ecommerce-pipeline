with source as (
    select * from {{ source('warehouse', 'fact_orders') }}
),

cleaned as (
    select
        order_line_id,
        invoice_id,
        stock_code,
        customer_id,
        date_id,
        country,
        quantity,
        unit_price,
        revenue,
        is_cancelled,
        loaded_at

    from source
    where quantity > 0
      and unit_price > 0
      and invoice_id is not null
)

select * from cleaned