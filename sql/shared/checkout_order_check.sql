-- One row: how often the sample's event order contradicts the checkout sequence. These counts
-- are why funnel_step_sessions.sql ignores order (docs/decisions.md, 2026-11-11).
-- Runs unchanged in BigQuery and DuckDB; {session_step_event} is filled in by the caller.
with session_step as (
    select
        session_key,
        min(case when step_name = 'view_item' then event_at end) as first_view_item_at,
        min(case when step_name = 'add_to_cart' then event_at end) as first_add_to_cart_at,
        min(case when step_name = 'begin_checkout' then event_at end) as first_begin_checkout_at,
        min(case when step_name = 'add_shipping_info' then event_at end)
            as first_add_shipping_info_at,
        min(case when step_name = 'purchase' then event_at end) as first_purchase_at
    from {session_step_event}
    group by session_key
)

select
    sum(case when first_begin_checkout_at is not null then 1 else 0 end) as checkout_sessions,
    sum(
        case when first_add_shipping_info_at < first_begin_checkout_at then 1 else 0 end
    ) as shipping_before_checkout,
    sum(case when first_purchase_at is not null then 1 else 0 end) as purchase_sessions,
    sum(
        case
            when first_purchase_at is not null and first_add_to_cart_at is null then 1 else 0
        end
    ) as purchases_without_add_to_cart,
    sum(
        case
            when first_purchase_at is not null and first_view_item_at is null then 1 else 0
        end
    ) as purchases_without_view_item
from session_step
