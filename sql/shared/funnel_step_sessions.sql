-- Step conversion by device: of the sessions that had the previous step's event, how many also
-- had this step's event. Runs unchanged in BigQuery and DuckDB; {session_step_event} is filled in
-- by the caller.
-- Each step pair is measured on its own and event order is ignored, because the sample's
-- timestamps put add_shipping_info before begin_checkout in most checkout sessions and many
-- purchasing sessions have no add_to_cart (the cart was filled in an earlier visit); see
-- checkout_order_check.sql and docs/decisions.md.
with session_step as (
    select
        session_key,
        device_category,
        max(case when step_name = 'session_start' then 1 else 0 end) as has_session_start,
        max(case when step_name = 'view_item' then 1 else 0 end) as has_view_item,
        max(case when step_name = 'add_to_cart' then 1 else 0 end) as has_add_to_cart,
        max(case when step_name = 'begin_checkout' then 1 else 0 end) as has_begin_checkout,
        max(case when step_name = 'add_shipping_info' then 1 else 0 end) as has_add_shipping_info,
        max(case when step_name = 'add_payment_info' then 1 else 0 end) as has_add_payment_info,
        max(case when step_name = 'purchase' then 1 else 0 end) as has_purchase
    from {session_step_event}
    group by session_key, device_category
),

step_pair as (
    select
        device_category,
        2 as step_number,
        'view_item' as step_name,
        'session_start' as previous_step,
        sum(has_session_start) as sessions_entered,
        sum(has_session_start * has_view_item) as sessions_reached
    from session_step
    group by device_category
    union all
    select
        device_category,
        3 as step_number,
        'add_to_cart' as step_name,
        'view_item' as previous_step,
        sum(has_view_item) as sessions_entered,
        sum(has_view_item * has_add_to_cart) as sessions_reached
    from session_step
    group by device_category
    union all
    select
        device_category,
        4 as step_number,
        'begin_checkout' as step_name,
        'add_to_cart' as previous_step,
        sum(has_add_to_cart) as sessions_entered,
        sum(has_add_to_cart * has_begin_checkout) as sessions_reached
    from session_step
    group by device_category
    union all
    select
        device_category,
        5 as step_number,
        'add_shipping_info' as step_name,
        'begin_checkout' as previous_step,
        sum(has_begin_checkout) as sessions_entered,
        sum(has_begin_checkout * has_add_shipping_info) as sessions_reached
    from session_step
    group by device_category
    union all
    select
        device_category,
        6 as step_number,
        'add_payment_info' as step_name,
        'add_shipping_info' as previous_step,
        sum(has_add_shipping_info) as sessions_entered,
        sum(has_add_shipping_info * has_add_payment_info) as sessions_reached
    from session_step
    group by device_category
    union all
    select
        device_category,
        7 as step_number,
        'purchase' as step_name,
        'add_payment_info' as previous_step,
        sum(has_add_payment_info) as sessions_entered,
        sum(has_add_payment_info * has_purchase) as sessions_reached
    from session_step
    group by device_category
)

select
    device_category,
    step_number,
    step_name,
    previous_step,
    sessions_entered,
    sessions_reached
from step_pair
order by device_category asc, step_number asc
