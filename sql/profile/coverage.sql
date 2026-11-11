-- One row: which daily tables exist and how much they hold.
-- A session is identified by user_pseudo_id plus the ga_session_id event parameter;
-- events without ga_session_id are counted in placeholder_share.sql, not here.
select
    count(distinct _table_suffix) as daily_tables,
    min(_table_suffix) as first_day,
    max(_table_suffix) as last_day,
    count(*) as events,
    count(distinct user_pseudo_id) as users,
    count(
        distinct concat(
            user_pseudo_id,
            '-',
            cast(
                (
                    select event_param.value.int_value
                    from unnest(event_params) as event_param
                    where event_param.key = 'ga_session_id'
                ) as string
            )
        )
    ) as sessions
from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
