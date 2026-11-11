-- One row per funnel event, keyed by session. This is the only funnel query that needs BigQuery:
-- it unnests event_params to build the session key. Everything downstream is shared SQL.
-- A session is user_pseudo_id plus ga_session_id; events without ga_session_id cannot be placed in
-- a session and are left out (their share is in the data profile). Each session gets the device
-- category of its earliest event, so it is never counted on two devices; placeholder or missing
-- categories become 'unknown' instead of being dropped.
with keyed_event as (
    select
        event_name,
        event_timestamp,
        device.category as device_category,
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
        ) as session_key
    from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
),

session_device as (
    select
        session_key,
        array_agg(device_category order by event_timestamp limit 1)[offset(0)] as device_category
    from keyed_event
    where session_key is not null
    group by session_key
)

select
    keyed_event.session_key,
    keyed_event.event_name as step_name,
    keyed_event.event_timestamp as event_at,
    case
        when session_device.device_category in ('desktop', 'mobile', 'tablet')
            then session_device.device_category
        else 'unknown'
    end as device_category
from keyed_event
inner join session_device
    on keyed_event.session_key = session_device.session_key
where
    keyed_event.event_name in (
        'session_start',
        'view_item',
        'add_to_cart',
        'begin_checkout',
        'add_shipping_info',
        'add_payment_info',
        'purchase'
    )
