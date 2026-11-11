-- Orders and revenue by device, counting each transaction ID once. 335 purchase events repeat an
-- ID already seen (docs/data-profile.md); events without a usable ID count as one order each.
-- Runs unchanged in BigQuery and DuckDB; {purchase_event} is filled in by the caller.
with identified_order as (
    select
        device_category,
        transaction_id,
        max(revenue_usd) as revenue_usd
    from {purchase_event}
    where transaction_id is not null
    group by device_category, transaction_id
),

purchase_order as (
    select
        device_category,
        revenue_usd
    from identified_order
    union all
    select
        device_category,
        revenue_usd
    from {purchase_event}
    where transaction_id is null
)

select
    device_category,
    count(*) as orders,
    sum(revenue_usd) as revenue_usd,
    sum(case when revenue_usd = 0 then 1 else 0 end) as zero_revenue_orders
from purchase_order
group by device_category
order by device_category asc
