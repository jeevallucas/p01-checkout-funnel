-- For each step and device: sessions with that step's event, and how many of them also purchased.
-- Sizing uses it to turn extra sessions at a step into extra purchases without multiplying the
-- per-pair rates, which are each conditional on a different set of sessions.
-- Runs unchanged in BigQuery and DuckDB; {session_step_event} is filled in by the caller.
with session_step as (
    select
        session_key,
        device_category,
        step_name,
        max(
            case when step_name = 'purchase' then 1 else 0 end
        ) over (partition by session_key) as session_purchased
    from {session_step_event}
)

select
    device_category,
    step_name,
    count(distinct session_key) as sessions_with_step,
    count(distinct case when session_purchased = 1 then session_key end) as sessions_purchased
from session_step
group by device_category, step_name
order by device_category asc, step_name asc
