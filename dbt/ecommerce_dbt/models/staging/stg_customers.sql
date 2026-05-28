with source as (
    select * from {{ source('warehouse', 'dim_customer') }}
)

select
    customer_id,
    country,
    is_guest,
    first_order_date,
    last_order_date,
    total_orders,
    (last_order_date - first_order_date) as customer_tenure_days
from source