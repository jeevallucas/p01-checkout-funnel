-- One row: whether a user's acquisition medium is stable across their events.
-- GA4 documents traffic_source as the user's first-touch source, so it should never change for a
-- user; the obfuscated sample may break that, which decides which event the cohort reads it from.
with user_medium as (
    select
        user_pseudo_id,
        count(distinct traffic_source.medium) as mediums,
        count(
            distinct if(
                traffic_source.medium in ('<Other>', '(data deleted)'),
                null,
                traffic_source.medium
            )
        ) as real_mediums,
        countif(event_name = 'purchase') as purchase_events
    from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
    group by user_pseudo_id
)

select
    count(*) as users,
    countif(mediums > 1) as users_with_several_mediums,
    countif(real_mediums > 1) as users_with_several_real_mediums,
    countif(purchase_events > 0) as buyers,
    countif(purchase_events > 0 and mediums > 1) as buyers_with_several_mediums,
    countif(purchase_events > 0 and real_mediums > 1) as buyers_with_several_real_mediums
from user_medium
