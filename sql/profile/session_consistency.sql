-- One row: how internally consistent sessions are, which decides the funnel's session rules.
with session_summary as (
    select
        concat(
            user_pseudo_id,
            '-',
            cast(
                (
                    select event_param.value.int_value
                    from unnest(event_params) as event_param
                    where event_param.key = 'ga_session_id'
                ) as string
            )
        ) as session_key,
        count(distinct device.category) as device_categories,
        countif(event_name = 'session_start') as session_start_events,
        countif(event_name = 'begin_checkout') as begin_checkout_events,
        countif(event_name = 'purchase') as purchase_events
    from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
    group by session_key
    having session_key is not null
)

select
    count(*) as sessions,
    countif(device_categories > 1) as sessions_on_several_devices,
    countif(session_start_events = 0) as sessions_without_session_start,
    countif(session_start_events > 1) as sessions_with_repeated_session_start,
    countif(purchase_events > 0) as sessions_with_purchase,
    countif(purchase_events > 0 and begin_checkout_events = 0) as purchases_without_begin_checkout
from session_summary
