-- One row per user who bought at least once: the day GA4 first saw them and their acquisition
-- medium. The medium changes across a user's events in this sample, so it is read from the
-- user's earliest event, the closest the sample has to a first touch (docs/decisions.md).
with buyer_event as (
    select
        all_event.user_pseudo_id as user_key,
        all_event.event_timestamp,
        all_event.user_first_touch_timestamp,
        all_event.traffic_source.medium
    from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*` as all_event
    where
        all_event.user_pseudo_id in (
            select purchase.user_pseudo_id
            from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*` as purchase
            where purchase.event_name = 'purchase'
        )
),

earliest as (
    select
        user_key,
        min(user_first_touch_timestamp) as first_touch_timestamp,
        array_agg(medium order by event_timestamp limit 1)[offset(0)] as earliest_medium
    from buyer_event
    group by user_key
)

select
    user_key,
    unix_date(date(timestamp_micros(first_touch_timestamp))) as first_touch_day,
    case
        when earliest_medium = '(none)' then 'direct'
        when earliest_medium = 'cpc' then 'paid search'
        when earliest_medium in ('organic', 'referral') then earliest_medium
        else 'unknown'
    end as acquisition_medium
from earliest
