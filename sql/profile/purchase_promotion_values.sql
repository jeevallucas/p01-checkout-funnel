-- Values of the coupon and promotion fields on purchase events, to decide what "bought with a
-- promotion" can mean in this sample. Event-level parameters and item-level fields are both
-- listed because GA4 can record either.
with purchase_field as (
    select
        promotion_field.field_name,
        promotion_field.field_value
    from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
        unnest([
            struct(
                'event_params.coupon' as field_name,
                (
                    select event_param.value.string_value
                    from unnest(event_params) as event_param
                    where event_param.key = 'coupon'
                ) as field_value
            ),
            struct(
                'event_params.promotion_name',
                (
                    select event_param.value.string_value
                    from unnest(event_params) as event_param
                    where event_param.key = 'promotion_name'
                )
            ),
            struct('items.coupon (first item)', items[safe_offset(0)].coupon),
            struct('items.promotion_name (first item)', items[safe_offset(0)].promotion_name)
        ]) as promotion_field
    where event_name = 'purchase'
)

select
    field_name,
    coalesce(field_value, 'NULL') as field_value,
    count(*) as purchase_events
from purchase_field
group by field_name, field_value
order by field_name asc, purchase_events desc, field_value asc
