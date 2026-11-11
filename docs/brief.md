# Brief

A growth lead at an online merchandise store uses this analysis to decide which single checkout fix
to fund next quarter, and whether to keep paying for promotion-driven acquisition.

## User
The user is hypothetical; this context is an assumption used to scope the work. The growth lead of a
mid-sized online store that sells branded merchandise plans the next quarter's experiments with a
small team: one product manager, one front-end engineer, one analyst. They read the memo on a laptop
before the planning meeting and may reopen it on a phone during it.

## Decisions
1. Which checkout step to fix first for mobile shoppers. Engineering capacity covers one checkout
   change per quarter, so the choice has to be ranked, not listed.
2. Whether promotion-driven acquisition (coupons at first purchase, paid first-touch traffic) brings
   buyers who come back. If those buyers do not repeat, the promotion budget buys one-off orders.

## Questions the analysis answers
- At which step of session_start, view_item, add_to_cart, begin_checkout, add_shipping_info,
  add_payment_info, purchase does mobile conversion fall furthest below desktop, and is the gap
  larger than the noise?
- What share of first-time buyers buys again within 30 and 60 days, split by acquisition medium and
  by coupon use at the first purchase?
- How much revenue would closing half of the worst mobile gap add, as a range with its assumptions?

## Constraints
- The data is an obfuscated sample: some fields hold placeholder values (`<Other>`, `NULL`, `''`),
  and Google warns that internal consistency is limited. Every result must say how placeholders were
  treated.
- The data covers 92 days (2020-11-01 to 2021-01-31). A buyer's first purchase in the window may not
  be their first purchase ever, and late cohorts cannot be followed for 60 days.
- Queries run in the BigQuery sandbox: no billing, 1 TB of query processing and 10 GB of storage per
  month, and tables that expire after 60 days.
- The report is a static site on GitHub Pages. It reads committed aggregate files, not BigQuery.

## Success metric
- The memo makes exactly three recommendations, each with a number, the assumption behind it, and a
  way to test it.
- Every number in the memo and the report regenerates from the SQL in this repo with one command.
- The report reads on a 375 px wide phone with no clipped content and no placeholder text.

## Non-goals
Attribution modelling, machine learning, real-time data, and a general KPI dashboard. The analysis
does not try to explain why a step fails; it ranks where to look first.

## Data source and licence
- Google Analytics 4 obfuscated sample e-commerce export, BigQuery dataset
  `bigquery-public-data.ga4_obfuscated_sample_ecommerce`, daily tables `events_20201101` to
  `events_20210131`, from the Google Merchandise Store.
  Documentation: https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset
- Google publishes it in the BigQuery public datasets program for exploration. The documentation
  states no dataset-specific licence. This repo therefore publishes only SQL and aggregated counts
  and rates, never raw rows (see docs/decisions.md, 2026-11-11).
