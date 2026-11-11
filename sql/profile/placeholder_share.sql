-- How often each field the analysis groups by holds a placeholder instead of a real value.
-- Google documents <Other>, NULL, and '' as placeholders; '(not set)' and '(data deleted)' are
-- also counted because GA4 exports use them for missing attribution.
-- The fields are unpivoted inside one scan so the table is read once.
with grouping_field as (
    select
        field.field_name,
        field.field_value
    from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
        unnest([
            struct('device.category' as field_name, device.category as field_value),
            struct('device.operating_system', device.operating_system),
            struct('geo.country', geo.country),
            struct('traffic_source.medium', traffic_source.medium),
            struct('traffic_source.source', traffic_source.source),
            struct('traffic_source.name', traffic_source.name),
            struct(
                'event_params.ga_session_id',
                cast(
                    (
                        select event_param.value.int_value
                        from unnest(event_params) as event_param
                        where event_param.key = 'ga_session_id'
                    ) as string
                )
            )
        ]) as field
)

select
    field_name,
    case
        when field_value is null then 'NULL'
        when field_value = '' then 'empty string'
        when field_value in ('<Other>', '(not set)', '(data deleted)') then field_value
        else 'real value'
    end as value_class,
    count(*) as events
from grouping_field
group by field_name, value_class
order by field_name asc, events desc
