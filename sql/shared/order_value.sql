-- Orders and revenue by device, counting each transaction ID once, on the device of its first
-- event. 335 purchase events repeat an ID already seen (docs/data-profile.md); events without a
-- usable ID count as one order each.
-- Runs unchanged in BigQuery and DuckDB; {purchase_event} is filled in by the caller.
with ranked_purchase as (
    select
        transaction_id,
        device_category,
        revenue_usd,
        row_number() over (
            partition by transaction_id order by event_at asc, device_category asc
        ) as event_rank
    from {purchase_event}
    where transaction_id is not null
),

purchase_order as (
    select
        device_category,
        revenue_usd
    from ranked_purchase
    where event_rank = 1
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
