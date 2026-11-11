-- One row per purchase event with the fields the cohort and sizing queries need.
-- Days are integers (days since 1970-01-01) so the shared SQL needs no engine-specific date
-- functions. A coupon counts only when the `coupon` event parameter holds a real code; item-level
-- coupons are always '(not set)' in this sample (docs/data-profile.md).
select
    user_pseudo_id as user_key,
    event_timestamp as event_at,
    device.category as device_category,
    ecommerce.purchase_revenue_in_usd as revenue_usd,
    unix_date(parse_date('%Y%m%d', event_date)) as purchase_day,
    if(
        ecommerce.transaction_id in ('', '<Other>', '(not set)', '(data deleted)'),
        null,
        ecommerce.transaction_id
    ) as transaction_id,
    coalesce(
        (
            select event_param.value.string_value
            from unnest(event_params) as event_param
            where event_param.key = 'coupon'
        ) not in ('', '<Other>', '(not set)', '(data deleted)'),
        false
    ) as used_coupon
from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
where event_name = 'purchase'
