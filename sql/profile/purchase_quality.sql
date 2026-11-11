-- One row: how usable the purchase events are for revenue and repeat-purchase work.
-- A transaction ID or coupon counts as missing when it is NULL or one of the placeholders.
with purchase as (
    select
        user_pseudo_id,
        ecommerce.transaction_id,
        ecommerce.purchase_revenue_in_usd,
        items
    from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
    where event_name = 'purchase'
)

select
    count(*) as purchase_events,
    count(distinct user_pseudo_id) as purchasing_users,
    countif(
        transaction_id is null
        or transaction_id in ('', '<Other>', '(not set)', '(data deleted)')
    ) as purchases_without_transaction_id,
    count(
        distinct if(
            transaction_id in ('', '<Other>', '(not set)', '(data deleted)'), null, transaction_id
        )
    ) as distinct_transaction_ids,
    countif(purchase_revenue_in_usd is null) as purchases_without_revenue,
    countif(purchase_revenue_in_usd = 0) as purchases_with_zero_revenue,
    round(sum(purchase_revenue_in_usd), 2) as revenue_usd,
    countif(array_length(items) = 0) as purchases_without_items,
    countif(
        exists (
            select 1
            from unnest(items) as item
            where
                item.coupon is not null
                and item.coupon not in ('', '<Other>', '(not set)', '(data deleted)')
        )
    ) as purchases_with_item_coupon
from purchase
