-- Share of first-time buyers who buy again within 30 and 60 days, overall, by coupon use at the
-- first purchase, and by acquisition medium. Runs unchanged in BigQuery and DuckDB; the caller
-- fills in {purchase_event}, {buyer}, and the export's first and last day as day numbers.
-- A first-time buyer was first seen inside the export, so an earlier purchase is unlikely. A
-- repeat is a purchase on a later calendar day, so same-day second orders and repeated
-- transaction IDs never count. A buyer enters a window's rate only if the whole window fits
-- before the export ends.
with first_purchase as (
    select
        user_key,
        min(purchase_day) as first_purchase_day
    from {purchase_event}
    group by user_key
),

first_purchase_coupon as (
    select
        first_purchase.user_key,
        max(case when purchase.used_coupon then 1 else 0 end) as coupon_at_first_purchase
    from first_purchase
    inner join {purchase_event} as purchase
        on
            first_purchase.user_key = purchase.user_key
            and first_purchase.first_purchase_day = purchase.purchase_day
    group by first_purchase.user_key
),

first_time_buyer as (
    select
        first_purchase.user_key,
        first_purchase.first_purchase_day,
        buyer.acquisition_medium,
        first_purchase_coupon.coupon_at_first_purchase
    from first_purchase
    inner join {buyer} as buyer
        on first_purchase.user_key = buyer.user_key
    inner join first_purchase_coupon
        on first_purchase.user_key = first_purchase_coupon.user_key
    where buyer.first_touch_day >= {export_first_day}
),

first_repeat as (
    select
        first_time_buyer.user_key,
        min(purchase.purchase_day - first_time_buyer.first_purchase_day) as days_to_repeat
    from first_time_buyer
    inner join {purchase_event} as purchase
        on
            first_time_buyer.user_key = purchase.user_key
            and first_time_buyer.first_purchase_day < purchase.purchase_day
    group by first_time_buyer.user_key
),

follow_up_window as (
    select 30 as window_days
    union all
    select 60 as window_days
),

buyer_in_window as (
    select
        first_time_buyer.acquisition_medium,
        first_time_buyer.coupon_at_first_purchase,
        follow_up_window.window_days,
        case
            when first_repeat.days_to_repeat <= follow_up_window.window_days then 1 else 0
        end as repeated
    from first_time_buyer
    cross join follow_up_window
    left join first_repeat
        on first_time_buyer.user_key = first_repeat.user_key
    where first_time_buyer.first_purchase_day + follow_up_window.window_days <= {export_last_day}
)

select
    'all' as split,
    'all first-time buyers' as segment,
    window_days,
    count(*) as first_time_buyers,
    sum(repeated) as repeat_buyers
from buyer_in_window
group by window_days
union all
select
    'coupon at first purchase' as split,
    case when coupon_at_first_purchase = 1 then 'coupon' else 'no coupon' end as segment,
    window_days,
    count(*) as first_time_buyers,
    sum(repeated) as repeat_buyers
from buyer_in_window
group by window_days, coupon_at_first_purchase
union all
select
    'acquisition medium' as split,
    acquisition_medium as segment,
    window_days,
    count(*) as first_time_buyers,
    sum(repeated) as repeat_buyers
from buyer_in_window
group by window_days, acquisition_medium
order by split asc, segment asc, window_days asc
