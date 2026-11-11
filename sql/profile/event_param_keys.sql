-- Which event parameters exist, on how many events, and for which event names.
-- Used to check whether coupon or promotion parameters are available.
select
    event_param.key as param_key,
    count(*) as events,
    count(distinct event_name) as event_names,
    string_agg(distinct event_name order by event_name limit 8) as sample_event_names
from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
    unnest(event_params) as event_param
group by param_key
order by events desc, param_key asc
