-- One row: counts from the raw export next to the same counts from the work tables that the
-- BigQuery-only queries build. `uv run pipeline check` fails if a pair differs, which is how
-- the flattening queries (session key, placeholders, coupon) are tested against real data.
-- The last column guards the repeat-purchase rule: a transaction ID that one user logs on two
-- different days would be counted as a repeat.
with raw_purchase as (
    select
        user_pseudo_id,
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
    where event_name = 'purchase'
),

user_id_days as (
    select
        user_key,
        transaction_id
    from {purchase_event}
    where transaction_id is not null
    group by user_key, transaction_id
    having count(distinct purchase_day) > 1
)

select
    (select count(*) from raw_purchase) as raw_purchase_events,
    (select count(*) from {purchase_event}) as table_purchase_events,
    (select count(distinct user_pseudo_id) from raw_purchase) as raw_buyers,
    (select count(*) from {buyer}) as table_buyers,
    (select count(distinct session_key) from raw_purchase) as raw_purchase_sessions,
    (
        select count(distinct session_key)
        from {session_step_event}
        where step_name = 'purchase'
    ) as table_purchase_sessions,
    (select count(*) from user_id_days) as user_transaction_ids_on_two_days
