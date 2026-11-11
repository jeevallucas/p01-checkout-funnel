-- Sessions that pass each checkout step in order, by device category.
-- Runs unchanged in BigQuery and DuckDB; {session_step_event} is filled in by the caller.
-- A session reaches a step when it has that step's event at or after the moment it reached the
-- previous step. Using every event, not only each step's first one, means a shopper who adds to
-- cart from a list page and later views the item still counts once the order is satisfied.
-- Events with equal timestamps count as in order, because GA4 batches events.
with step_session_start as (
    select
        session_key,
        device_category,
        min(event_at) as reached_at
    from {session_step_event}
    where step_name = 'session_start'
    group by session_key, device_category
),

step_view_item as (
    select
        previous_step.session_key,
        previous_step.device_category,
        min(step_event.event_at) as reached_at
    from step_session_start as previous_step
    inner join {session_step_event} as step_event
        on
            previous_step.session_key = step_event.session_key
            and step_event.step_name = 'view_item'
            and previous_step.reached_at <= step_event.event_at
    group by previous_step.session_key, previous_step.device_category
),

step_add_to_cart as (
    select
        previous_step.session_key,
        previous_step.device_category,
        min(step_event.event_at) as reached_at
    from step_view_item as previous_step
    inner join {session_step_event} as step_event
        on
            previous_step.session_key = step_event.session_key
            and step_event.step_name = 'add_to_cart'
            and previous_step.reached_at <= step_event.event_at
    group by previous_step.session_key, previous_step.device_category
),

step_begin_checkout as (
    select
        previous_step.session_key,
        previous_step.device_category,
        min(step_event.event_at) as reached_at
    from step_add_to_cart as previous_step
    inner join {session_step_event} as step_event
        on
            previous_step.session_key = step_event.session_key
            and step_event.step_name = 'begin_checkout'
            and previous_step.reached_at <= step_event.event_at
    group by previous_step.session_key, previous_step.device_category
),

step_add_shipping_info as (
    select
        previous_step.session_key,
        previous_step.device_category,
        min(step_event.event_at) as reached_at
    from step_begin_checkout as previous_step
    inner join {session_step_event} as step_event
        on
            previous_step.session_key = step_event.session_key
            and step_event.step_name = 'add_shipping_info'
            and previous_step.reached_at <= step_event.event_at
    group by previous_step.session_key, previous_step.device_category
),

step_add_payment_info as (
    select
        previous_step.session_key,
        previous_step.device_category,
        min(step_event.event_at) as reached_at
    from step_add_shipping_info as previous_step
    inner join {session_step_event} as step_event
        on
            previous_step.session_key = step_event.session_key
            and step_event.step_name = 'add_payment_info'
            and previous_step.reached_at <= step_event.event_at
    group by previous_step.session_key, previous_step.device_category
),

step_purchase as (
    select
        previous_step.session_key,
        previous_step.device_category,
        min(step_event.event_at) as reached_at
    from step_add_payment_info as previous_step
    inner join {session_step_event} as step_event
        on
            previous_step.session_key = step_event.session_key
            and step_event.step_name = 'purchase'
            and previous_step.reached_at <= step_event.event_at
    group by previous_step.session_key, previous_step.device_category
),

reached_step as (
    select
        device_category,
        1 as step_number,
        'session_start' as step_name
    from step_session_start
    union all
    select
        device_category,
        2 as step_number,
        'view_item' as step_name
    from step_view_item
    union all
    select
        device_category,
        3 as step_number,
        'add_to_cart' as step_name
    from step_add_to_cart
    union all
    select
        device_category,
        4 as step_number,
        'begin_checkout' as step_name
    from step_begin_checkout
    union all
    select
        device_category,
        5 as step_number,
        'add_shipping_info' as step_name
    from step_add_shipping_info
    union all
    select
        device_category,
        6 as step_number,
        'add_payment_info' as step_name
    from step_add_payment_info
    union all
    select
        device_category,
        7 as step_number,
        'purchase' as step_name
    from step_purchase
)

select
    device_category,
    step_number,
    step_name,
    count(*) as sessions
from reached_step
group by device_category, step_number, step_name
order by device_category asc, step_number asc
