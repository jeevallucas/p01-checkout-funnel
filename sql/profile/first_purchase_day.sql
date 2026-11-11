-- First purchase per user, counted by day, with how many of those users were first seen inside
-- the export window. Users first seen before 2020-11-01 may have bought before the window, so
-- their "first purchase" here may not be their first ever. Also counts later purchase days per
-- user, which bounds how many repeat buyers there can be.
with purchase_day as (
    select
        user_pseudo_id,
        parse_date('%Y%m%d', event_date) as event_day,
        min(user_first_touch_timestamp) as first_touch_timestamp
    from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
    where event_name = 'purchase'
    group by user_pseudo_id, event_day
),

buyer as (
    select
        user_pseudo_id,
        min(event_day) as first_purchase_day,
        count(*) as purchase_days,
        min(first_touch_timestamp) as first_touch_timestamp
    from purchase_day
    group by user_pseudo_id
)

select
    first_purchase_day,
    count(*) as first_time_buyers,
    countif(
        date(timestamp_micros(first_touch_timestamp)) >= date '2020-11-01'
    ) as first_touched_in_window,
    countif(first_touch_timestamp is null) as first_touch_missing,
    countif(purchase_days >= 2) as bought_on_a_later_day
from buyer
group by first_purchase_day
order by first_purchase_day
