-- Events, users, and purchases per day, to spot gaps and the holiday peak.
select
    parse_date('%Y%m%d', event_date) as event_day,
    count(*) as events,
    count(distinct user_pseudo_id) as users,
    countif(event_name = 'purchase') as purchase_events
from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
group by event_day
order by event_day
