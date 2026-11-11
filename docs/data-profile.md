# Data profile

Measured on 2026-11-11 with `uv run pipeline profile` (queries in `sql/profile/`, results in
`report/sources/results/profile_*.csv`). The eleven queries processed about 7.4 GB in total. All
counts are for the full export, `events_20201101` to `events_20210131`.

## Coverage
- 92 daily tables, 2020-11-01 to 2021-01-31, with no missing day.
- 4,295,584 events, 270,154 users (`user_pseudo_id`), 360,129 sessions (user plus
  `ga_session_id`).
- Daily events range from 21,355 to 92,199. Every day has purchases; the five busiest purchase
  days fall between 2020-11-24 and 2020-12-16 (peak: 160 purchase events on 2020-12-11).

## Devices and sessions
- Events by device category: desktop 58.2%, mobile 39.7%, tablet 2.2%. No placeholder values.
- No session spans two device categories, so a session's device is unambiguous.
- `ga_session_id` is present on every event.
- 5,272 sessions (1.46%) have no `session_start` event, and 105 have more than one.
- 4,848 sessions contain a purchase; only 3 of them have no `begin_checkout`. The checkout events
  are tagged in order, so an ordered funnel loses almost nothing.

## Funnel events (events, users)

| Event | Desktop | Mobile | Tablet |
| --- | --- | --- | --- |
| session_start | 205,978 / 157,079 | 141,111 / 107,981 | 7,881 / 6,175 |
| view_item | 225,037 / 36,323 | 152,676 / 24,810 | 8,355 / 1,443 |
| add_to_cart | 34,047 / 7,384 | 23,223 / 5,142 | 1,273 / 276 |
| begin_checkout | 22,272 / 5,665 | 15,696 / 3,968 | 789 / 219 |
| add_shipping_info | 11,334 / 5,663 | 7,994 / 3,969 | 394 / 219 |
| add_payment_info | 7,888 / 3,352 | 5,724 / 2,387 | 287 / 134 |
| purchase | 3,226 / 2,541 | 2,355 / 1,851 | 111 / 97 |

Tablet has 97 purchasing users, too few for its own comparison; the memo compares mobile with
desktop and reports tablet in the detail tables only.

## Placeholder values
Share of all events whose field holds a placeholder instead of a real value:

| Field | `<Other>` | `(data deleted)` | `(not set)` |
| --- | --- | --- | --- |
| traffic_source.medium | 13.9% | 7.3% | - |
| traffic_source.source | 26.3% | 7.2% | - |
| traffic_source.name | 18.2% | 7.1% | - |
| device.operating_system | 2.6% | - | - |
| geo.country | - | - | 0.7% |

`device.category` and `ga_session_id` have no placeholders. Real medium values are `organic`,
`(none)` (direct), `referral`, and `cpc`.

## Acquisition medium is not stable per user
GA4 documents `traffic_source` as the user's first-touch source, which should never change for a
user. In this sample it does: 41,164 users (15.2%) have more than one medium across their events,
and among buyers it is 3,116 of 4,419 (70.5%); 2,408 buyers (54.5%) have two or more real mediums.
The cause is not documented; Google only warns that obfuscation limits internal consistency. Any
split by medium is therefore a split by the medium recorded on one chosen event, not a true first
touch.

## Purchases
- 5,692 purchase events from 4,419 users. Revenue on purchase events sums to 362,165 USD before
  removing duplicates.
- 906 purchase events (15.9%) have no real `ecommerce.transaction_id`. The 4,786 that have one
  carry 4,451 distinct IDs, so 335 events repeat an ID already seen.
- 450 purchase events (7.9%) have zero revenue; none has missing revenue.
- `items.coupon` is always `(not set)` or NULL, so item-level coupons are unusable.
- The `coupon` event parameter is set on 3,075 purchase events (54.0%), with three obfuscated
  codes. The `promotion_name` parameter is set on 2,270 (39.9%).

## First-time buyers and follow-up
- 4,419 users bought at least once. 3,510 of them (79.4%) were first seen inside the window; 108
  have no first-touch timestamp.
- 329 buyers (7.4%) bought again on a later day within the window.
- Users whose first purchase allows a full 30-day follow-up (first purchase on or before
  2021-01-01): 3,421. For 60 days (on or before 2020-12-02): 1,690. These counts include buyers
  first seen before the window; the cohort rules below narrow them.

## Rules that follow from the profile
- Funnel: ordered, session-based, starting at `session_start`; the 1.46% of sessions without it
  are left out. Device comes from the session, which is always one category.
- Medium: read from the user's earliest event in the window; `<Other>` and `(data deleted)`
  become "unknown" and stay in the totals as their own row.
- Promotion at first purchase: the `coupon` event parameter on the first purchase event.
- First-time buyer: first purchase in the window and first seen on or after 2020-11-01, so that an
  earlier purchase before the export is unlikely.
- Repeat purchase: a purchase event on a later calendar day than the first purchase, within 30 or
  60 days. Same-day second orders and repeated transaction IDs therefore never count as repeats.
