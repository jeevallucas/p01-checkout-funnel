-- The most common values of the grouping fields, with user counts, to decide how to bucket them.
with grouping_field as (
    select
        events.user_pseudo_id,
        field.field_name,
        field.field_value
    from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*` as events,
        unnest([
            struct('device.category' as field_name, events.device.category as field_value),
            struct('traffic_source.medium', events.traffic_source.medium),
            struct('traffic_source.source', events.traffic_source.source),
            struct('traffic_source.name', events.traffic_source.name)
        ]) as field
),

value_count as (
    select
        field_name,
        coalesce(field_value, 'NULL') as shown_value,
        count(*) as events,
        count(distinct user_pseudo_id) as users
    from grouping_field
    group by field_name, shown_value
),

ranked_value as (
    select
        field_name,
        shown_value,
        events,
        users,
        row_number() over (partition by field_name order by events desc) as value_rank
    from value_count
)

select
    field_name,
    shown_value as field_value,
    events,
    users
from ranked_value
where value_rank <= 15
order by field_name asc, events desc
