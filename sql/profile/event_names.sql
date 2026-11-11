-- Every event name with its volume, by device category, so the funnel uses events that exist.
select
    event_name,
    device.category as device_category,
    count(*) as events,
    count(distinct user_pseudo_id) as users
from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
group by event_name, device_category
order by events desc
