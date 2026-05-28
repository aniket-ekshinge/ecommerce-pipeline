with source as (
    select * from {{ source('warehouse', 'dim_geography') }}
)

select
    country,
    region,
    continent
from source