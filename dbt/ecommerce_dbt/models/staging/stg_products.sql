with source as (
    select * from {{ source('warehouse', 'dim_product') }}
)

select
    stock_code,
    description                                        as product_name,
    avg_price,
    times_ordered,
    case
        when avg_price < 1    then 'budget'
        when avg_price < 5    then 'economy'
        when avg_price < 20   then 'standard'
        when avg_price < 100  then 'premium'
        else 'luxury'
    end                                                as price_tier
from source
where stock_code is not null
  and description is not null